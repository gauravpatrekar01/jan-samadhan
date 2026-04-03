from fastapi import APIRouter
from db import db

router = APIRouter()

@router.get("/users")
def get_users():
    collection = db.get_collection("users")
    users = list(collection.find({}, {"_id": 0, "password": 0}))
    return {"success": True, "data": users}

@router.get("/analytics")
def get_analytics():
    collection = db.get_collection("complaints")
    complaints = list(collection.find({}))
    
    total = len(complaints)
    resolved = sum(1 for c in complaints if c.get("status") in ["resolved", "closed"])
    resolution_rate = round((resolved / total * 100)) if total > 0 else 0
    
    status_dist = {
        "submitted": 0,
        "under_review": 0,
        "in_progress": 0,
        "resolved": 0,
        "closed": 0
    }
    
    priority_dist = {
        "emergency": 0,
        "high": 0,
        "medium": 0,
        "low": 0
    }
    
    for c in complaints:
        status = c.get("status", "submitted").lower()
        if status in status_dist:
            status_dist[status] += 1
            
        priority = c.get("priority", "medium").lower()
        if priority in priority_dist:
            priority_dist[priority] += 1
            
    # Also support region for the map if needed
    regions = {}
    for c in complaints:
        r = c.get("region")
        if r:
            regions[r] = regions.get(r, 0) + 1
            
    stats = {
        "total_complaints": total,
        "resolved_complaints": resolved,
        "resolution_rate": resolution_rate,
        "status_distribution": status_dist,
        "priority_distribution": priority_dist,
        "byRegion": regions
    }
    
    return {"success": True, "data": stats}
