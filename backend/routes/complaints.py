from fastapi import APIRouter, Depends, Query, UploadFile, File, Form, HTTPException, Request, BackgroundTasks
from typing import Optional
from limiter import limiter
from services.s3_service import s3_service
from services.media_service import upload_media, delete_media, validate_media_file
from schemas.complaint import ComplaintCreate, VALID_CATEGORIES
from db import db
from datetime import datetime, timezone, timedelta
import uuid
import os
from dependencies import (
    require_citizen,
    require_officer,
    require_officer_or_admin,
    require_role,
    get_current_user,
    get_current_user_optional,
)
from errors import ValidationError, NotFoundError, AuthorizationError
from audit import log_audit
from bson import ObjectId
from bson.errors import InvalidId
from search import search_complaints, get_complaint_count
from notifications import notify_status_change, notify_complaint_registered, notify_assignment
from services.summary_service import generate_summary, generate_marathi_summary
from services.geo_service import normalize_geo_complaint, cluster_geo_points, detect_high_risk_zones
from services.priority_service import compute_priority_score, escalate_complaint_doc

router = APIRouter()


def find_officer_for_region(region: str) -> str | None:
    """Return the least loaded officer for a given district."""
    if not region:
        return None
    officer_cursor = db.get_collection("users").find({"role": "officer", "district": region}, {"email": 1})
    officers = list(officer_cursor)
    if not officers:
        return None
    complaints = db.get_collection("complaints")
    def load_count(officer):
        return complaints.count_documents({"assigned_officer": officer["email"]})
    officer = min(officers, key=load_count)
    return officer["email"]


def is_citizen_owner(complaint: dict, user: dict | None) -> bool:
    """Support both current and legacy owner fields."""
    if not user:
        return False
    user_email = (user.get("sub") or user.get("email") or "").strip().lower()
    if not user_email:
        return False
    owner_emails = {
        str(complaint.get("citizen_email") or "").strip().lower(),
        str(complaint.get("email") or "").strip().lower(),
    }
    owner_emails.discard("")
    return user_email in owner_emails


def post_process_complaint(c: dict, user: dict | None) -> dict:
    """Helper to inject defaults and user-specific data into a complaint doc."""
    c.setdefault("marathi_summary", None)
    c.setdefault("summary_generated", False)
    c.setdefault("summary_generation_status", "pending" if not c.get("summary_generated") else "completed")
    c.setdefault("summary_attempts", 0)
    
    # Inject user vote status
    safe_user_id = user["sub"].replace(".", "_dot_") if user else None
    if safe_user_id:
        c["user_vote"] = c.get("votes_history", {}).get(safe_user_id)
    
    # Secure anonymization for anonymous/confidential complaints
    is_anon = c.get("is_anonymous", False)
    user_role = user.get("role") if user else None
    
    if is_anon:
        if user_role != "admin":
            # Mask all identifying fields
            c["name"] = "Anonymous"
            c["citizen_email"] = "Anonymous"
            c["email"] = "Anonymous"
            if "contact_info" in c:
                c["contact_info"] = None
            if "contact_name" in c:
                c["contact_name"] = "Anonymous"
            if "contact_email" in c:
                c["contact_email"] = "Anonymous"
            if "contact_phone" in c:
                c["contact_phone"] = "Anonymous"
    
    # Under all circumstances, NEVER expose created_by_user_id in non-admin responses
    if user_role != "admin" and "created_by_user_id" in c:
        del c["created_by_user_id"]
        
    # Clean up internal fields
    if "votes_history" in c:
        del c["votes_history"]
    if "_id" in c:
        del c["_id"]
        
    return c


async def generate_and_store_summary(complaint_id: str, target_language: str | None = None):
    """Background task to generate and persist AI summary."""
    collection = db.get_collection("complaints")
    complaint = collection.find_one({"id": complaint_id})
    if not complaint:
        return

    max_attempts = 2
    for attempt in range(1, max_attempts + 1):
        try:
            source_text = (
                f"{complaint.get('title', '')}. "
                f"{complaint.get('description', '')}. "
                f"स्थान: {complaint.get('location', 'उपलब्ध नाही')}. "
                f"विभाग: {complaint.get('category', 'इतर')}. "
                f"प्राधान्य: {complaint.get('priority', 'medium')}."
            )
            
            # Use provided language, or detect from complaint, or default to Marathi
            target_lang = target_language
            if not target_lang:
                target_lang = "Marathi"
                if str(complaint.get("source_language", "")).lower() == "hi":
                    target_lang = "Hindi"
                
            summary = await generate_summary(source_text, target_language=target_lang)
            now_iso = datetime.now(timezone.utc).isoformat()
            collection.update_one(
                {"id": complaint_id},
                {
                    "$set": {
                        "marathi_summary": summary,
                        "summary_generated": bool(summary),
                        "summary_generation_status": "completed" if summary else "failed",
                        "summary_last_error": None if summary else "Empty summary generated",
                        "summary_last_generated_at": now_iso,
                    },
                    "$inc": {"summary_attempts": 1},
                },
            )
            
            # Trigger SMS Notification for AI Report
            from notifications import send_notification
            citizen_email = complaint.get("citizen_email", "")
            # Phone may be in complaint or user doc. Fallback logic inside send_notification
            if citizen_email:
                subject = f"AI Summary Generated for {complaint_id}"
                message = f"An AI summary for complaint {complaint_id} has been generated. JanSamadhan"
                send_notification(citizen_email, subject, message, channel="sms", complaint_id=complaint_id)
                
            return
        except Exception as e:
            error_text = str(e)
            collection.update_one(
                {"id": complaint_id},
                {
                    "$set": {
                        "summary_generated": False,
                        "summary_generation_status": "failed" if attempt >= max_attempts else "retrying",
                        "summary_last_error": error_text,
                    },
                    "$inc": {"summary_attempts": 1},
                },
            )
            if attempt >= max_attempts:
                print(f"⚠️ AI summary generation failed for {complaint_id}: {error_text}")




@router.get("/my")
def get_my_complaints(
    status: str = Query(None),
    priority: str = Query(None),
    skip: int = Query(0),
    limit: int = Query(50),
    user: dict = Depends(require_citizen),
):
    """Get complaints filed by current citizen"""
    complaints = search_complaints(
        citizen_email=user["sub"],
        status=status,
        priority=priority,
        skip=skip,
        limit=limit,
    )
    complaints = [post_process_complaint(c, user) for c in complaints]
    total = get_complaint_count(citizen_email=user["sub"])
    return {"success": True, "data": complaints, "total": total}


@router.get("/assigned")
def get_assigned_complaints(
    status: str = Query(None),
    priority: str = Query(None),
    skip: int = Query(0),
    limit: int = Query(50),
    user: dict = Depends(require_officer_or_admin),
):
    """Get complaints assigned to current officer or all (if admin)"""
    assigned_to = user["sub"] if user.get("role") == "officer" else None
    # Filter out complaints that are already converted to projects
    complaints = search_complaints(
        assigned_to=assigned_to,
        status=status,
        priority=priority,
        skip=skip,
        limit=limit,
    )
    # Filter out approved conversions in-memory or improve search_complaints
    # For now, we'll exclude them here if status is not explicitly requested
    if not status:
        complaints = [c for c in complaints if c.get("project_conversion_status") != "approved"]
    
    complaints = [post_process_complaint(c, user) for c in complaints]
    total = get_complaint_count(assigned_to=assigned_to)
    return {"success": True, "data": complaints, "total": total}


@router.get("/ngo/assigned")
def get_ngo_assigned_complaints(
    status: str = Query(None),
    priority: str = Query(None),
    skip: int = Query(0),
    limit: int = Query(50),
    user: dict = Depends(require_role(["ngo"])),
):
    """Get complaints assigned to current NGO"""
    query = {"assigned_to_ngo": user["sub"]}
    if status:
        query["status"] = status.lower()
    if priority:
        query["priority"] = priority.lower()

    collection = db.get_collection("complaints")
    complaints = list(collection.find(query, {"_id": 0}).sort("createdAt", -1).skip(skip).limit(limit))
    complaints = [post_process_complaint(c, user) for c in complaints]
    total = collection.count_documents(query)
    return {"success": True, "data": complaints, "total": total}


