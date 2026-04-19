from fastapi import APIRouter, Depends, Query, UploadFile, File, Form, HTTPException, Request
from limiter import limiter
from services.s3_service import s3_service
from schemas.complaint import ComplaintCreate
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
from notifications import notify_status_change

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


@router.get("/")
def get_complaints(
    status: str = Query(None),
    priority: str = Query(None),
    category: str = Query(None),
    region: str = Query(None),
    search: str = Query(None),
    near: str = Query(None),
    radius: int = Query(5000),
    skip: int = Query(0),
    limit: int = Query(50),
    user: dict = Depends(get_current_user),
):
    """
    Get complaints - public feed for all users
    Citizens see all complaints (public feed)
    Officers see their assigned complaints and others
    Admins see all complaints
    """
    # Officers should be able to view all complaints in the all complaints tab.
    complaints = search_complaints(
        status=status,
        priority=priority,
        category=category,
        region=region,
        search=search,
        near=near,
        radius=radius,
        skip=skip,
        limit=limit,
    )

    # Count should match the same logic
    total = get_complaint_count(
        status=status,
        priority=priority,
        category=category,
        region=region,
        near=near,
        radius=radius,
    )

    return {"success": True, "data": complaints, "total": total}


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
    complaints = search_complaints(
        assigned_to=assigned_to,
        status=status,
        priority=priority,
        skip=skip,
        limit=limit,
    )
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
    query = {"assigned_ngo": user["sub"]}
    if status:
        query["status"] = status.lower()
    if priority:
        query["priority"] = priority.lower()

    collection = db.get_collection("complaints")
    complaints = list(collection.find(query, {"_id": 0}).sort("createdAt", -1).skip(skip).limit(limit))
    total = collection.count_documents(query)
    return {"success": True, "data": complaints, "total": total}


@router.post("/", status_code=201)
@limiter.limit("5/hour")
def create_complaint(request: Request, complaint: ComplaintCreate, user: dict = Depends(require_citizen)):
    collection = db.get_collection("complaints")
    now = datetime.now(timezone.utc).isoformat()
    complaint_id = f"JSM-{datetime.now(timezone.utc).year}-{str(uuid.uuid4())[:8].upper()}"

    user_doc = db.get_collection("users").find_one({"email": user["sub"]})
    citizen_name = user_doc.get("name", "Citizen") if user_doc else "Citizen"

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
            "assigned_officer": None,
            "assigned_ngo": None,
            "createdAt": now,
            "updatedAt": now,
            "sla_deadline": deadline.isoformat(),
            "timeline": [
                {
                    "stage": "Submitted",
                    "remarks": "Grievance filed by citizen",
                    "timestamp": now,
                    "updated_by_user_id": user["sub"],
                }
            ],
            "media": [],
            "feedback": [],
            "feedbackAverage": 0,
            "feedbackCount": 0,
        }
    )

    assigned_officer = find_officer_for_region(c_dict.get("region"))
    if assigned_officer:
        c_dict["assigned_officer"] = assigned_officer
        c_dict["timeline"].append(
            {
                "stage": "Under Review",
                "remarks": f"Auto-assigned to officer {assigned_officer} for district {c_dict.get('region')}",
                "timestamp": now,
                "updated_by_user_id": "system"
            }
        )

    collection.insert_one(c_dict)
    c_dict.pop("_id", None)

    log_audit(
        action="complaint_created",
        actor_email=user["sub"],
        actor_role="citizen",
        resource_type="complaint",
        resource_id=complaint_id,
        details={"category": complaint.category, "priority": complaint.priority},
    )

    notify_status_change(user["sub"], complaint_id, "Submitted", "Your complaint has been successfully registered.")

    return {"success": True, "data": c_dict}


