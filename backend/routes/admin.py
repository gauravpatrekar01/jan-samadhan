from fastapi import APIRouter, Depends
from schemas.user import UserCreate
from db import db
from security import hash_password
from dependencies import require_admin, require_officer_or_admin
from datetime import datetime, timezone
from government_registry import verify_citizen_record
from audit import log_audit, get_audit_log
from errors import ValidationError, NotFoundError, ConflictError, AuthorizationError
import uuid

router = APIRouter()


@router.post("/users", status_code=201)
def create_user(user: UserCreate, admin: dict = Depends(require_admin)):
    if user.role not in {"officer", "admin", "ngo"}:
        raise ValidationError("Admin may only create officer, admin, or NGO accounts")

    if user.role == "officer" and not user.district:
        raise ValidationError("Officer district is required")

    collection = db.get_collection("users")
    if collection.find_one({"email": user.email}):
        raise ConflictError("User already exists")

    user_dict = user.model_dump()
    user_dict["password"] = hash_password(user.password)
    if user.role == "officer":
        user_dict["district"] = user.district
    user_dict["createdAt"] = datetime.now(timezone.utc).isoformat()
    user_dict["verified"] = True

    collection.insert_one(user_dict)
    user_dict.pop("_id", None)
    user_dict.pop("password", None)

    log_audit(
        action="user_created",
        actor_email=admin["sub"],
        actor_role=admin["role"],
        resource_type="user",
        resource_id=user.email,
        details={"name": user.name, "role": user.role},
    )

    return {"success": True, "data": user_dict}


@router.get("/users")
def get_users(admin: dict = Depends(require_admin)):
    collection = db.get_collection("users")
    users = list(collection.find({}, {"_id": 0, "password": 0}))
    return {"success": True, "data": users}


@router.patch("/users/{email}/verify")
def verify_user(email: str, admin: dict = Depends(require_admin)):
    collection = db.get_collection("users")
    user = collection.find_one({"email": email})
    if not user:
        raise NotFoundError("User")

    new_status = not user.get("verified", False)
    collection.update_one({"email": email}, {"$set": {"verified": new_status}})

    log_audit(
        action="user_verified",
        actor_email=admin["sub"],
        actor_role=admin["role"],
        resource_type="user",
        resource_id=email,
        details={"verified": new_status},
    )

    return {
        "success": True,
        "message": f"User {'verified' if new_status else 'unverified'}",
        "verified": new_status,
    }


@router.post("/users/{email}/verify-government")
def verify_user_government(email: str, admin: dict = Depends(require_admin)):
    collection = db.get_collection("users")
    user = collection.find_one({"email": email})
    if not user:
        raise NotFoundError("User")

    if user.get("role") != "citizen":
        raise ValidationError("Government verification only applies to citizen accounts")

    if not user.get("aadhar"):
        raise ValidationError("Aadhar number is required for government verification")

    if not verify_citizen_record(
        user.get("name"), user.get("email"), user.get("aadhar")
    ):
        raise ValidationError("No matching government record found")

    collection.update_one({"email": email}, {"$set": {"verified": True}})

    log_audit(
        action="citizen_verified_government",
        actor_email=admin["sub"],
        actor_role=admin["role"],
        resource_type="user",
        resource_id=email,
        details={"method": "government_record"},
    )

    return {"success": True, "message": "Citizen verified against government records"}


@router.get("/analytics")
def get_analytics(admin: dict = Depends(require_admin)):
    collection = db.get_collection("complaints")
    complaints = list(collection.find({}, {"_id": 0, "status": 1, "priority": 1, "region": 1, "sla_deadline": 1, "feedback": 1, "feedbackAverage": 1, "feedbackCount": 1}))

    total = len(complaints)
    resolved = sum(1 for c in complaints if c.get("status") in {"resolved", "closed"})
    resolution_rate = round((resolved / total * 100), 1) if total > 0 else 0

    # Calculate satisfaction rating
    total_ratings = 0
    total_rating_sum = 0
    rated_complaints = 0
    for c in complaints:
        count = c.get("feedbackCount") if c.get("feedbackCount") is not None else len(c.get("feedback", []) or [])
        if count > 0:
            rated_complaints += 1
            if c.get("feedbackAverage") is not None:
                total_rating_sum += c.get("feedbackAverage", 0) * count
            else:
                total_rating_sum += sum(item.get("rating", 0) for item in (c.get("feedback") or []))
            total_ratings += count

    average_satisfaction = round((total_rating_sum / total_ratings), 2) if total_ratings > 0 else 0

    status_dist = {
        "submitted": 0,
        "under_review": 0,
        "in_progress": 0,
        "resolved": 0,
        "closed": 0,
    }
    priority_dist = {"emergency": 0, "high": 0, "medium": 0, "low": 0}
    regions: dict[str, int] = {}

    for c in complaints:
        status = c.get("status", "submitted").lower()
        if status in status_dist:
            status_dist[status] += 1

        priority = c.get("priority", "medium").lower()
        if priority in priority_dist:
            priority_dist[priority] += 1

        r = c.get("region")
        if r:
            regions[r] = regions.get(r, 0) + 1

    return {
        "success": True,
        "data": {
            "total_complaints": total,
            "resolved_complaints": resolved,
            "resolution_rate": resolution_rate,
            "average_satisfaction": average_satisfaction,
            "rated_complaints": rated_complaints,
            "status_distribution": status_dist,
            "priority_distribution": priority_dist,
            "byRegion": regions,
        },
    }