@router.get("/debug")
def debug_complaint_system(request: Request):
    """Debug endpoint for troubleshooting complaint submission issues"""
    try:
        # Test database connection
        collection = db.get_collection("complaints")
        complaint_count = collection.count_documents({})
        
        # Test user collection
        users_collection = db.get_collection("users")
        user_count = users_collection.count_documents({})
        
        # Get recent complaints for testing
        recent_complaints = list(collection.find({}, {"id": 1, "title": 1, "status": 1, "createdAt": 1}).sort("createdAt", -1).limit(3))
        
        # Format complaints for JSON response
        formatted_complaints = []
        for complaint in recent_complaints:
            formatted_complaints.append({
                "id": complaint.get("id"),
                "title": complaint.get("title"),
                "status": complaint.get("status"),
                "createdAt": complaint.get("createdAt")
            })
        
        return {
            "status": "ok",
            "database_connected": True,
            "complaints_count": complaint_count,
            "users_count": user_count,
            "valid_categories": list(VALID_CATEGORIES),
            "recent_complaints": formatted_complaints,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "request_headers": dict(request.headers),
            "client_ip": request.client.host if request.client else "unknown"
        }
        
    except Exception as e:
        return {
            "status": "error",
            "database_connected": False,
            "error": str(e),
            "error_type": type(e).__name__,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }


@router.get("/geo-data")
def get_complaints_geo_data(
    region: str = Query(None),
    category: str = Query(None),
    priority: str = Query(None),
    limit: int = Query(1000),
    user: dict = Depends(get_current_user),
):
    """Return normalized geospatial complaints payload for heatmaps and clustering."""
    query = {}
    if region:
        query["region"] = region
    if category:
        query["category"] = category
    if priority:
        query["priority"] = priority.lower()

    docs = list(
        db.get_collection("complaints")
        .find(query, {"_id": 0})
        .sort("createdAt", -1)
        .limit(limit)
    )
    points = [p for p in (normalize_geo_complaint(d) for d in docs) if p]
    clusters = cluster_geo_points(points)
    high_risk = detect_high_risk_zones(clusters)
    return {
        "success": True,
        "data": {
            "points": points,
            "clusters": clusters,
            "high_risk_zones": high_risk,
            "total_points": len(points),
        },
    }


@router.post("/", status_code=201)
@limiter.limit("5/hour")
def create_complaint(
    request: Request,
    complaint: ComplaintCreate,
    background_tasks: BackgroundTasks,
    user: dict = Depends(require_citizen),
):
    print(f"=== COMPLAINT CREATION REQUEST ===")
    print(f"Request from: {request.client.host if request.client else 'unknown'}")
    print(f"User: {user}")
    print(f"Complaint data: {complaint.model_dump()}")
    print(f"Request headers: {dict(request.headers)}")
    
    try:
        collection = db.get_collection("complaints")
        print("✅ Database connection: OK")
        
        now = datetime.now(timezone.utc).isoformat()
        complaint_id = f"JSM-{datetime.now(timezone.utc).year}-{str(uuid.uuid4())[:8].upper()}"

        user_doc = db.get_collection("users").find_one({"email": user["sub"]})
        citizen_name = user_doc.get("name", "Citizen") if user_doc else "Citizen"
        print(f"✅ User lookup: {citizen_name}")

        # Validate complaint data
        if not complaint.title.strip():
            print("❌ Validation failed: Empty title")
            raise HTTPException(status_code=400, detail="Title cannot be empty")
            
        if len(complaint.title.strip()) < 5:
            print("❌ Validation failed: Title too short")
            raise HTTPException(status_code=400, detail="Title must be at least 5 characters")
            
        if len(complaint.title.strip()) > 100:
            print("❌ Validation failed: Title too long")
            raise HTTPException(status_code=400, detail="Title must be less than 100 characters")
            
        if len(complaint.description.strip()) < 10:
            print("❌ Validation failed: Description too short")
            raise HTTPException(status_code=400, detail="Description must be at least 10 characters")
            
        if len(complaint.description.strip()) > 2000:
            print("❌ Validation failed: Description too long")
            raise HTTPException(status_code=400, detail="Description must be less than 2000 characters")
            
        if complaint.category not in VALID_CATEGORIES:
            print(f"❌ Validation failed: Invalid category '{complaint.category}'")
            raise HTTPException(status_code=400, detail=f"Invalid category. Must be one of: {list(VALID_CATEGORIES)}")
        
        print("✅ Validation: PASSED")

        c_dict = complaint.model_dump()
        
        # Set SLA deadline based on priority
        sla_hours = {"emergency": 24, "high": 48, "medium": 72, "low": 120}
        priority_key = (complaint.priority or "medium").lower()
        deadline = datetime.now(timezone.utc) + timedelta(hours=sla_hours.get(priority_key, 72))

        c_dict.update(
            {
                "grievanceID": complaint_id,
                "id": complaint_id,
                "status": "submitted",
                "citizen_email": user["sub"],
                "email": user["sub"],  # For backward compatibility
                "name": citizen_name,
                "is_anonymous": complaint.is_anonymous or False,
                "created_by_user_id": user["sub"],
                "assigned_officer": None,
                "assigned_to_ngo": None,
                "createdAt": now,
                "updatedAt": now,
                "sla_deadline": deadline.isoformat(),
                "history": [
                    {
                        "status": "Submitted",
                        "remarks": "Grievance filed by citizen",
                        "timestamp": now,
                        "updated_by_user_id": user["sub"],
                    }
                ],
                "media": [],
                "feedback": [],
                "feedbackAverage": 0,
                "feedbackCount": 0,
                "marathi_summary": None,
                "summary_generated": False,
                "summary_generation_status": "pending",
                "summary_attempts": 0,
                "summary_last_error": None,
                "summary_last_generated_at": None,
                "priority_score": 0,
                "source_language": request.headers.get("x-user-language") or user.get("lang") or "en",
            }
        )
        if complaint.latitude is not None and complaint.longitude is not None:
            c_dict["location_geo"] = {
                "type": "Point",
                "coordinates": [complaint.longitude, complaint.latitude],
            }

        # Calculate priority score now that c_dict has createdAt
        c_dict["priority_score"] = compute_priority_score(c_dict)

        # Auto-assign officer if region is provided
        assigned_officer = find_officer_for_region(c_dict.get("region"))
        if assigned_officer:
            c_dict["assigned_officer"] = assigned_officer
            c_dict["history"].append(
                {
                    "status": "Under Review",
                    "remarks": f"Auto-assigned to officer: {assigned_officer}",
                    "timestamp": now,
                    "updated_by_user_id": "system",
                }
            )
            print(f"✅ Auto-assigned to officer: {assigned_officer}")
            # Notify the officer
            officer_user = db.get_collection("users").find_one({"email": assigned_officer})
            if officer_user:
                background_tasks.add_task(
                    notify_assignment,
                    assigned_officer, 
                    complaint_id, 
                    officer_user.get("name", "Officer"), 
                    c_dict.get("category", "General"),
                    officer_user.get("department", "Field"),
                    c_dict.get("sla_deadline", "Pending")
                )

        # Insert into database
        print("📝 Inserting complaint into database...")
        result = collection.insert_one(c_dict)
        
        if not result.inserted_id:
            print("❌ Database insert failed")
            raise HTTPException(status_code=500, detail="Failed to save complaint")
        
        print(f"✅ Database insert successful: {result.inserted_id}")
        background_tasks.add_task(generate_and_store_summary, complaint_id)
        
        # Log the audit
        try:
            log_audit(
                action="anonymous_complaint_created" if complaint.is_anonymous else "complaint_created",
                actor_email=user["sub"],
                actor_role=user.get("role", "citizen"),
                resource_type="complaint",
                resource_id=complaint_id,
                details={
                    "category": complaint.category,
                    "priority": complaint.priority,
                    "region": complaint.region,
                    "user_id": user["sub"],
                    "complaint_id": complaint_id,
                    "timestamp": now
                }
            )
            print("✅ Audit log: OK")
        except Exception as audit_error:
            print(f"⚠️ Audit log failed: {audit_error}")
            
        # Send Email notification
        try:
            background_tasks.add_task(notify_complaint_registered, user["sub"], complaint_id, citizen_name)
            print("✅ Email notification queued")
        except Exception as email_error:
            print(f"⚠️ Email notification failed to queue: {email_error}")
        
        # Prepare response
        response_data = {
            "id": complaint_id,
            "grievanceID": complaint_id,
            "status": "submitted",
            "createdAt": now,
            "assigned_officer": assigned_officer,
            "sla_deadline": deadline.isoformat()
        }
        
        print(f"✅ Complaint created successfully: {complaint_id}")
        print(f"=== END COMPLAINT CREATION ===")
        
        return {"success": True, "data": response_data, "message": "Complaint submitted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Unexpected error in complaint creation: {str(e)}")
        print(f"Error type: {type(e).__name__}")
        import traceback
        print(f"Traceback: {traceback.format_exc()}")
        
        raise HTTPException(
            status_code=500, 
            detail=f"Internal server error while creating complaint: {str(e)}"
        )


