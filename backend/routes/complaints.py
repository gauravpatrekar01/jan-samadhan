from fastapi import APIRouter, HTTPException, Depends, Header, Body
from schemas.complaint import ComplaintCreate
from db import db
from datetime import datetime, timezone
import uuid
from security import decode_token

router = APIRouter()


def get_current_user(authorization: str = Header(None)) -> dict:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Unauthorized")
    token = authorization.split(" ", 1)[1]
    payload = decode_token(token)
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    return payload


def require_admin(user: dict = Depends(get_current_user)) -> dict:
    if user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    return user


@router.get("/")
def get_complaints():
    collection = db.get_collection("complaints")
    complaints = list(collection.find({}, {"_id": 0}))
    return {"success": True, "data": complaints}


@router.get("/my")
def get_my_complaints(user: dict = Depends(get_current_user)):
    collection = db.get_collection("complaints")
    complaints = list(collection.find({"email": user["sub"]}, {"_id": 0}))
    return {"success": True, "data": complaints}


@router.get("/assigned")
def get_assigned_complaints(user: dict = Depends(get_current_user)):
    # Officers see all complaints; extend with assignment logic as needed
    collection = db.get_collection("complaints")
    complaints = list(collection.find({}, {"_id": 0}))
    return {"success": True, "data": complaints}


@router.post("/", status_code=201)
def create_complaint(complaint: ComplaintCreate, user: dict = Depends(get_current_user)):
    collection = db.get_collection("complaints")
    now = datetime.now(timezone.utc).isoformat()
    complaint_id = f"JSM-{datetime.now(timezone.utc).year}-{str(uuid.uuid4())[:8].upper()}"

    user_doc = db.get_collection("users").find_one({"email": user["sub"]})
    citizen_name = user_doc.get("name", "Citizen") if user_doc else "Citizen"

    c_dict = complaint.model_dump()
    c_dict.update(
        {
            "grievanceID": complaint_id,
            "id": complaint_id,
            "status": "submitted",
            "email": user["sub"],
            "name": citizen_name,
            "createdAt": now,
            "updatedAt": now,
            "history": [
                {
                    "status": "submitted",
                    "remarks": "Grievance filed by citizen",
                    "timestamp": now,
                }
            ],
        }
    )

    collection.insert_one(c_dict)
    c_dict.pop("_id", None)

    return {"success": True, "data": c_dict}


@router.get("/{id}")
def get_complaint(id: str):
    collection = db.get_collection("complaints")
    complaint = collection.find_one({"id": id}, {"_id": 0})
    if not complaint:
        raise HTTPException(status_code=404, detail="Complaint not found")
    return {"success": True, "data": complaint}


@router.patch("/{id}/status")
def update_status(
    id: str,
    status: str,
    remarks: str = "",
    user: dict = Depends(get_current_user),
):
    allowed_statuses = {"submitted", "under_review", "in_progress", "resolved", "closed"}
    if status not in allowed_statuses:
        raise HTTPException(status_code=400, detail=f"Invalid status. Must be one of: {allowed_statuses}")

    collection = db.get_collection("complaints")
    now = datetime.now(timezone.utc).isoformat()
    result = collection.update_one(
        {"id": id},
        {
            "$set": {"status": status, "updatedAt": now},
            "$push": {"history": {"status": status, "remarks": remarks, "timestamp": now}},
        },
    )
    if result.modified_count == 0:
        raise HTTPException(status_code=404, detail="Complaint not found")
    return {"success": True, "message": f"Updated {id} status to {status}"}


@router.patch("/{id}/feedback")
def submit_feedback(
    id: str,
    rating: int,
    comment: str = "",
    user: dict = Depends(get_current_user),
):
    if not 1 <= rating <= 5:
        raise HTTPException(status_code=400, detail="Rating must be between 1 and 5")

    collection = db.get_collection("complaints")

    # Only allow the complaint owner to submit feedback
    complaint = collection.find_one({"id": id}, {"_id": 0, "email": 1})
    if not complaint:
        raise HTTPException(status_code=404, detail="Complaint not found")
    if complaint["email"] != user["sub"]:
        raise HTTPException(status_code=403, detail="You can only submit feedback on your own complaints")

    now = datetime.now(timezone.utc).isoformat()
    collection.update_one(
        {"id": id},
        {
            "$set": {
                "feedbackRating": rating,
                "feedbackComment": comment,
                "status": "closed",
                "updatedAt": now,
            },
            "$push": {
                "history": {
                    "status": "closed",
                    "remarks": f"Citizen Feedback ({rating}/5): {comment}",
                    "timestamp": now,
                }
            },
        },
    )
    return {"success": True, "message": f"Feedback submitted for {id}"}
