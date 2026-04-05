"""
Audit logging for officer and admin actions.
"""

from datetime import datetime, timezone
from db import db
from typing import Optional


def log_audit(
    action: str,
    actor_email: str,
    actor_role: str,
    resource_type: str,
    resource_id: str,
    details: Optional[dict] = None,
    status: str = "success",
):
    """
    Log an admin or officer action to the audit log.

    Args:
        action: e.g., 'complaint_assigned', 'status_updated', 'user_verified'
        actor_email: Email of the user performing the action
        actor_role: Role of the user (officer, admin)
        resource_type: Type of resource (complaint, user, notice)
        resource_id: ID of the resource
        details: Additional context (optional)
        status: 'success' or 'failed'
    """
    collection = db.get_collection("audit_log")
    audit_entry = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "action": action,
        "actor_email": actor_email,
        "actor_role": actor_role,
        "resource_type": resource_type,
        "resource_id": resource_id,
        "details": details or {},
        "status": status,
    }
    collection.insert_one(audit_entry)


def get_audit_log(
    actor_email: Optional[str] = None,
    action: Optional[str] = None,
    limit: int = 100,
):
    """
    Retrieve audit log entries (admin-only).

    Args:
        actor_email: Filter by actor email
        action: Filter by action type
        limit: Maximum number of entries to return
    """
    collection = db.get_collection("audit_log")
    query = {}
    if actor_email:
        query["actor_email"] = actor_email
    if action:
        query["action"] = action

    entries = list(
        collection.find(query, {"_id": 0})
        .sort("timestamp", -1)
        .limit(limit)
    )
    return entries
