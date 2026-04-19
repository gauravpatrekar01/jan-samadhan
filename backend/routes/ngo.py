from fastapi import APIRouter, Depends, HTTPException, Request
from db import db
from dependencies import require_role, get_current_user
from datetime import datetime, timezone
import uuid
from schemas.complaint import NGORequestSchema, TimelineEvent
from audit import log_audit
from limiter import limiter

router = APIRouter()

@router.post("/requests")
@limiter.limit("5/hour")
def request_handling(request: Request, request_data: NGORequestSchema, user=Depends(require_role(["ngo"]))):
    """NGO requests to handle a specific grievance."""
    # Check if NGO is verified
    user_doc = db.get_collection("users").find_one({"email": user["sub"]})
    if not user_doc or not user_doc.get("verified"):
        raise HTTPException(status_code=403, detail="Your NGO account is pending verification by administration.")

    # Check if complaint exists and is available
    complaint_coll = db.get_collection("complaints")
    complaint = complaint_coll.find_one({"id": request_data.complaint_id})
    
    if not complaint:
        raise HTTPException(status_code=404, detail="Complaint not found")
    
    if complaint.get("assigned_to_ngo"):
         raise HTTPException(status_code=400, detail="Grievance already assigned to an NGO.")

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
    """View complaints currently assigned to this NGO."""
    complaints = list(db.get_collection("complaints").find({"assigned_to_ngo": user["sub"]}, {"_id": 0}).sort("updatedAt", -1))
    return {"success": True, "data": complaints}

@router.get("/available-complaints")
def get_available_complaints(user=Depends(require_role(["ngo"]))):
    """View complaints that are open/unassigned for NGOs to request."""
    # Only show complaints that are NOT assigned to any NGO and are in relevant states
    query = {
        "$or": [
            {"assigned_to_ngo": {"$exists": False}},
            {"assigned_to_ngo": None}
        ],
        "status": {"$in": ["submitted", "under_review", "assigned"]}
    }
    complaints = list(db.get_collection("complaints").find(query, {"_id": 0}).sort("createdAt", -1).limit(50))
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