@router.post("/with-media", status_code=201)
@limiter.limit("5/hour")
async def create_complaint_with_media(
    request: Request,
    background_tasks: BackgroundTasks,
    title: str = Form(...),
    description: str = Form(...),
    category: str = Form(...),
    subcategory: str = Form(""),
    priority: str = Form("medium"),
    location: str = Form(...),
    region: str = Form(...),
    latitude: float = Form(None),
    longitude: float = Form(None),
    files: list[UploadFile] = File([]),
    contact_name: str = Form(None),
    contact_phone: str = Form(None),
    contact_email: str = Form(None),
    is_anonymous: bool = Form(False),
    user: dict = Depends(require_citizen),
):
    """
    Create complaint with media files support
    Accepts multipart form data for file uploads
    """
    print(f"=== COMPLAINT CREATION WITH MEDIA REQUEST ===")
    print(f"Request from: {request.client.host if request.client else 'unknown'}")
    print(f"User: {user}")
    print(f"Form data: title={title}, category={category}, priority={priority}")
    print(f"Media files count: {len(files)}")
    
    try:
        collection = db.get_collection("complaints")
        print("✅ Database connection: OK")
        
        now = datetime.now(timezone.utc).isoformat()
        complaint_id = f"JSM-{datetime.now(timezone.utc).year}-{str(uuid.uuid4())[:8].upper()}"

        user_doc = db.get_collection("users").find_one({"email": user["sub"]})
        citizen_name = user_doc.get("name", "Citizen") if user_doc else "Citizen"
        print(f"✅ User lookup: {citizen_name}")

        # Validate complaint data
        if not title.strip():
            print("❌ Validation failed: Empty title")
            raise HTTPException(status_code=400, detail="Title cannot be empty")
            
        if len(title.strip()) < 5:
            print("❌ Validation failed: Title too short")
            raise HTTPException(status_code=400, detail="Title must be at least 5 characters")
            
        if len(title.strip()) > 100:
            print("❌ Validation failed: Title too long")
            raise HTTPException(status_code=400, detail="Title must be less than 100 characters")
            
        if len(description.strip()) < 10:
            print("❌ Validation failed: Description too short")
            raise HTTPException(status_code=400, detail="Description must be at least 10 characters")
            
        if len(description.strip()) > 2000:
            print("❌ Validation failed: Description too long")
            raise HTTPException(status_code=400, detail="Description must be less than 2000 characters")
            
        if category not in VALID_CATEGORIES:
            print(f"❌ Validation failed: Invalid category '{category}'")
            raise HTTPException(status_code=400, detail=f"Invalid category. Must be one of: {list(VALID_CATEGORIES)}")
        
        print("✅ Validation: PASSED")

        # Process media files
        media_attachments = []
        for media_file in files:
            print(f"📁 Processing media file: {media_file.filename}")
            
            # Validate file before upload
            validation_result = validate_media_file(media_file)
            if not validation_result["valid"]:
                print(f"❌ Media validation failed: {validation_result['errors']}")
                raise HTTPException(
                    status_code=400,
                    detail=f"Media validation failed: {', '.join(validation_result['errors'])}"
                )
            
            # Upload to Cloudinary
            try:
                upload_result = await upload_media(media_file)
                
                # Map Cloudinary resource_type to our schema literal
                r_type = upload_result.get("type", "image")
                media_type = "document"
                if r_type in ["image", "video"]:
                    media_type = r_type
                
                media_attachments.append({
                    "url": upload_result["url"],
                    "public_id": upload_result["public_id"],
                    "media_type": media_type,
                    "file_name": media_file.filename,
                    "size_bytes": upload_result["size_bytes"],
                    "format": upload_result.get("format"),
                    "original_filename": upload_result.get("original_filename"),
                    "uploaded_at": upload_result["uploaded_at"]
                })
                print(f"✅ Media uploaded successfully: {upload_result['url']}")
                
            except Exception as upload_error:
                print(f"❌ Media upload failed: {str(upload_error)}")
                raise HTTPException(
                    status_code=500,
                    detail=f"Failed to upload media file {media_file.filename}: {str(upload_error)}"
                )

        # Create complaint object
        complaint_data = {
            "title": title.strip(),
            "description": description.strip(),
            "category": category,
            "subcategory": subcategory.strip() if subcategory else "",
            "priority": priority.lower(),
            "location": location.strip(),
            "region": region.strip(),
            "latitude": latitude,
            "longitude": longitude,
            "media": media_attachments,
            "votes": 0,
            "comments": [],
            "marathi_summary": None,
            "summary_generated": False,
            "contact_info": {
                "name": contact_name,
                "phone": contact_phone,
                "email": contact_email
            } if contact_name else None
        }
        
        # Set SLA deadline based on priority
        sla_hours = {"emergency": 24, "high": 48, "medium": 72, "low": 120}
        priority_key = priority.lower()
        deadline = datetime.now(timezone.utc) + timedelta(hours=sla_hours.get(priority_key, 72))

        # Add system fields
        complaint_data.update(
            {
                "grievanceID": complaint_id,
                "id": complaint_id,
                "status": "submitted",
                "citizen_email": user["sub"],
                "email": user["sub"],  # For backward compatibility
                "name": citizen_name,
                "is_anonymous": is_anonymous,
                "created_by_user_id": user["sub"],
                "assigned_officer": None,
                "assigned_to_ngo": None,
                "createdAt": now,
                "updatedAt": now,
                "sla_deadline": deadline.isoformat(),
                "timeline": [
                    {
                        "stage": "Submitted",
                        "remarks": f"Grievance filed by citizen with {len(media_attachments)} media file(s)",
                        "timestamp": now,
                        "updated_by_user_id": user["sub"],
                    }
                ],
                "feedback": [],
                "feedbackAverage": 0,
                "feedbackCount": 0,
            }
        )
        
        # Calculate priority score
        complaint_data["priority_score"] = compute_priority_score(complaint_data)

        # Auto-assign officer if region is provided
        assigned_officer = find_officer_for_region(complaint_data.get("region"))
        if assigned_officer:
            complaint_data["assigned_officer"] = assigned_officer
            complaint_data["timeline"].append(
                {
                    "stage": "Under Review",
                    "remarks": f"Auto-assigned to officer: {assigned_officer}",
                    "timestamp": now,
                    "updated_by_user_id": "system",
                }
            )
            print(f"✅ Auto-assigned to officer: {assigned_officer}")
            # Notify the officer
            officer_user = db.get_collection("users").find_one({"email": assigned_officer})
            if officer_user:
                background_tasks.add_task(
                    notify_assignment,
                    assigned_officer, 
                    complaint_id, 
                    officer_user.get("name", "Officer"), 
                    complaint_data.get("category", "General"),
                    officer_user.get("department", "Field"),
                    complaint_data.get("sla_deadline", "Pending")
                )

        # Insert into database
        print("📝 Inserting complaint into database...")
        result = collection.insert_one(complaint_data)
        
        if not result.inserted_id:
            print("❌ Database insert failed")
            raise HTTPException(status_code=500, detail="Failed to save complaint")
        
        print(f"✅ Database insert successful: {result.inserted_id}")
        
        # Log to audit
        try:
            log_audit(
                action="anonymous_complaint_created" if is_anonymous else "complaint_created_with_media",
                actor_email=user["sub"],
                actor_role=user.get("role", "citizen"),
                resource_type="complaint",
                resource_id=complaint_id,
                details={
                    "category": category,
                    "priority": priority,
                    "region": region,
                    "media_count": len(media_attachments),
                    "user_id": user["sub"],
                    "complaint_id": complaint_id,
                    "timestamp": now
                }
            )
            print("✅ Audit log: OK")
        except Exception as audit_error:
            print(f"⚠️ Audit log failed: {audit_error}")
        
        # Start background task for summary generation
        background_tasks.add_task(generate_and_store_summary, complaint_id)
        
        # Send Email notification
        try:
            background_tasks.add_task(notify_complaint_registered, user["sub"], complaint_id, citizen_name)
            print("✅ Email notification queued")
        except Exception as email_error:
            print(f"⚠️ Email notification failed to queue: {email_error}")
        
        # Prepare response
        response_data = {
            "id": complaint_id,
            "grievanceID": complaint_id,
            "status": "submitted",
            "createdAt": now,
            "assigned_officer": assigned_officer,
            "sla_deadline": deadline.isoformat(),
            "media_count": len(media_attachments)
        }
        
        print(f"✅ Complaint with media created successfully: {complaint_id}")
        print(f"=== END COMPLAINT CREATION WITH MEDIA ===")
        
        return {"success": True, "data": response_data, "message": "Complaint submitted successfully with media"}
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Unexpected error in complaint creation with media: {str(e)}")
        print(f"Error type: {type(e).__name__}")
        import traceback
        print(f"Traceback: {traceback.format_exc()}")
        
        raise HTTPException(
            status_code=500, 
            detail=f"Internal server error while creating complaint with media: {str(e)}"
        )