@router.post("/notices", status_code=201)
def add_notice(notice: dict, user: dict = Depends(require_officer_or_admin)):
    """Officers and admins can add notices"""
    if not notice.get("text", "").strip():
        raise ValidationError("Notice text is required")

    collection = db.get_collection("announcements")
    notice_doc = {
        "id": str(uuid.uuid4()),
        "text": notice.get("text"),
        "date": datetime.now(timezone.utc).isoformat().split("T")[0],
        "createdBy": user["sub"],
        "createdByRole": user["role"],
        "pinned": notice.get("pinned", False),
    }
    collection.insert_one(notice_doc)

    log_audit(
        action="notice_created",
        actor_email=user["sub"],
        actor_role=user["role"],
        resource_type="notice",
        resource_id=notice_doc["id"],
        details={"text": notice.get("text")[:100]},
    )

    notice_doc.pop("_id", None)
    return {"success": True, "message": "Notice added", "data": notice_doc}


@router.get("/notices")
def get_notices():
    # Public — citizens can see announcements
    collection = db.get_collection("announcements")
    notices = list(collection.find({}, {"_id": 0}).sort("date", -1))
    return {"success": True, "data": notices}


@router.delete("/notices/{notice_id}")
def delete_notice(notice_id: str, user: dict = Depends(require_officer_or_admin)):
    """Admins can delete any notice, officers can only delete their own"""
    collection = db.get_collection("announcements")
    notice = collection.find_one({"id": notice_id})
    
    if not notice:
        raise NotFoundError("Notice")
    
    # Officers can only delete their own notices; admins can delete any
    if user["role"] == "officer" and notice.get("createdBy") != user["sub"]:
        raise AuthorizationError("You can only delete notices you created")

    result = collection.delete_one({"id": notice_id})
    if result.deleted_count == 0:
        raise NotFoundError("Notice")

    log_audit(
        action="notice_deleted",
        actor_email=user["sub"],
        actor_role=user["role"],
        resource_type="notice",
        resource_id=notice_id,
    )

    return {"success": True, "message": "Notice deleted"}


@router.get("/audit-log")
def fetch_audit_log(
    actor_email: str = None,
    action: str = None,
    limit: int = 100,
    admin: dict = Depends(require_admin),
):
    """Retrieve admin/officer audit log"""
    entries = get_audit_log(actor_email=actor_email, action=action, limit=limit)
    return {"success": True, "data": entries}


# ── NGO Request Management ──
@router.get("/ngo-requests")
def get_all_ngo_requests(status: str = "pending", admin: dict = Depends(require_admin)):
    """Admin views all pending NGO requests."""
    collection = db.get_collection("ngo_requests")
    requests = list(collection.find({"status": status}, {"_id": 0}).sort("requested_at", -1))
    return {"success": True, "data": requests}

@router.patch("/ngo-requests/{request_id}/approve")
def approve_ngo_request(request_id: str, admin: dict = Depends(require_admin)):
    """Approve an NGO request and assign the grievance."""
    req_coll = db.get_collection("ngo_requests")
    complaint_coll = db.get_collection("complaints")
    
    req = req_coll.find_one({"id": request_id})
    if not req:
        raise NotFoundError("NGO Request")
    
    if req["status"] != "pending":
        raise ValidationError(f"Request is already {req['status']}")

    complaint_id = req["complaint_id"]
    now = datetime.now(timezone.utc).isoformat()
    
    # Verify complaint status and current assignment
    complaint = complaint_coll.find_one({"id": complaint_id})
    if not complaint:
         raise NotFoundError("Complaint")
    if complaint.get("assigned_to_ngo"):
         raise ValidationError("Grievance is already assigned to another NGO")

    # Update Complaint: Assign NGO, change status, add timeline
    timeline_event = {
        "status": "In Progress",
        "remarks": f"Grievance assigned to NGO: {req['ngo_name']}. Handled by social partner.",
        "timestamp": now,
        "updated_by": "admin"
    }

    complaint_coll.update_one(
        {"id": complaint_id},
        {
            "$set": {
                "assigned_to_ngo": req["ngo_email"],
                "status": "in_progress",
                "updatedAt": now
            },
            "$push": {"history": timeline_event}
        }
    )

    # Update request status
    req_coll.update_one({"id": request_id}, {"$set": {"status": "approved", "processed_at": now}})

    # Reject other pending requests for this same complaint
    req_coll.update_many(
        {"complaint_id": complaint_id, "status": "pending", "id": {"$ne": request_id}},
        {"$set": {
            "status": "rejected", 
            "admin_remarks": "Another NGO was assigned to this case.", 
            "processed_at": now
        }}
    )

    log_audit("ngo_request_approved", admin["sub"], admin["role"], "ngo_request", request_id)
    return {"success": True, "message": "NGO assigned successfully"}

@router.patch("/ngo-requests/{request_id}/reject")
def reject_ngo_request(request_id: str, remarks: str = "Request declined.", admin: dict = Depends(require_admin)):
    """Reject an NGO's request to handle a grievance."""
    req_coll = db.get_collection("ngo_requests")
    req = req_coll.find_one({"id": request_id})
    if not req:
        raise NotFoundError("NGO Request")
        
    req_coll.update_one({"id": request_id}, {
        "$set": {
            "status": "rejected", 
            "admin_remarks": remarks, 
            "processed_at": datetime.now(timezone.utc).isoformat()
        }
    })
    
    return {"success": True, "message": "NGO request rejected"}

