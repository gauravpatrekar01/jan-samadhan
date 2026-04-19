from fastapi import APIRouter, Depends, HTTPException, Request
from db import db
from dependencies import require_role, get_current_user
from datetime import datetime, timezone
import uuid
from schemas.complaint import NGORequestSchema, TimelineEvent
from audit import log_audit
from limiter import limiter

def mask_name(name: str) -> str:
    if not name or len(name) < 2: return "***"
    return f"{name[0]}*** {name[-1]}"

router = APIRouter()

@router.post("/requests")
@limiter.limit("5/hour")
def request_handling(request: Request, request_data: NGORequestSchema, user=Depends(require_role(["ngo"]))):
    """NGO requests to handle a specific grievance."""
    user_doc = db.get_collection("users").find_one({"email": user["sub"]})
    
    # Check if NGO is verified and active
    if not user_doc or not user_doc.get("verified"):
        raise HTTPException(status_code=403, detail="Your NGO account is pending verification by administration.")
    if not user_doc.get("is_active", True):
        raise HTTPException(status_code=403, detail="NGO account is currently inactive. Contact administration.")

    complaint_coll = db.get_collection("complaints")
    
    # Capacity Limit Check (Max 5 active cases)
    active_cases = complaint_coll.count_documents({
        "assigned_to_ngo": user["sub"],
        "status": {"$in": ["assigned", "under_review", "in_progress"]}
    })
    if active_cases >= 5:
        raise HTTPException(status_code=400, detail="NGO capacity reached. Complete existing assignments before requesting more.")

    # Check if complaint exists and is available
    complaint = complaint_coll.find_one({"id": request_data.complaint_id})
    if not complaint:
        raise HTTPException(status_code=404, detail="Complaint not found")

    # Category-Based Matching Check
    if complaint.get("category") not in user_doc.get("categories", []):
         raise HTTPException(status_code=400, detail=f"Your NGO is not authorized to handle {complaint.get('category')} cases.")
    
    if complaint.get("assigned_to_ngo"):
         raise HTTPException(status_code=400, detail="Grievance already assigned to another NGO.")

    # 8. Fraud Detection & Activity Tracking
    today = datetime.now(timezone.utc).date().isoformat()
    if user_doc.get("last_request_reset", "").split('T')[0] != today:
        db.get_collection("users").update_one(
            {"email": user["sub"]}, 
            {"$set": {"request_count_today": 0, "last_request_reset": datetime.now(timezone.utc).isoformat()}}
        )
        user_doc["request_count_today"] = 0

    if user_doc.get("request_count_today", 0) >= 10:
        db.get_collection("users").update_one({"email": user["sub"]}, {"$set": {"suspicious_activity": True}})
        raise HTTPException(status_code=429, detail="Daily request limit reached. Account flagged for automated activity check.")

    db.get_collection("users").update_one({"email": user["sub"]}, {"$inc": {"request_count_today": 1}})

    # Prevent duplicate requests

    request_coll = db.get_collection("ngo_requests")
    existing = request_coll.find_one({
        "complaint_id": request_data.complaint_id,
        "ngo_email": user["sub"],
        "status": "pending"
    })
    if existing:
        raise HTTPException(status_code=400, detail="You already have a pending request for this grievance.")

    new_req = {
        "id": str(uuid.uuid4()),
        "complaint_id": request_data.complaint_id,
        "complaint_title": complaint.get("title"),
        "ngo_email": user["sub"],
        "ngo_name": user_doc.get("name", "Unknown NGO"),
        "requested_at": datetime.now(timezone.utc).isoformat(),
        "status": "pending"
    }
    
    request_coll.insert_one(new_req)
    
    # Log timeline event in complaint
    timeline_event = {
        "status": "NGO Requested",
        "remarks": f"NGO '{user_doc.get('name')}' has requested to handle this grievance.",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "updated_by": "ngo"
    }
    complaint_coll.update_one(
        {"id": request_data.complaint_id},
        {"$push": {"history": timeline_event}}
    )

    new_req.pop("_id", None)
    return {"success": True, "data": new_req}


@router.get("/my-requests")
def get_my_requests(user=Depends(require_role(["ngo"]))):
    """View status of all requests made by the NGO."""
    requests = list(db.get_collection("ngo_requests").find({"ngo_email": user["sub"]}, {"_id": 0}).sort("requested_at", -1))
    return {"success": True, "data": requests}