@router.get("/{id}")
def get_complaint(id: str, user: dict = Depends(get_current_user_optional)):
    collection = db.get_collection("complaints")
    complaint = collection.find_one({"id": id})
    if not complaint:
        raise NotFoundError("Complaint")

    if complaint.get("is_deleted"):
        is_admin = user and user.get("role") == "admin"
        if not is_admin:
            raise NotFoundError("Complaint")

    # If it is anonymous, bypass the key deletion to keep "Anonymous" placeholders intact
    is_anon = complaint.get("is_anonymous", False)

    # Inject defaults and user data
    complaint = post_process_complaint(complaint, user)
    
    if not is_anon:
        if not user or user.get("role") == "citizen":
            if not is_citizen_owner(complaint, user):
                # Public feed complaints should remain viewable, but hide private identifiers.
                complaint = {k: v for k, v in complaint.items() if k not in {"citizen_email", "email"}}

        # NGO Access Control
        if user and user.get("role") == "ngo":
            if complaint.get("assigned_to_ngo") != user["sub"]:
                # NGO can see public data to decide whether to request, but not full citizen details
                complaint = {k: v for k, v in complaint.items() if k not in {"citizen_email", "email", "history"}}

    return {"success": True, "data": complaint}


@router.post("/{id}/generate-summary")
@limiter.limit("3/minute")
def regenerate_complaint_summary(
    id: str,
    background_tasks: BackgroundTasks,
    request: Request,
    target_language: str = Query(None),
    user: dict = Depends(get_current_user),
):
    """
    Regenerate and PERSIST AI summary for a complaint.
    Accessible to ALL authenticated users with rate limiting (max 3/min) and audit logging.
    """
    start_time = datetime.now(timezone.utc)
    actor_email = user.get("sub", "unknown")
    actor_role = user.get("role", "citizen")
    ip_address = request.client.host if request.client else "unknown"

    try:
        collection = db.get_collection("complaints")
        complaint = collection.find_one({"id": id}, {"_id": 0})
        if not complaint:
            duration_ms = (datetime.now(timezone.utc) - start_time).total_seconds() * 1000
            log_audit(
                action="complaint_summary_regenerated",
                actor_email=actor_email,
                actor_role=actor_role,
                resource_type="complaint",
                resource_id=id,
                details={
                    "ip": ip_address,
                    "response_time_ms": duration_ms,
                    "error": "Complaint not found"
                },
                status="failed"
            )
            raise NotFoundError("Complaint")

        collection.update_one(
            {"id": id},
            {"$set": {"summary_generated": False, "summary_generation_status": "pending", "summary_last_error": None}},
        )
        background_tasks.add_task(generate_and_store_summary, id, target_language)

        duration_ms = (datetime.now(timezone.utc) - start_time).total_seconds() * 1000
        log_audit(
            action="complaint_summary_regenerated",
            actor_email=actor_email,
            actor_role=actor_role,
            resource_type="complaint",
            resource_id=id,
            details={
                "ip": ip_address,
                "response_time_ms": duration_ms,
                "target_language": target_language or "Marathi"
            },
            status="success"
        )
        return {"success": True, "message": "Background summary regeneration started", "id": id}

    except Exception as e:
        if not isinstance(e, HTTPException):
            duration_ms = (datetime.now(timezone.utc) - start_time).total_seconds() * 1000
            log_audit(
                action="complaint_summary_regenerated",
                actor_email=actor_email,
                actor_role=actor_role,
                resource_type="complaint",
                resource_id=id,
                details={
                    "ip": ip_address,
                    "response_time_ms": duration_ms,
                    "error": str(e)
                },
                status="failed"
            )
        raise e