@router.get("/{id}")
def get_complaint(id: str, user: dict = Depends(get_current_user_optional)):
    collection = db.get_collection("complaints")
    complaint = collection.find_one({"id": id}, {"_id": 0})
    if not complaint:
        raise NotFoundError("Complaint")

    if not user or user.get("role") == "citizen":
        sub = user.get("sub") if user else None
        if complaint.get("citizen_email") != sub:
            # Public feed complaints should remain viewable, but hide private identifiers.
            complaint = {k: v for k, v in complaint.items() if k not in {"citizen_email", "email"}}

    # NGO Access Control
    if user and user.get("role") == "ngo":
        if complaint.get("assigned_to_ngo") != user["sub"]:
            # NGO can see public data to decide whether to request, but not full citizen details
            complaint = {k: v for k, v in complaint.items() if k not in {"citizen_email", "email", "history"}}

    return {"success": True, "data": complaint}


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
                "timeline": {
                    "stage": "Under Review",
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
                    "stage": "Under Review",
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
        action="complaint_assigned_ngo",
        actor_email=user["sub"],
        actor_role=user.get("role"),
        resource_type="complaint",
        resource_id=id,
        details={"assigned_ngo": ngo_email},
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
    
    # Enforce Status Flow
    STATUS_SEQUENCE = ["submitted", "under_review", "in_progress", "resolved", "closed"]
    current_status = complaint.get("status", "submitted")
    
    try:
        current_idx = STATUS_SEQUENCE.index(current_status)
        new_idx = STATUS_SEQUENCE.index(status)
        
        if new_idx < current_idx and not (current_status == "in_progress" and status == "under_review"):
            # Allow one-step rollback for review, otherwise block
            raise ValidationError(f"Invalid status transition from {current_status} to {status}")
            
        if new_idx > current_idx + 1 and status != "resolved":
            # Prevent skipping unless marking as resolved (which can happen from in_progress)
            if not (current_status == "in_progress" and status == "resolved"):
                raise ValidationError(f"Cannot skip stages in status flow")
    except ValueError:
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
                "timeline": {
                    "stage": stage_map.get(status, "In Progress"),
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
                "feedback": feedback_doc,
                "feedbackRating": rating, # For aggregation
                "feedbackAverage": rating, # Initial
                "feedbackCount": 1,        # First feedback
                "updatedAt": now,
            },
            "$push": {
                "timeline": {
                    "stage": "Closed",
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
    complaint = collection.find_one({"id": id}, {"timeline": 1, "citizen_email": 1, "_id": 0})
    
    if not complaint:
        raise NotFoundError("Complaint")
        
    if user.get("role") == "citizen" and complaint.get("citizen_email") != user.get("sub"):
        raise AuthorizationError("Not authorized to view other citizens' detailed timeline.")
        
    return {"success": True, "data": complaint.get("timeline", [])}


@router.post("/{id}/upload-media")
@limiter.limit("10/hour")
def upload_complaint_media(
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
            
        # Actual S3 Upload
        file_extension = file.filename.split(".")[-1]
        unique_filename = f"{uuid.uuid4()}.{file_extension}"
        
        file_content = file.file.read()
        s3_url = s3_service.upload_file(file_content, file.filename, folder=f"complaints/{id}")
        
        if not s3_url:
            raise HTTPException(status_code=500, detail="Cloud storage upload failed")
        
        media_doc = {
            "url": s3_url,
            "media_type": "image" if "image" in file.content_type else ("video" if "video" in file.content_type else "document"),
            "file_name": file.filename,
            "size_bytes": file_size,
            "uploaded_at": datetime.now(timezone.utc).isoformat()
        }
        
        # Proper use of $push to prevent array overwrites
        collection.update_one(
            {"id": id},
            {"$push": {"media": media_doc}}
        )
        
        # Push timeline event to record media upload
        collection.update_one(
            {"id": id},
            {"$push": {
                "timeline": {
                    "stage": complaint.get("status", "in_progress").title().replace("_", " "),
                    "remarks": f"Uploaded media attachment: {file.filename}",
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "updated_by_user_id": user["sub"]
                }
            }}
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
