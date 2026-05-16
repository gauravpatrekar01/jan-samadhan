from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks
from typing import List, Optional
from datetime import datetime, timezone
import uuid
from db import db
from schemas.project import ProjectCreate, ProjectUpdate, ExtensionRequest, Milestone, ProjectProgressUpdate
from dependencies import require_officer, require_admin, require_officer_or_admin, get_current_user
from audit import log_audit
from notifications import notify_status_change # Assuming this exists and can be used

router = APIRouter()

# 1. Project Conversion Requests

@router.post("/project-conversion/request")
async def request_project_conversion(
    complaint_id: str,
    reason: str,
    scale: str,
    urgency: str,
    budget: float,
    duration: str,
    department: str,
    deadline: str,
    user: dict = Depends(require_officer)
):
    complaints = db.get_collection("complaints")
    complaint = complaints.find_one({"id": complaint_id})
    if not complaint:
        raise HTTPException(status_code=404, detail="Complaint not found")
    
    update_data = {
        "project_conversion_requested": True,
        "project_conversion_status": "pending",
        "project_conversion_reason": reason,
        "project_conversion_requested_by": user["sub"],
        "project_conversion_requested_at": datetime.now(timezone.utc).isoformat(),
        "project_conversion_details": {
            "scale": scale,
            "urgency": urgency,
            "estimated_budget": budget,
            "estimated_duration": duration,
            "suggested_department": department,
            "estimated_deadline": deadline
        }
    }
    
    complaints.update_one({"id": complaint_id}, {"$set": update_data})
    
    log_audit(
        action="project_conversion_requested",
        actor_email=user["sub"],
        actor_role="officer",
        resource_type="complaint",
        resource_id=complaint_id,
        details=update_data
    )
    
    return {"success": True, "message": "Project conversion request submitted to admin"}

@router.get("/project-conversion/pending")
async def get_pending_conversion_requests(user: dict = Depends(require_admin)):
    complaints = db.get_collection("complaints")
    pending = list(complaints.find({"project_conversion_status": "pending"}, {"_id": 0}))
    return {"success": True, "data": pending}

@router.post("/project-conversion/approve")
async def approve_project_conversion(
    complaint_id: str,
    admin_remarks: str = "",
    user: dict = Depends(require_admin)
):
    complaints = db.get_collection("complaints")
    complaint = complaints.find_one({"id": complaint_id})
    if not complaint:
        raise HTTPException(status_code=404, detail="Complaint not found")
    
    # Update complaint status
    complaints.update_one(
        {"id": complaint_id},
        {
            "$set": {
                "project_conversion_status": "approved",
                "status": "Converted to Government Project"
            }
        }
    )
    
    # Create Project
    project_id = f"PROJ-{uuid.uuid4().hex[:8].upper()}"
    details = complaint.get("project_conversion_details", {})
    
    # Calculate initial deadlines
    now = datetime.now(timezone.utc)
    # Simple duration parsing if needed, but for now we'll just take it as input or use a default
    # Assuming duration is something like "6 months" or "180 days" - for simplicity let's use 180 days default if parsing fails
    expected_completion = now # placeholder
    
    # Use the suggested deadline from conversion details
    suggested_deadline = details.get("estimated_deadline")
    deadline_dt = datetime.fromisoformat(suggested_deadline) if suggested_deadline else now
    
    project_data = {
        "project_id": project_id,
        "title": complaint["title"],
        "description": complaint["description"],
        "category": complaint["category"],
        "originating_complaint_id": complaint_id,
        "linked_complaints": [complaint_id],
        "department": details.get("suggested_department", complaint["category"]),
        "assigned_officer": complaint.get("project_conversion_requested_by"),
        "contractor_name": None,
        "budget": details.get("estimated_budget", 0),
        "status": "Project Approved",
        "progress_percentage": 0,
        "geo_location": complaint.get("location_geo"),
        "start_date": now.isoformat(),
        "expected_completion": deadline_dt.isoformat(),
        "current_deadline": deadline_dt.isoformat(),
        "original_deadline": deadline_dt.isoformat(),
        "total_extensions": 0,
        "delay_status": False,
        "milestones": [],
        "deadline_history": [],
        "progress_updates": [],
        "created_by_admin": user["sub"],
        "createdAt": now.isoformat(),
        "updatedAt": now.isoformat()
    }
    
    db.get_collection("projects").insert_one(project_data)
    complaints.update_one({"id": complaint_id}, {"$set": {"linked_project_id": project_id}})
    
    log_audit(
        action="project_conversion_approved",
        actor_email=user["sub"],
        actor_role="admin",
        resource_type="project",
        resource_id=project_id,
        details={"complaint_id": complaint_id, "remarks": admin_remarks}
    )
    
    return {"success": True, "project_id": project_id}

