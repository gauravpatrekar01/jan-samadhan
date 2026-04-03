from fastapi import APIRouter, HTTPException, Depends, Header
from schemas.complaint import ComplaintCreate
from db import db
from datetime import datetime
import uuid
from security import decode_token

router = APIRouter()

def get_current_user(authorization: str = Header(None)):
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Unauthorized")
    token = authorization.split(" ")[1]
    payload = decode_token(token)
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid token")
    return payload

@router.get("/")
def get_complaints():
    collection = db.get_collection("complaints")
    complaints = list(collection.find({}, {"_id": 0}))
    return {"success": True, "data": complaints}

@router.get("/my")
def get_my_complaints(user: dict = Depends(get_current_user)):
    collection = db.get_collection("complaints")
    complaints = list(collection.find({"email": user.get("sub")}, {"_id": 0}))
    return {"success": True, "data": complaints}

@router.get("/assigned")
def get_assigned_complaints(user: dict = Depends(get_current_user)):
    collection = db.get_collection("complaints")
    complaints = list(collection.find({}, {"_id": 0}))
    return {"success": True, "data": complaints}

@router.post("/")
def create_complaint(complaint: ComplaintCreate, user: dict = Depends(get_current_user)):
    collection = db.get_collection("complaints")
    
    complaint_id = f"JSM-{datetime.utcnow().year}-{str(uuid.uuid4())[:8].upper()}"
    
    c_dict = complaint.model_dump()
    c_dict["grievanceID"] = complaint_id
    c_dict["id"] = complaint_id  # Frontend expects `id`
    c_dict["status"] = "submitted"
    c_dict["email"] = user.get("sub")
    
    # Retrieve user name
    user_doc = db.get_collection("users").find_one({"email": user.get("sub")})
    c_dict["name"] = user_doc.get("name", "Citizen") if user_doc else "Citizen"
    
    c_dict["createdAt"] = datetime.utcnow().isoformat()
    c_dict["updatedAt"] = datetime.utcnow().isoformat()
    c_dict["history"] = [
        {"status": "submitted", "remarks": "Grievance filed by citizen", "timestamp": datetime.utcnow().isoformat()}
    ]
    
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
