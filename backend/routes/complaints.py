from fastapi import APIRouter, HTTPException
from schemas.complaint import ComplaintCreate
from db import db
from datetime import datetime
import uuid

router = APIRouter()

@router.get("/")
def get_complaints():
    collection = db.get_collection("complaints")
    complaints = list(collection.find({}, {"_id": 0}))
    return {"success": True, "data": complaints}

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
def update_status(id: str, status: str, remarks: str = ""):
    collection = db.get_collection("complaints")
    update_data = {
        "$set": {"status": status, "updatedAt": datetime.utcnow().isoformat()},
        "$push": {"history": {"status": status, "remarks": remarks, "timestamp": datetime.utcnow().isoformat()}}
    }
    result = collection.update_one({"id": id}, update_data)
    if result.modified_count == 0:
        raise HTTPException(status_code=404, detail="Complaint not found")
    return {"success": True, "message": f"Updated {id} status to {status}"}

@router.patch("/{id}/feedback")
def submit_feedback(id: str, rating: int, comment: str = ""):
    collection = db.get_collection("complaints")
    update_data = {
        "$set": {"feedbackRating": rating, "feedbackComment": comment, "status": "closed", "updatedAt": datetime.utcnow().isoformat()},
        "$push": {"history": {"status": "closed", "remarks": f"Citizen Feedback ({rating} Stars): {comment}", "timestamp": datetime.utcnow().isoformat()}}
    }
    result = collection.update_one({"id": id}, update_data)
    if result.modified_count == 0:
        raise HTTPException(status_code=404, detail="Complaint not found")
    return {"success": True, "message": f"Feedback submitted for {id}"}