@router.post("/project-conversion/reject")
async def reject_project_conversion(
    complaint_id: str,
    reason: str,
    user: dict = Depends(require_admin)
):
    complaints = db.get_collection("complaints")
    complaints.update_one(
        {"id": complaint_id},
        {
            "$set": {
                "project_conversion_status": "rejected",
                "project_conversion_rejection_reason": reason
            }
        }
    )
    return {"success": True, "message": "Project conversion request rejected"}

# 2. Project Management

@router.get("/")
async def get_projects():
    projects = []
    for doc in db.get_collection("projects").find({}):
        doc["_id"] = str(doc["_id"])
        # Ensure dates are ISO strings
        for date_field in ["current_deadline", "original_deadline", "expected_completion", "start_date", "updatedAt"]:
            if date_field in doc and isinstance(doc[date_field], datetime):
                doc[date_field] = doc[date_field].isoformat()
        projects.append(doc)
    return {"success": True, "data": projects}

@router.get("/pending-extensions")
async def get_pending_extensions(user: dict = Depends(require_admin)):
    extensions = []
    projects_col = db.get_collection("projects")
    for doc in db.get_collection("extension_requests").find({"status": "pending"}):
        doc["_id"] = str(doc["_id"])
        
        # Ensure new_deadline is ISO string
        if isinstance(doc.get("new_deadline"), datetime):
            doc["new_deadline"] = doc["new_deadline"].isoformat()
            
        # Fetch current deadline from project
        proj = projects_col.find_one({"project_id": doc["project_id"]}, {"current_deadline": 1})
        if proj and isinstance(proj.get("current_deadline"), datetime):
             doc["current_deadline"] = proj["current_deadline"].isoformat()
        else:
             doc["current_deadline"] = proj.get("current_deadline", "N/A") if proj else "N/A"
             
        extensions.append(doc)
    return {"success": True, "data": extensions}

@router.get("/{project_id}")
async def get_project(project_id: str):
    project = db.get_collection("projects").find_one({"project_id": project_id})
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    project["_id"] = str(project["_id"])
    for date_field in ["current_deadline", "original_deadline", "expected_completion", "start_date", "updatedAt"]:
        if date_field in project and isinstance(project[date_field], datetime):
            project[date_field] = project[date_field].isoformat()
            
    return {"success": True, "data": project}

