from fastapi import APIRouter, Depends, Query
from schemas.complaint import ComplaintCreate
from db import db
from datetime import datetime, timezone
import uuid
from dependencies import (
    require_citizen,
    require_officer,
    require_officer_or_admin,
    get_current_user,
)
from errors import ValidationError, NotFoundError, AuthorizationError
from audit import log_audit
from search import search_complaints, get_complaint_count

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
        skip=skip,
        limit=limit,
    )

    # Count should match the same logic
    total = get_complaint_count(
        status=status,
        priority=priority,
        category=category,
        region=region,
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


@router.post("/", status_code=201)
def create_complaint(complaint: ComplaintCreate, user: dict = Depends(require_citizen)):
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
            "citizen_email": user["sub"],
            "email": user["sub"],  # For backward compatibility
            "name": citizen_name,
            "assigned_officer": None,
            "createdAt": now,
            "updatedAt": now,
            "history": [
                {
                    "status": "submitted",
                    "remarks": "Grievance filed by citizen",
                    "timestamp": now,
                }
            ],
            "feedback": [],
            "feedbackAverage": 0,
            "feedbackCount": 0,
        }
    )

    # Auto-assign complaints to the officer responsible for the district
    assigned_officer = find_officer_for_region(c_dict.get("region"))
    if assigned_officer:
        c_dict["assigned_officer"] = assigned_officer
        c_dict["history"].append(
            {
                "status": "submitted",
                "remarks": f"Auto-assigned to officer {assigned_officer} for district {c_dict.get('region')}",
                "timestamp": now,
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

    return {"success": True, "data": c_dict}


@router.get("/{id}")
def get_complaint(id: str, user: dict = Depends(get_current_user)):
    collection = db.get_collection("complaints")
    complaint = collection.find_one({"id": id}, {"_id": 0})
    if not complaint:
        raise NotFoundError("Complaint")

    if user.get("role") == "citizen":
        if complaint.get("citizen_email") != user["sub"]:
            # Public feed complaints should remain viewable, but hide private identifiers.
            complaint = {k: v for k, v in complaint.items() if k not in {"citizen_email", "email"}}

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
                "history": {
                    "status": "assigned",
                    "remarks": f"Assigned to officer {officer_email}",
                    "timestamp": now,
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


@router.patch("/{id}/status")
def update_status(
    id: str,
    status: str,
    remarks: str = "",
    user: dict = Depends(require_officer_or_admin),
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

    now = datetime.now(timezone.utc).isoformat()
    
    # Auto-assign emergency complaints to the officer updating them
    update_fields = {"status": status, "updatedAt": now}
    if user.get("role") == "officer" and complaint.get("priority", "").lower() == "emergency":
        if complaint.get("assigned_officer") != user["sub"]:
            update_fields["assigned_officer"] = user["sub"]
            remarks = f"[AUTO-ASSIGNED] {remarks}" if remarks else "Emergency complaint auto-assigned to responding officer"
    
    collection.update_one(
        {"id": id},
        {
            "$set": update_fields,
            "$push": {
                "history": {
                    "status": status,
                    "remarks": remarks,
                    "timestamp": now,
                    "updated_by": user["sub"],
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

    return {"success": True, "message": f"Updated {id} status to {status}"}


@router.patch("/{id}/feedback")
def submit_feedback(
    id: str,
    rating: int,
    comment: str = "",
    user: dict = Depends(require_citizen),
):
    if not 1 <= rating <= 5:
        raise ValidationError("Rating must be between 1 and 5")

    collection = db.get_collection("complaints")
    complaint = collection.find_one({"id": id}, {"_id": 0, "status": 1, "feedback": 1, "feedbackAverage": 1, "feedbackCount": 1})
    if not complaint:
        raise NotFoundError("Complaint")

    if complaint.get("status") not in {"resolved", "closed"}:
        raise ValidationError("Only resolved or closed complaints can be rated")

    feedback_entries = complaint.get("feedback") or []
    if any(entry.get("user_email") == user["sub"] for entry in feedback_entries):
        raise ValidationError("You have already rated this complaint")

    now = datetime.now(timezone.utc).isoformat()
    total_count = len(feedback_entries) + 1
    total_sum = sum(entry.get("rating", 0) for entry in feedback_entries) + rating
    average = round(total_sum / total_count, 2)

    collection.update_one(
        {"id": id},
        {
            "$push": {
                "feedback": {
                    "user_email": user["sub"],
                    "rating": rating,
                    "comment": comment,
                    "timestamp": now,
                },
                "history": {
                    "status": "closed",
                    "remarks": f"Citizen Feedback ({rating}/5): {comment}",
                    "timestamp": now,
                }
            },
            "$set": {
                "status": "closed",
                "updatedAt": now,
                "feedbackAverage": average,
                "feedbackCount": total_count,
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
