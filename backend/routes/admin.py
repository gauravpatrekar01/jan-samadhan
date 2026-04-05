from fastapi import APIRouter, Depends, HTTPException, Header
from schemas.user import UserCreate
from db import db
from security import decode_token, hash_password
from datetime import datetime, timezone
from government_registry import verify_citizen_record
import uuid

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


@router.post("/users", status_code=201)
def create_user(user: UserCreate, admin: dict = Depends(require_admin)):
    if user.role not in {"officer", "admin"}:
        raise HTTPException(status_code=400, detail="Admin may only create officer or admin accounts")

    collection = db.get_collection("users")
    if collection.find_one({"email": user.email}):
        raise HTTPException(status_code=400, detail="User already exists")

    user_dict = user.model_dump()
    user_dict["password"] = hash_password(user.password)
    user_dict["createdAt"] = datetime.now(timezone.utc).isoformat()
    user_dict["verified"] = True

    collection.insert_one(user_dict)
    user_dict.pop("_id", None)
    user_dict.pop("password", None)
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
        raise HTTPException(status_code=404, detail="User not found")
    new_status = not user.get("verified", False)
    collection.update_one({"email": email}, {"$set": {"verified": new_status}})
    return {"success": True, "message": f"User {'verified' if new_status else 'unverified'}", "verified": new_status}


@router.post("/users/{email}/verify-government")
def verify_user_government(email: str, admin: dict = Depends(require_admin)):
    collection = db.get_collection("users")
    user = collection.find_one({"email": email})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if user.get("role") != "citizen":
        raise HTTPException(status_code=400, detail="Government verification only applies to citizen accounts")
    if not user.get("aadhar"):
        raise HTTPException(status_code=400, detail="Aadhar number is required for government verification")

    if not verify_citizen_record(user.get("name"), user.get("email"), user.get("aadhar")):
        raise HTTPException(status_code=400, detail="No matching government record found")

    collection.update_one({"email": email}, {"$set": {"verified": True}})
    return {"success": True, "message": "Citizen verified against government records"}


@router.get("/analytics")
def get_analytics(admin: dict = Depends(require_admin)):
    collection = db.get_collection("complaints")
    complaints = list(collection.find({}, {"_id": 0, "status": 1, "priority": 1, "region": 1}))

    total = len(complaints)
    resolved = sum(1 for c in complaints if c.get("status") in {"resolved", "closed"})
    resolution_rate = round((resolved / total * 100), 1) if total > 0 else 0

    status_dist = {"submitted": 0, "under_review": 0, "in_progress": 0, "resolved": 0, "closed": 0}
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
            "status_distribution": status_dist,
            "priority_distribution": priority_dist,
            "byRegion": regions,
        },
    }


@router.post("/notices", status_code=201)
def add_notice(notice: dict, admin: dict = Depends(require_admin)):
    if not notice.get("text", "").strip():
        raise HTTPException(status_code=400, detail="Notice text is required")
    collection = db.get_collection("announcements")
    notice["id"] = str(uuid.uuid4())
    notice["date"] = datetime.now(timezone.utc).isoformat().split("T")[0]
    notice["createdBy"] = admin["sub"]
    collection.insert_one(notice)
    notice.pop("_id", None)
    return {"success": True, "message": "Notice added", "data": notice}


@router.get("/notices")
def get_notices():
    # Public — citizens can see announcements
    collection = db.get_collection("announcements")
    notices = list(collection.find({}, {"_id": 0}))
    return {"success": True, "data": notices}


@router.delete("/notices/{notice_id}")
def delete_notice(notice_id: str, admin: dict = Depends(require_admin)):
    collection = db.get_collection("announcements")
    result = collection.delete_one({"id": notice_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Notice not found")
    return {"success": True, "message": "Notice deleted"}
