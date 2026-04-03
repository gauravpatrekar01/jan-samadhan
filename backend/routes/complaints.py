from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from schemas.complaint import ComplaintCreate
from db import db
from datetime import datetime
import uuid

router = APIRouter()

class StatusUpdate(BaseModel):
    status: str
    remarks: str = ""

class FeedbackUpdate(BaseModel):
    rating: int
    comment: str = ""

@router.get("/")
def get_complaints():
    collection = db.get_collection("complaints")
    complaints = list(collection.find({}, {"_id": 0}))
    return {"success": True, "data": complaints}

@router.get("/my")
def get_my_complaints():
    # In a real app this would filter by JWT token user
    # For now we'll just return all as a mock or filter locally in frontend
    collection = db.get_collection("complaints")
    complaints = list(collection.find({}, {"_id": 0}))
    return {"success": True, "data": complaints}

@router.get("/assigned")
def get_assigned_complaints():
    # Same as above, mock for officer
    collection = db.get_collection("complaints")
    complaints = list(collection.find({}, {"_id": 0}))
    return {"success": True, "data": complaints}

@router.get("/{id}")
def get_complaint(id: str):
    collection = db.get_collection("complaints")
    c = collection.find_one({"$or": [{"id": id}, {"grievanceID": id}]}, {"_id": 0})
    if not c:
        raise HTTPException(status_code=404, detail="Complaint not found")
    return {"success": True, "data": c}

@router.post("/")
def create_complaint(complaint: ComplaintCreate):
    collection = db.get_collection("complaints")
    
    complaint_id = f"JSM-{datetime.utcnow().year}-{str(uuid.uuid4())[:8].upper()}"
    
    c_dict = complaint.model_dump()
    c_dict["grievanceID"] = complaint_id
    c_dict["id"] = complaint_id  # Frontend expects `id`
    c_dict["status"] = "submitted"
    c_dict["createdAt"] = datetime.utcnow().isoformat()
    c_dict["updatedAt"] = datetime.utcnow().isoformat()
    c_dict["history"] = [
        {"status": "submitted", "remarks": "Grievance filed by citizen", "timestamp": datetime.utcnow().isoformat()}
    ]
    
    collection.insert_one(c_dict)
    c_dict.pop("_id", None)
    
    return {"success": True, "data": c_dict}

@router.patch("/{id}/status")
def update_status(id: str, payload: StatusUpdate):
    collection = db.get_collection("complaints")
    update_data = {
        "$set": {"status": payload.status, "updatedAt": datetime.utcnow().isoformat()},
        "$push": {"history": {"status": payload.status, "remarks": payload.remarks, "timestamp": datetime.utcnow().isoformat()}}
    }
    result = collection.update_one({"$or": [{"id": id}, {"grievanceID": id}]}, update_data)
    if result.modified_count == 0:
        raise HTTPException(status_code=404, detail="Complaint not found")
    return {"success": True, "message": f"Updated {id} status to {payload.status}"}

@router.patch("/{id}/feedback")
def submit_feedback(id: str, payload: FeedbackUpdate):
    collection = db.get_collection("complaints")
    update_data = {
        "$set": {"feedbackRating": payload.rating, "feedbackComment": payload.comment, "status": "closed", "updatedAt": datetime.utcnow().isoformat()},
        "$push": {"history": {"status": "closed", "remarks": f"Citizen Feedback ({payload.rating} Stars): {payload.comment}", "timestamp": datetime.utcnow().isoformat()}}
    }
    result = collection.update_one({"$or": [{"id": id}, {"grievanceID": id}]}, update_data)
    if result.modified_count == 0:
        raise HTTPException(status_code=404, detail="Complaint not found")
    return {"success": True, "message": f"Feedback submitted for {id}"}
