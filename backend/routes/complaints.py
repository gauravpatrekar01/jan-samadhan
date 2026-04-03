from fastapi import APIRouter
from schemas.complaint import ComplaintCreate

router = APIRouter()

@router.get("/")
def get_complaints():
    return {"success": True, "data": []}

@router.post("/")
def create_complaint(complaint: ComplaintCreate):
    return {"success": True, "data": {"message": "Complaint created stub"}}

@router.patch("/{id}/status")
def update_status(id: str, status: str):
    return {"success": True, "message": f"Updated status of {id} to {status}"}