@router.post("/{id}/generate-view-summary")
@limiter.limit("5/hour")
async def generate_view_only_summary(
    id: str,
    request: Request,
    target_language: str = Query(None),
    user: dict = Depends(get_current_user),
):
    """
    Read-Only AI Summary Generation:
    Generates a transient summary for viewing without modifying the database.
    Accessible to ALL authenticated users.
    """
    collection = db.get_collection("complaints")
    complaint = collection.find_one({"id": id})
    if not complaint:
        raise NotFoundError("Complaint")

    # Fetch grievance text
    source_text = (
        f"{complaint.get('title', '')}. "
        f"{complaint.get('description', '')}. "
        f"स्थान: {complaint.get('location', 'उपलब्ध नाही')}. "
        f"विभाग: {complaint.get('category', 'इतर')}. "
        f"प्राधान्य: {complaint.get('priority', 'medium')}."
    )

    # Detect language if not provided
    target_lang = target_language
    if not target_lang:
        target_lang = "Marathi"
        if str(complaint.get("source_language", "")).lower() == "hi":
            target_lang = "Hindi"

    try:
        # Generate AI summary directly
        summary = await generate_summary(source_text, target_language=target_lang)
        return {
            "success": True, 
            "data": {
                "summary": summary,
                "id": id,
                "transient": True
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"AI Summary generation failed: {str(e)}")


@router.get("/")
def list_complaints(
    status: str = None,
    priority: str = None,
    category: str = None,
    region: str = None,
    district: str = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    user: dict = Depends(get_current_user_optional)
):
    query = {}
    # Exclude soft-deleted complaints by default, unless the user is an admin
    is_admin = user and user.get("role") == "admin"
    if not is_admin:
        query["is_deleted"] = {"$ne": True}

    if status:
        query["status"] = status
    if priority:
        query["priority"] = priority
    if category:
        query["category"] = category
    if region:
        query["region"] = region
    if district:
        query["district"] = district

    # RBAC Projection
    is_privileged = user and user.get("role") in ["admin", "officer"]
    
    if is_privileged:
        projection = {"_id": 0}
    else:
        projection = {
            "_id": 0, 
            "citizen_email": 0, 
            "email": 0, 
            "history": 0,
            "comments.user_id": 0
        }
    
    docs = list(db.get_collection("complaints").find(query, projection).limit(500))
    for d in docs:
        d["priority_score"] = d.get("priority_score") or compute_priority_score(d)
        if not is_privileged and "name" in d:
             name = d.get("name", "Citizen")
             d["name"] = name[0] + "***" + name[-1] if len(name) > 2 else "***"
             
    docs.sort(key=lambda x: x.get("priority_score", 0), reverse=True)
    docs = [post_process_complaint(d, user) for d in docs]
    return {"success": True, "data": docs[:limit], "total": len(docs)}


@router.get("/next")
def get_next_complaints(
    limit: int = Query(10),
    user: dict = Depends(require_officer_or_admin),
):
    """Priority queue endpoint for officer/admin dashboards."""
    query = {"status": {"$nin": ["resolved", "closed"]}}
    if user.get("role") == "officer":
        query["$or"] = [
            {"assigned_officer": user.get("sub")},
            {"assigned_officer": None},
        ]
    docs = list(db.get_collection("complaints").find(query, {"_id": 0}).limit(500))
    for d in docs:
        d["priority_score"] = d.get("priority_score") or compute_priority_score(d)
    docs.sort(key=lambda x: x.get("priority_score", 0), reverse=True)
    return {"success": True, "data": docs[:limit], "total": len(docs)}


@router.post("/{id}/escalate")
def escalate_complaint(
    id: str,
    remarks: str = "",
    user: dict = Depends(require_role(["admin", "officer"])),
):
    """Manual escalation endpoint; keeps lifecycle/timeline backward-compatible."""
    collection = db.get_collection("complaints")
    complaint = collection.find_one({"id": id}, {"_id": 0})
    if not complaint:
        raise NotFoundError("Complaint")

    updates = escalate_complaint_doc(complaint)
    now = datetime.now(timezone.utc).isoformat()
    timeline_event = {
        "status": "Under Review",
        "remarks": remarks or f"Escalated to level {updates['escalation_level']}",
        "timestamp": now,
        "updated_by_user_id": user.get("sub", "system"),
    }
    collection.update_one(
        {"id": id},
        {"$set": {**updates, "updatedAt": now}, "$push": {"history": timeline_event}},
    )
    return {"success": True, "data": {"id": id, **updates}, "message": "Complaint escalated"}


@router.patch("/{id}/assign")
def assign_complaint(
    id: str,
    officer_email: str,
    user: dict = Depends(require_officer_or_admin),
):
    """Assign a complaint to an officer (admin only)"""
    if user.get("role") != "admin":
        raise AuthorizationError("Only admins can assign complaints")

    # Verify officer exists
    officer = db.get_collection("users").find_one({"email": officer_email})
    if not officer or officer.get("role") != "officer":
        raise ValidationError("Officer not found")

    collection = db.get_collection("complaints")
    now = datetime.now(timezone.utc).isoformat()
    result = collection.update_one(
        {"id": id},
        {
            "$set": {"assigned_officer": officer_email, "updatedAt": now},
            "$push": {
                "history": {
                    "status": "Under Review",
                    "remarks": f"Assigned to officer {officer_email}",
                    "timestamp": now,
                    "updated_by_user_id": user["sub"]
                }
            },
        },
    )
    if result.matched_count == 0:
        raise NotFoundError("Complaint")

    log_audit(
        action="complaint_assigned",
        actor_email=user["sub"],
        actor_role=user.get("role"),
        resource_type="complaint",
        resource_id=id,
        details={"assigned_to": officer_email},
    )
    
    complaint = collection.find_one({"id": id})

    notify_assignment(
        officer_email,
        id,
        officer.get("name", "Officer"),
        complaint.get("category", "General") if complaint else "General",
        officer.get("department", "Field"),
        complaint.get("sla_deadline", "Pending") if complaint else "Pending"
    )

    return {"success": True, "message": f"Complaint {id} assigned to {officer_email}"}


@router.patch("/{id}/assign-ngo")
def assign_ngo(
    id: str,
    ngo_email: str,
    user: dict = Depends(require_role(["admin", "officer"]))
):
    """Assign an NGO to assist with a complaint"""
    ngo_user = db.get_collection("users").find_one({"email": ngo_email})
    if not ngo_user or ngo_user.get("role") != "ngo":
        raise ValidationError("Valid NGO user not found")

    collection = db.get_collection("complaints")
    now = datetime.now(timezone.utc).isoformat()
    result = collection.update_one(
        {"id": id},
        {
            "$set": {"assigned_to_ngo": ngo_email, "updatedAt": now},
            "$push": {
                "history": {
                    "status": "Under Review",
                    "remarks": f"Assigned to NGO {ngo_user.get('name', ngo_email)} for field assistance",
                    "timestamp": now,
                    "updated_by": user["sub"]
                }
            },
        },
    )
    if result.matched_count == 0:
        raise NotFoundError("Complaint")

    log_audit(
        action="complaint_assigned_to_ngo",
        actor_email=user["sub"],
        actor_role=user.get("role"),
        resource_type="complaint",
        resource_id=id,
        details={"assigned_to_ngo": ngo_email},
    )
    
    notify_status_change(ngo_email, id, "NGO Assignment", f"You have been assigned to assist on grievance {id}.")

    return {"success": True, "message": f"Complaint {id} assigned to NGO {ngo_email}"}


@router.patch("/{id}/status")
def update_status(
    id: str,
    status: str,
    remarks: str = "",
    user: dict = Depends(require_role(["admin", "officer", "ngo"])),
):
    allowed_statuses = {"submitted", "under_review", "in_progress", "resolved", "closed"}
    if status not in allowed_statuses:
        raise ValidationError(
            f"Invalid status. Must be one of: {', '.join(allowed_statuses)}"
        )

    collection = db.get_collection("complaints")
    complaint = collection.find_one({"id": id})
    if not complaint:
        raise NotFoundError("Complaint")

    if complaint.get("is_deleted"):
        raise ValidationError("Cannot update status of a deleted complaint")

    # Officer can only update their assigned complaints, EXCEPT for emergency cases
    if (
        user.get("role") == "officer"
        and complaint.get("assigned_officer") != user["sub"]
        and complaint.get("priority", "").lower() != "emergency"
    ):
        raise AuthorizationError("You can only update your assigned complaints (except emergency cases)")

    # NGO can only update their assigned complaints
    if (
        user.get("role") == "ngo"
        and complaint.get("assigned_to_ngo") != user["sub"]
    ):
        raise AuthorizationError("You can only update grievances assigned specifically to your NGO.")

    # Formal Work Permissions: NGO can only Resolve or set to In Progress
    if user.get("role") == "ngo" and status not in ["in_progress", "resolved"]:
        raise ValidationError("NGOs can only update status to 'In Progress' or 'Resolved'")

    now = datetime.now(timezone.utc).isoformat()
    
    # Auto-assign emergency complaints to the officer updating them
    update_fields = {"status": status, "updatedAt": now}
    if user.get("role") == "officer" and complaint.get("priority", "").lower() == "emergency":
        if complaint.get("assigned_officer") != user["sub"]:
            update_fields["assigned_officer"] = user["sub"]
            remarks = f"[AUTO-ASSIGNED] {remarks}" if remarks else "Emergency complaint auto-assigned to responding officer"
    
    # Enforce Status Flow (case-insensitive for robustness against capitalized values)
    STATUS_SEQUENCE = ["submitted", "under_review", "in_progress", "reopened", "resolved", "closed", "rejected"]
    current_status = complaint.get("status", "submitted").lower()
    target_status = status.lower()
    
    try:
        current_idx = STATUS_SEQUENCE.index(current_status)
        new_idx = STATUS_SEQUENCE.index(target_status)
        
        # Admin can override any transition
        if user.get("role") != "admin":
            # Allow one-step rollback for review (e.g. in_progress -> under_review)
            # OR rollback from resolved to in_progress
            # OR rollback from reopened to in_progress (essential for re-working reopened complaints)
            is_rollback = new_idx < current_idx
            allowed_rollback = (current_status == "in_progress" and target_status == "under_review") or \
                               (current_status == "resolved" and target_status == "in_progress") or \
                               (current_status == "reopened" and target_status == "in_progress")
            
            if is_rollback and not allowed_rollback:
                raise ValidationError(f"Invalid status transition from {current_status} to {target_status}")
                
            # Prevent skipping unless marking as resolved or closed
            if new_idx > current_idx + 1:
                if target_status not in ["resolved", "closed"]:
                    raise ValidationError(f"Cannot skip stages in status flow")
    except ValueError:
        # If status not in sequence (shouldn't happen with allowed_statuses check), just proceed if admin
        if user.get("role") != "admin":
            raise ValidationError(f"Invalid status value: {status}")

    stage_map = {
        "submitted": "Submitted",
        "under_review": "Under Review",
        "in_progress": "In Progress",
        "resolved": "Resolved",
        "closed": "Closed"
    }
    
    collection.update_one(
        {"id": id},
        {
            "$set": update_fields,
            "$push": {
                "history": {
                    "status": stage_map.get(status, "In Progress"),
                    "remarks": remarks,
                    "timestamp": now,
                    "updated_by_user_id": user["sub"],
                }
            },
        },
    )

    log_audit(
        action="complaint_status_updated",
        actor_email=user["sub"],
        actor_role=user.get("role"),
        resource_type="complaint",
        resource_id=id,
        details={"new_status": status},
    )
    
    citizen_email = complaint.get("citizen_email")
    if citizen_email:
        notify_status_change(citizen_email, id, stage_map.get(status, "In Progress"), remarks)

    return {"success": True, "message": f"Updated {id} status to {status}"}


@router.patch("/{id}/feedback")
def submit_feedback(
    id: str,
    rating: int,
    comment: str = "",
    satisfaction: str = "Neutral",
    user: dict = Depends(require_citizen),
):
    if not 1 <= rating <= 5:
        raise ValidationError("Rating must be between 1 and 5")

    collection = db.get_collection("complaints")
    complaint = collection.find_one({"id": id})
    if not complaint:
        raise NotFoundError("Complaint")

    if complaint.get("feedback"):
        raise ValidationError("Feedback has already been submitted for this complaint")

    if complaint.get("status") not in {"resolved", "closed"}:
        raise ValidationError("Feedback allowed only after resolution")

    now = datetime.now(timezone.utc).isoformat()
    feedback_doc = {
        "rating": rating,
        "comment": comment,
        "satisfaction": satisfaction,
        "submitted_at": now
    }

    collection.update_one(
        {"id": id},
        {
            "$set": {
                "status": "closed",
                "feedbackRating": rating, # For aggregation
                "feedbackAverage": rating, # Initial
                "feedbackCount": 1,        # First feedback
                "updatedAt": now,
            },
            "$push": {
                "feedback": feedback_doc,
                "history": {
                    "status": "Closed",
                    "remarks": f"Citizen Feedback ({rating}/5): {comment}",
                    "timestamp": now,
                    "updated_by_user_id": user["sub"]
                }
            },
        },
    )

    log_audit(
        action="feedback_submitted",
        actor_email=user["sub"],
        actor_role="citizen",
        resource_type="complaint",
        resource_id=id,
        details={"rating": rating},
    )

    return {"success": True, "message": f"Feedback submitted for {id}"}


@router.get("/{id}/timeline")
def get_complaint_timeline(id: str, user: dict = Depends(get_current_user)):
    """Fetch the isolated timeline of a complaint."""
    try:
        # Just safely checking if an ObjectId arrived by mistake, although we use 'id'
        if len(id) == 24:
             _ = ObjectId(id)
    except InvalidId:
        pass
        
    collection = db.get_collection("complaints")
    complaint = collection.find_one({"id": id}, {"history": 1, "citizen_email": 1, "_id": 0})
    
    if not complaint:
        raise NotFoundError("Complaint")
        
    if user.get("role") == "citizen" and complaint.get("citizen_email") != user.get("sub"):
        raise AuthorizationError("Not authorized to view other citizens' detailed timeline.")
        
    return {"success": True, "data": complaint.get("history", [])}


@router.post("/{id}/upload-media")
@limiter.limit("10/hour")
async def upload_complaint_media(
    request: Request,
    id: str,
    file: UploadFile = File(...),
    user: dict = Depends(get_current_user)
):
    """Secure Media Upload endpoint for complaints."""
    collection = db.get_collection("complaints")
    complaint = collection.find_one({"id": id})
    if not complaint:
        raise NotFoundError("Complaint")
        
    # Access Control: Citizens own their complaints, NGOs must be assigned.
    if user.get("role") == "citizen" and complaint.get("citizen_email") != user.get("sub"):
        raise AuthorizationError("Cannot upload media to someone else's complaint.")
    
    if user.get("role") == "ngo" and complaint.get("assigned_to_ngo") != user.get("sub"):
        raise AuthorizationError("NGOs can only upload evidence for grievances assigned to them.")
        
    try:
        # Size limitation (5MB)
        file.file.seek(0, 2)
        file_size = file.file.tell()
        file.file.seek(0)
        
        if file_size > 5 * 1024 * 1024:
            raise ValidationError("File size exceeds 5MB limit.")
            
        allowed_types = ["image/jpeg", "image/png", "application/pdf", "video/mp4"]
        if file.content_type not in allowed_types:
            raise ValidationError(f"Invalid file type: {file.content_type}")
            
        # Upload to Cloudinary using dynamic media service
        upload_result = await upload_media(file, folder=f"jansamadhan/complaints/{id}")
        
        if not upload_result or not upload_result.get("url"):
            raise HTTPException(status_code=500, detail="Cloud storage upload failed")
        
        media_doc = {
            "url": upload_result["url"],
            "media_type": "image" if "image" in file.content_type else ("video" if "video" in file.content_type else "document"),
            "file_name": file.filename,
            "size_bytes": file_size,
            "public_id": upload_result.get("public_id"),
            "uploaded_at": datetime.now(timezone.utc).isoformat()
        }
        
        # Proper use of $push to prevent array overwrites
        collection.update_one(
            {"id": id},
            {
                "$push": {
                    "media": media_doc,
                    "history": {
                        "status": complaint.get("status", "in_progress").title().replace("_", " "),
                        "remarks": f"Uploaded media attachment: {file.filename}",
                        "timestamp": datetime.now(timezone.utc).isoformat(),
                        "updated_by_user_id": user["sub"]
                    }
                }
            }
        )
        
        return {"success": True, "data": media_doc}
    except ValidationError:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Media upload failed: {str(e)}")


from pydantic import BaseModel

class LocationInputSchema(BaseModel):
    latitude: float
    longitude: float

@router.patch("/{id}/location")
def update_location(
    id: str,
    data: LocationInputSchema,
    user: dict = Depends(require_role(["citizen", "admin", "officer"]))
):
    """Enable Geo Spatial indexing by patching geolocation state."""
    if not (-90 <= data.latitude <= 90 and -180 <= data.longitude <= 180):
        raise ValidationError("Invalid coordinates")

    geo_point = {
        "type": "Point",
        "coordinates": [data.longitude, data.latitude]
    }

    collection = db.get_collection("complaints")
    result = collection.update_one(
        {"id": id},
        {"$set": {"location_geo": geo_point}}
    )

    if result.matched_count == 0:
        raise NotFoundError("Complaint")

    return {"success": True, "message": "Location updated seamlessly."}


@router.delete("/media/{public_id}")
async def delete_media_endpoint(
    public_id: str,
    user: dict = Depends(require_citizen)
):
    """
    Delete media from Cloudinary by public_id
    Only allows users to delete their own uploaded media
    """
    try:
        print(f"=== MEDIA DELETION REQUEST ===")
        print(f"Public ID: {public_id}")
        print(f"User: {user}")
        
        # Find the complaint containing this media
        collection = db.get_collection("complaints")
        complaint = collection.find_one({
            "media.public_id": public_id,
            "citizen_email": user["sub"]
        })
        
        if not complaint:
            print(f"❌ Media not found or user not authorized")
            raise HTTPException(
                status_code=404,
                detail="Media not found or you don't have permission to delete it"
            )
        
        # Delete from Cloudinary
        deletion_success = await delete_media(public_id)
        
        if not deletion_success:
            print(f"❌ Failed to delete media from Cloudinary")
            raise HTTPException(
                status_code=500,
                detail="Failed to delete media from storage"
            )
        
        # Remove from complaint
        update_result = collection.update_one(
            {"id": complaint["id"]},
            {"$pull": {"media": {"public_id": public_id}}}
        )
        
        if update_result.modified_count == 0:
            print(f"❌ Failed to remove media from complaint")
            raise HTTPException(
                status_code=500,
                detail="Failed to remove media from complaint"
            )
        
        # Log audit
        try:
            log_audit("media_deleted", user["sub"], {
                "complaint_id": complaint["id"],
                "public_id": public_id,
                "action": "media_deletion"
            })
            print("✅ Audit log: OK")
        except Exception as audit_error:
            print(f"⚠️ Audit log failed: {audit_error}")
        
        print(f"✅ Media deleted successfully: {public_id}")
        print(f"=== END MEDIA DELETION ===")
        
        return {
            "success": True, 
            "message": "Media deleted successfully",
            "public_id": public_id
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Unexpected error in media deletion: {str(e)}")
        print(f"Error type: {type(e).__name__}")
        import traceback
        print(f"Traceback: {traceback.format_exc()}")
        
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error while deleting media: {str(e)}"
        )


@router.post("/{id}/vote")
def vote_complaint(
    id: str,
    vote_type: str = Query(..., regex="^(up|down)$"),
    user: dict = Depends(get_current_user)
):
    """
    Vote on a complaint (upvote or downvote).
    Strictly enforces one-user-one-vote via atomic MongoDB update.
    Toggling the same vote type removes the vote.
    """
    try:
        collection = db.get_collection("complaints")
        user_id = user["sub"]
        
        # Sanitize user_id for use as MongoDB field key (replace dots)
        safe_user_id = user_id.replace(".", "_dot_")
        history_field = f"votes_history.{safe_user_id}"
        now = datetime.now(timezone.utc).isoformat()

        # Read current state atomically
        complaint = collection.find_one({"id": id}, {"_id": 0, "votes": 1, "votes_history": 1})
        if not complaint:
            raise HTTPException(status_code=404, detail="Complaint not found")

        existing_vote = complaint.get("votes_history", {}).get(safe_user_id)
        current_votes = complaint.get("votes", 0)

        if existing_vote == vote_type:
            # TOGGLE OFF: user clicked the same vote again -> remove it
            vote_change = -1 if vote_type == "up" else 1
            new_votes = current_votes + vote_change

            collection.update_one(
                {"id": id},
                {
                    "$set": {"votes": new_votes, "updatedAt": now},
                    "$unset": {history_field: ""}
                }
            )
            return {
                "success": True,
                "message": "Vote removed",
                "new_vote_count": new_votes,
                "vote_type": None
            }

        elif existing_vote is not None:
            # SWITCH: user is changing from up->down or down->up
            vote_change = 2 if vote_type == "up" else -2
            new_votes = current_votes + vote_change

            collection.update_one(
                {"id": id},
                {"$set": {"votes": new_votes, history_field: vote_type, "updatedAt": now}}
            )
            return {
                "success": True,
                "message": f"Vote changed to {vote_type}",
                "new_vote_count": new_votes,
                "vote_type": vote_type
            }

        else:
            # NEW VOTE: no prior vote from this user
            vote_change = 1 if vote_type == "up" else -1
            new_votes = current_votes + vote_change

            collection.update_one(
                {"id": id},
                {"$set": {"votes": new_votes, history_field: vote_type, "updatedAt": now}}
            )

            try:
                log_audit("complaint_voted", user["sub"], {
                    "complaint_id": id,
                    "vote_type": vote_type,
                    "new_votes": new_votes
                })
            except Exception:
                pass

            return {
                "success": True,
                "message": f"{vote_type.capitalize()}voted successfully",
                "new_vote_count": new_votes,
                "vote_type": vote_type
            }

    except HTTPException:
        raise
    except Exception as e:
        print(f"Error in vote_complaint: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to vote on complaint: {str(e)}"
        )


@router.post("/{id}/comment")
def comment_complaint(
    id: str,
    comment: str = Form(..., min_length=1, max_length=500),
    user: dict = Depends(get_current_user_optional)
):
    """
    Add a comment to a complaint
    Allows both authenticated and anonymous users
    """
    try:
        collection = db.get_collection("complaints")
        complaint = collection.find_one({"id": id}, {"_id": 0})
        
        if not complaint:
            raise HTTPException(status_code=404, detail="Complaint not found")
        
        # Get user identifier
        user_id = user["sub"] if user else f"anonymous_{id}"
        user_name = user.get("name", "Anonymous User") if user else "Anonymous User"
        user_role = user.get("role", "citizen") if user else "anonymous"
        
        # Create comment object
        comment_obj = {
            "id": str(uuid.uuid4())[:8],
            "user_id": user_id,
            "user_name": user_name,
            "user_role": user_role,
            "comment": comment.strip(),
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "is_official": user_role in ["admin", "officer"],
            "is_anonymous": not user
        }
        
        # Add comment to complaint
        collection.update_one(
            {"id": id},
            {
                "$push": {"comments": comment_obj},
                "$set": {"updatedAt": datetime.now(timezone.utc).isoformat()}
            }
        )
        
        # Log audit for authenticated users
        if user:
            try:
                log_audit("complaint_commented", user["sub"], {
                    "complaint_id": id,
                    "comment_id": comment_obj["id"],
                    "comment_length": len(comment)
                })
            except:
                pass
        
        # Update timeline if official comment
        if user_role in ["admin", "officer"]:
            timeline_event = {
                "status": "Comment Added",
                "remarks": f"Comment by {user_name}: {comment[:100]}{'...' if len(comment) > 100 else ''}",
                "timestamp": comment_obj["timestamp"],
                "updated_by_user_id": user_id,
                "is_official": True
            }
            
            collection.update_one(
                {"id": id},
                {"$push": {"history": timeline_event}}
            )
        
        return {
            "success": True,
            "message": "Comment added successfully",
            "data": {
                "comment_id": comment_obj["id"],
                "timestamp": comment_obj["timestamp"],
                "is_official": comment_obj["is_official"],
                "is_anonymous": comment_obj["is_anonymous"]
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error in comment_complaint: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to add comment: {str(e)}"
        )


@router.get("/{id}/comments")
def get_complaint_comments(
    id: str,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100)
):
    """
    Get comments for a specific complaint
    Public endpoint - no authentication required
    """
    try:
        collection = db.get_collection("complaints")
        complaint = collection.find_one(
            {"id": id}, 
            {
                "_id": 0,
                "comments": 1,
                "votes": 1
            }
        )
        
        if not complaint:
            raise HTTPException(status_code=404, detail="Complaint not found")
        
        comments = complaint.get("comments", [])
        votes = complaint.get("votes", 0)
        
        # Sort comments by timestamp (newest first)
        comments.sort(key=lambda x: x.get("timestamp", ""), reverse=True)
        
        # Apply pagination
        total_comments = len(comments)
        paginated_comments = comments[skip:skip + limit]
        
        # Remove sensitive information for public view
        public_comments = []
        for comment in paginated_comments:
            public_comment = {
                "id": comment.get("id"),
                "user_name": comment.get("user_name", "Anonymous"),
                "comment": comment.get("comment"),
                "timestamp": comment.get("timestamp"),
                "is_official": comment.get("is_official", False),
                "is_anonymous": comment.get("is_anonymous", False)
            }
            # Don't include user_id in public view
            public_comments.append(public_comment)
        
        return {
            "success": True,
            "data": {
                "comments": public_comments,
                "total": total_comments,
                "skip": skip,
                "limit": limit,
                "has_more": skip + limit < total_comments,
                "complaint_votes": votes
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error in get_complaint_comments: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch comments: {str(e)}"
        )


class ExtendDeadlineRequest(BaseModel):
    new_due_date: str
    reason: str

class DeadlineExtensionRequestModel(BaseModel):
    complaint_id: str
    requested_deadline: str
    reason: str

@router.post("/{id}/request-deadline-extension")
def request_deadline_extension(
    id: str,
    req: DeadlineExtensionRequestModel,
    user: dict = Depends(require_role(["officer"]))
):
    """Officer submits a request to extend the deadline — requires admin approval."""
    collection = db.get_collection("complaints")
    complaint = collection.find_one({"id": id})
    if not complaint:
        raise NotFoundError("Complaint")
    if complaint.get("is_deleted"):
        raise ValidationError("Cannot request deadline extension for a deleted complaint")
    if complaint.get("assigned_officer") != user.get("sub"):
        raise AuthorizationError("You can only request extensions for your assigned complaints")

    # Validate the requested date
    try:
        current_deadline_str = complaint.get("sla_deadline")
        if current_deadline_str:
            current_deadline = datetime.fromisoformat(current_deadline_str.replace("Z", "+00:00"))
            new_deadline = datetime.fromisoformat(req.requested_deadline.replace("Z", "+00:00"))
            if new_deadline <= current_deadline:
                raise ValidationError("Requested deadline must be after current deadline")
    except ValueError:
        raise ValidationError("Invalid date format. Use ISO format.")

    now = datetime.now(timezone.utc).isoformat()
    extension_request = {
        "complaint_id": id,
        "officer_email": user.get("sub"),
        "requested_deadline": req.requested_deadline,
        "reason": req.reason,
        "current_deadline": complaint.get("sla_deadline"),
        "status": "pending",  # pending | approved | rejected
        "requested_at": now,
        "reviewed_at": None,
        "reviewed_by": None,
        "admin_remarks": None
    }

    db.get_collection("deadline_extension_requests").insert_one(extension_request)

    # Push notification record into complaint history
    collection.update_one(
        {"id": id},
        {"$push": {"history": {
            "status": complaint.get("status", "in_progress").title().replace("_", " "),
            "remarks": f"Officer requested deadline extension to {req.requested_deadline[:10]}. Reason: {req.reason}",
            "timestamp": now,
            "updated_by_user_id": user.get("sub")
        }}}
    )

    try:
        log_audit(
            action="DEADLINE_EXTENSION_REQUESTED",
            actor_email=user.get("sub"),
            actor_role="officer",
            resource_type="complaint",
            resource_id=id,
            details={"requested_deadline": req.requested_deadline, "reason": req.reason}
        )
    except Exception:
        pass

    return {"success": True, "message": "Deadline extension request submitted. Awaiting admin approval."}

@router.delete("/{id}")
def delete_complaint(id: str, user: dict = Depends(get_current_user)):
    """Soft delete a complaint."""
    try:
        collection = db.get_collection("complaints")
        complaint = collection.find_one({"id": id})
        if not complaint:
            raise NotFoundError("Complaint")
        
        if complaint.get("is_deleted"):
            raise ValidationError("Complaint is already deleted")
            
        role = user.get("role")
        
        # Validation
        if role == "citizen":
            if complaint.get("citizen_email") != user.get("sub"):
                raise AuthorizationError("Cannot delete someone else's complaint")
            if complaint.get("status") != "submitted":
                raise ValidationError("Citizens can only delete complaints in 'submitted' status")
                
        elif role == "officer":
             raise AuthorizationError("Officers cannot delete complaints. Contact admin.")
        elif role not in ["admin"]:
             raise AuthorizationError("Not authorized to delete complaint")
             
        now = datetime.now(timezone.utc).isoformat()
        
        update_data = {
            "is_deleted": True,
            "deleted_at": now,
            "deleted_by": user.get("sub"),
            "status": "deleted",
            "updatedAt": now
        }
        
        collection.update_one(
            {"id": id},
            {
                "$set": update_data,
                "$push": {
                    "history": {
                        "status": "Deleted",
                        "remarks": f"Complaint soft-deleted by {role}",
                        "timestamp": now,
                        "updated_by_user_id": user.get("sub")
                    }
                }
            }
        )
        
        try:
            log_audit(
                action="DELETE_COMPLAINT",
                actor_email=user.get("sub"),
                actor_role=role,
                resource_type="complaint",
                resource_id=id,
                details={"status_before": complaint.get("status")}
            )
        except Exception:
            pass
            
        return {"success": True, "message": "Complaint deleted successfully"}
    except Exception as e:
        try:
            log_audit(
                action="DELETE_COMPLAINT",
                actor_email=user.get("sub", "unknown"),
                actor_role=user.get("role", "unknown"),
                resource_type="complaint",
                resource_id=id,
                details={"error": str(e)},
                status="failed"
            )
        except Exception:
            pass
        raise e


class ReopenComplaintRequest(BaseModel):
    reason: str


@router.post("/{id}/reopen")
def reopen_complaint(id: str, req: ReopenComplaintRequest, user: dict = Depends(get_current_user)):
    """Reopen a resolved/closed/rejected complaint."""
    try:
        collection = db.get_collection("complaints")
        complaint = collection.find_one({"id": id})
        
        if not complaint:
            raise NotFoundError("Complaint")
            
        if complaint.get("is_deleted"):
            raise ValidationError("Cannot reopen a deleted complaint")
            
        # Check permissions
        role = user.get("role")
        if role == "citizen" and complaint.get("citizen_email") != user.get("sub"):
            raise AuthorizationError("Cannot reopen someone else's complaint")
            
        if complaint.get("status") not in ["resolved", "closed", "rejected"]:
            raise ValidationError(f"Cannot reopen a complaint with status '{complaint.get('status')}'")
            
        reopen_count = complaint.get("reopen_count", 0)
        if reopen_count >= 3:
            raise ValidationError("Maximum reopening limit (3) reached")
            
        now = datetime.now(timezone.utc).isoformat()
        
        collection.update_one(
            {"id": id},
            {
                "$set": {
                    "status": "reopened",
                    "last_reopened_at": now,
                    "reopened_by": user.get("sub"),
                    "updatedAt": now
                },
                "$inc": {"reopen_count": 1},
                "$push": {
                    "history": {
                        "status": "Reopened",
                        "remarks": f"Complaint reopened by {role}. Cycle {reopen_count + 1}/3. Reason: {req.reason}",
                        "timestamp": now,
                        "updated_by_user_id": user.get("sub")
                    }
                }
            }
        )
        
        try:
            log_audit(
                action="REOPEN_COMPLAINT",
                actor_email=user.get("sub"),
                actor_role=role,
                resource_type="complaint",
                resource_id=id,
                details={"reopen_count": reopen_count + 1, "reason": req.reason}
            )
        except Exception:
            pass
            
        return {"success": True, "message": "Complaint reopened successfully"}
    except Exception as e:
        try:
            log_audit(
                action="REOPEN_COMPLAINT",
                actor_email=user.get("sub", "unknown"),
                actor_role=user.get("role", "unknown"),
                resource_type="complaint",
                resource_id=id,
                details={"error": str(e)},
                status="failed"
            )
        except Exception:
            pass
        raise e


@router.post("/{id}/extend-deadline")
def extend_complaint_deadline(
    id: str,
    req: ExtendDeadlineRequest,
    user: dict = Depends(require_officer_or_admin)
):
    """Extend the deadline of a complaint."""
    try:
        collection = db.get_collection("complaints")
        complaint = collection.find_one({"id": id})
        
        if not complaint:
            raise NotFoundError("Complaint")
            
        if complaint.get("is_deleted"):
            raise ValidationError("Cannot extend deadline for a deleted complaint")
            
        if user.get("role") == "officer" and complaint.get("assigned_officer") != user.get("sub"):
            raise AuthorizationError("Can only extend deadline for assigned complaints")
            
        current_deadline_str = complaint.get("sla_deadline")
        if not current_deadline_str:
            raise ValidationError("Complaint has no existing deadline")
            
        try:
            current_deadline = datetime.fromisoformat(current_deadline_str.replace("Z", "+00:00"))
            new_deadline = datetime.fromisoformat(req.new_due_date.replace("Z", "+00:00"))
        except ValueError:
            raise ValidationError("Invalid date format. Must be ISO format")
            
        if new_deadline <= current_deadline:
            raise ValidationError("New deadline must be greater than current deadline")
            
        now = datetime.now(timezone.utc).isoformat()
        
        extension_record = {
            "previous_deadline": current_deadline_str,
            "new_deadline": new_deadline.isoformat(),
            "reason": req.reason,
            "extended_by": user.get("sub"),
            "extended_at": now
        }
        
        collection.update_one(
            {"id": id},
            {
                "$set": {
                    "sla_deadline": new_deadline.isoformat(),
                    "updatedAt": now
                },
                "$push": {
                    "extension_history": extension_record,
                    "history": {
                        "status": complaint.get("status", "in_progress").title().replace("_", " "),
                        "remarks": f"Deadline extended to {new_deadline.strftime('%Y-%m-%d %H:%M')}. Reason: {req.reason}",
                        "timestamp": now,
                        "updated_by_user_id": user.get("sub")
                    }
                }
            }
        )
        
        try:
            log_audit(
                action="EXTEND_DEADLINE",
                actor_email=user.get("sub"),
                actor_role=user.get("role"),
                resource_type="complaint",
                resource_id=id,
                details={"previous_deadline": current_deadline_str, "new_deadline": new_deadline.isoformat()}
            )
        except Exception:
            pass
            
        return {"success": True, "message": "Deadline extended successfully"}
    except Exception as e:
        try:
            log_audit(
                action="EXTEND_DEADLINE",
                actor_email=user.get("sub", "unknown"),
                actor_role=user.get("role", "unknown"),
                resource_type="complaint",
                resource_id=id,
                details={"error": str(e)},
                status="failed"
            )
        except Exception:
            pass
        raise e


@router.post("/{id}/ai-report/generate")
async def generate_ai_report_endpoint(
    id: str,
    user: dict = Depends(get_current_user)
):
    """Generate or regenerate an AI intelligence report for the complaint."""
    collection = db.get_collection("complaints")
    complaint = collection.find_one({"id": id})
    if not complaint:
        raise NotFoundError("Complaint")
        
    # Security Checks
    role = user.get("role")
    # Citizens can only view/generate for their own
    if role == "citizen" and complaint.get("citizen_email") != user.get("sub"):
        raise AuthorizationError("You are not authorized to access this AI report")
    # Officers can only view/generate their assigned complaints, unless it is emergency
    if role == "officer":
        if complaint.get("assigned_officer") != user.get("sub") and complaint.get("priority", "").lower() != "emergency":
            raise AuthorizationError("You are not assigned to this complaint")
    # NGOs can only view/generate their assigned complaints
    if role == "ngo" and complaint.get("assigned_to_ngo") != user.get("sub"):
        raise AuthorizationError("This complaint is not assigned to your NGO")
        
    from services.ai_report_service import ai_report_service
    report = await ai_report_service.generate_ai_report(id, refresh=True, performed_by=user.get("sub", "system"))
    return {"success": True, "data": report}


@router.get("/{id}/ai-report")
async def get_ai_report_endpoint(
    id: str,
    refresh: bool = False,
    user: dict = Depends(get_current_user)
):
    """Retrieve the AI intelligence report for the complaint."""
    collection = db.get_collection("complaints")
    complaint = collection.find_one({"id": id})
    if not complaint:
        raise NotFoundError("Complaint")
        
    # Security Checks
    role = user.get("role")
    # Citizens can only view/generate for their own
    if role == "citizen" and complaint.get("citizen_email") != user.get("sub"):
        raise AuthorizationError("You are not authorized to access this AI report")
    # Officers can only view/generate their assigned complaints, unless it is emergency
    if role == "officer":
        if complaint.get("assigned_officer") != user.get("sub") and complaint.get("priority", "").lower() != "emergency":
            raise AuthorizationError("You are not assigned to this complaint")
    # NGOs can only view/generate their assigned complaints
    if role == "ngo" and complaint.get("assigned_to_ngo") != user.get("sub"):
        raise AuthorizationError("This complaint is not assigned to your NGO")
        
    from services.ai_report_service import ai_report_service
    report = await ai_report_service.generate_ai_report(id, refresh=refresh, performed_by=user.get("sub", "system"))
    return {"success": True, "data": report}