@router.put("/{project_id}/update")
async def update_project(
    project_id: str,
    update_data: ProjectUpdate,
    user: dict = Depends(require_officer_or_admin)
):
    projects = db.get_collection("projects")
    project = projects.find_one({"project_id": project_id})
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    update_dict = update_data.model_dump(exclude_unset=True)
    update_dict["updatedAt"] = datetime.now(timezone.utc).isoformat()
    
    # If progress or status is being updated, log it in history
    if "progress_percentage" in update_dict or "status" in update_dict:
        history_entry = {
            "update_title": f"Status changed to {update_dict.get('status', project['status'])}",
            "description": update_dict.get("update_remarks", "System update"),
            "progress_increment": update_dict.get("progress_percentage", project["progress_percentage"]),
            "officer_name": user.get("sub", "Officer"),
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        projects.update_one(
            {"project_id": project_id}, 
            {"$push": {"progress_updates": history_entry}}
        )
    
    # Remove update_remarks from $set as it's not a field in the project document
    update_dict.pop("update_remarks", None)
    
    projects.update_one({"project_id": project_id}, {"$set": update_dict})
    
    return {"success": True, "message": "Project updated successfully"}

@router.post("/milestone")
async def add_milestone(
    project_id: str,
    milestone: Milestone,
    user: dict = Depends(require_officer_or_admin)
):
    projects = db.get_collection("projects")
    result = projects.update_one(
        {"project_id": project_id},
        {"$push": {"milestones": milestone.model_dump()}}
    )
    if result.modified_count == 0:
        raise HTTPException(status_code=404, detail="Project not found")
    return {"success": True, "message": "Milestone added"}

@router.post("/progress-update")
async def add_progress_update(
    update: ProjectProgressUpdate,
    user: dict = Depends(require_officer)
):
    projects = db.get_collection("projects")
    project = projects.find_one({"project_id": update.project_id})
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    new_progress = min(100, project.get("progress_percentage", 0) + update.progress_increment)
    
    projects.update_one(
        {"project_id": update.project_id},
        {
            "$set": {"progress_percentage": new_progress, "updatedAt": datetime.now(timezone.utc).isoformat()},
            "$push": {"progress_updates": update.model_dump()}
        }
    )
    
    return {"success": True, "new_progress": new_progress}

# 3. Deadline Extensions

@router.post("/request-extension")
async def request_deadline_extension(
    request: ExtensionRequest,
    user: dict = Depends(require_officer)
):
    projects = db.get_collection("projects")
    project = projects.find_one({"project_id": request.project_id})
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    extension_request = request.model_dump()
    extension_request["status"] = "pending"
    extension_request["requested_by"] = user["sub"]
    extension_request["requested_at"] = datetime.now(timezone.utc).isoformat()
    
    db.get_collection("extension_requests").insert_one(extension_request)
    
    return {"success": True, "message": "Extension request submitted"}


@router.post("/approve-extension")
async def approve_extension(
    request_id: str, # MongoDB _id or a custom ID
    user: dict = Depends(require_admin)
):
    # For simplicity, using project_id in this demo if we don't have a specific request_id
    # But let's assume we fetch the request by its MongoDB ID (as string)
    from bson import ObjectId
    ext_col = db.get_collection("extension_requests")
    req = ext_col.find_one({"_id": ObjectId(request_id)})
    if not req:
        raise HTTPException(status_code=404, detail="Extension request not found")
    
    project_id = req["project_id"]
    new_deadline = req["new_deadline"]
    
    projects = db.get_collection("projects")
    project = projects.find_one({"project_id": project_id})
    
    history_entry = {
        "previous_deadline": project["current_deadline"],
        "new_deadline": new_deadline,
        "reason": req["reason"],
        "requested_by": req["requested_by"],
        "approved_by": user["sub"],
        "approved_at": datetime.now(timezone.utc).isoformat()
    }
    
    projects.update_one(
        {"project_id": project_id},
        {
            "$set": {
                "current_deadline": new_deadline,
                "delay_status": True,
                "last_extension_reason": req["reason"],
                "last_extended_by": user["sub"],
                "last_extended_at": datetime.now(timezone.utc).isoformat()
            },
            "$inc": {"total_extensions": 1},
            "$push": {"deadline_history": history_entry}
        }
    )
    
    ext_col.update_one({"_id": ObjectId(request_id)}, {"$set": {"status": "approved"}})
    
    return {"success": True, "message": "Deadline extension approved"}

@router.post("/reject-extension")
async def reject_extension(
    request_id: str,
    reason: str,
    user: dict = Depends(require_admin)
):
    from bson import ObjectId
    db.get_collection("extension_requests").update_one(
        {"_id": ObjectId(request_id)},
        {"$set": {"status": "rejected", "rejection_reason": reason}}
    )
    return {"success": True, "message": "Extension request rejected"}

@router.get("/extension-history/{project_id}")
async def get_extension_history(project_id: str, user: dict = Depends(get_current_user)):
    project = db.get_collection("projects").find_one({"project_id": project_id}, {"deadline_history": 1, "_id": 0})
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return {"success": True, "data": project.get("deadline_history", [])}