@router.get("/assigned-complaints")
def get_assigned_complaints(user=Depends(require_role(["ngo"]))):
    """View complaints currently assigned to this NGO with masked names."""
    complaints = list(db.get_collection("complaints").find({"assigned_to_ngo": user["sub"]}, {"_id": 0}).sort("updatedAt", -1))
    for c in complaints:
        c["name"] = mask_name(c.get("name", "Citizen"))
    return {"success": True, "data": complaints}

@router.get("/available-complaints")
def get_available_complaints(user=Depends(require_role(["ngo"]))):
    """View complaints that are open/unassigned for NGOs to request, filtered by NGO expertise."""
    user_doc = db.get_collection("users").find_one({"email": user["sub"]})
    if not user_doc:
        raise HTTPException(status_code=404, detail="NGO details not found")
        
    ngo_categories = user_doc.get("categories", [])
    ngo_area = user_doc.get("service_area", "")

    # Base Query: Unassigned and in a state where assistance is needed
    query = {
        "$or": [
            {"assigned_to_ngo": {"$exists": False}},
            {"assigned_to_ngo": None}
        ],
        "status": {"$in": ["submitted", "under_review", "assigned"]},
        "category": {"$in": ngo_categories} # Match NGOexpertise
    }
    
    # Location Matching (Optional but prioritized)
    if ngo_area:
        query["region"] = {"$regex": ngo_area, "$options": "i"}

    complaints = list(db.get_collection("complaints").find(query, {"_id": 0, "aadhar": 0}).sort("createdAt", -1).limit(50))
    for c in complaints:
        c["name"] = mask_name(c.get("name", "Citizen"))
    return {"success": True, "data": complaints}


@router.get("/stats")
def get_ngo_stats(user=Depends(require_role(["ngo"]))):
    """Calculate performance metrics for the logged-in NGO."""
    complaint_coll = db.get_collection("complaints")
    
    # Total Resolved by this NGO
    resolved_count = complaint_coll.count_documents({
        "assigned_to_ngo": user["sub"],
        "status": {"$in": ["resolved", "closed"]}
    })
    
    # Avg Rating from public feedback on this NGO's cases
    pipeline = [
        {"$match": {"assigned_to_ngo": user["sub"], "feedback": {"$exists": True}}},
        {"$group": {"_id": None, "avgRating": {"$avg": "$feedback.rating"}}}
    ]
    rating_result = list(complaint_coll.aggregate(pipeline))
    avg_rating = round(rating_result[0]["avgRating"], 1) if rating_result else 0.0
    
    # Active cases currently being handled
    active_count = complaint_coll.count_documents({
        "assigned_to_ngo": user["sub"],
        "status": "in_progress"
    })

    return {
        "success": True, 
        "data": {
            "resolved": resolved_count,
            "avg_rating": avg_rating,
            "active": active_count,
            "impact_lives": resolved_count * 4 # Estimated families helped
        }
    }

@router.get("/profile")
def get_ngo_profile(user=Depends(require_role(["ngo"]))):
    """Retrieve full profile including verification status and rejection reasons."""
    user_doc = db.get_collection("users").find_one({"email": user["sub"]}, {"_id": 0, "password": 0})
    if not user_doc:
        raise HTTPException(status_code=404, detail="Profile not found")
    return {"success": True, "data": user_doc}

@router.patch("/profile")
def update_ngo_profile(profile_update: dict, user=Depends(require_role(["ngo"]))):
    """Allow NGO to update details/docs for re-verification if not currently verified."""
    users = db.get_collection("users")
    current = users.find_one({"email": user["sub"]})
    
    if current.get("verified") and current.get("verification_level", 0) > 0:
        raise HTTPException(status_code=403, detail="Verified profiles cannot be edited directly. Contact admin.")

    # Prevent privileged field spoofing
    for field in ["role", "email", "verified", "verification_level", "password", "resolved_cases", "avg_rating"]:
        profile_update.pop(field, None)
    
    # Reset rejection reason on update to mark as "ready for re-review"
    profile_update["rejection_reason"] = None
    
    users.update_one({"email": user["sub"]}, {"$set": profile_update})
    return {"success": True, "message": "Profile updated for re-verification."}

