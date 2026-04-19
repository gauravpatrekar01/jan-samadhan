"""
Search and filtering utilities for complaints.
"""

from typing import Optional, List, Dict, Any
from db import db


def build_complaint_query(
    status: Optional[str] = None,
    priority: Optional[str] = None,
    category: Optional[str] = None,
    region: Optional[str] = None,
    search: Optional[str] = None,
    assigned_to: Optional[str] = None,
    citizen_email: Optional[str] = None,
    near: Optional[str] = None,
    radius: int = 5000,
) -> Dict[str, Any]:
    """Build a MongoDB query for complaint filtering"""
    query = {}

    if near:
        try:
            lat, lng = map(float, near.split(","))
            query["location"] = {
                "$near": {
                    "$geometry": {
                        "type": "Point",
                        "coordinates": [lng, lat]
                    },
                    "$maxDistance": radius
                }
            }
        except ValueError:
            pass

    if status:
        query["status"] = status.lower()

    if priority:
        query["priority"] = priority.lower()

    if category:
        query["category"] = category

    if region:
        query["region"] = region

    if assigned_to:
        query["assigned_officer"] = assigned_to

    if citizen_email:
        query["citizen_email"] = citizen_email

    if search:
        # Full-text search across description and grievanceID
        query["$or"] = [
            {"description": {"$regex": search, "$options": "i"}},
            {"grievanceID": {"$regex": search, "$options": "i"}},
            {"category": {"$regex": search, "$options": "i"}},
        ]

    return query


def search_complaints(
    status: Optional[str] = None,
    priority: Optional[str] = None,
    category: Optional[str] = None,
    region: Optional[str] = None,
    search: Optional[str] = None,
    assigned_to: Optional[str] = None,
    citizen_email: Optional[str] = None,
    near: Optional[str] = None,
    radius: int = 5000,
    skip: int = 0,
    limit: int = 50,
) -> List[Dict[str, Any]]:
    """Search complaints with pagination"""
    query = build_complaint_query(
        status=status,
        priority=priority,
        category=category,
        region=region,
        search=search,
        assigned_to=assigned_to,
        citizen_email=citizen_email,
        near=near,
        radius=radius,
    )

    collection = db.get_collection("complaints")
    complaints = list(
        collection.find(query, {"_id": 0})
        .sort("timestamp", -1)
        .skip(skip)
        .limit(limit)
    )
    return complaints


def get_complaint_count(
    status: Optional[str] = None,
    priority: Optional[str] = None,
    category: Optional[str] = None,
    region: Optional[str] = None,
    assigned_to: Optional[str] = None,
    citizen_email: Optional[str] = None,
    near: Optional[str] = None,
    radius: int = 5000,
) -> int:
    """Get count of complaints matching criteria"""
    query = build_complaint_query(
        status=status,
        priority=priority,
        category=category,
        region=region,
        assigned_to=assigned_to,
        citizen_email=citizen_email,
        near=near,
        radius=radius,
    )

    collection = db.get_collection("complaints")
    return collection.count_documents(query)
