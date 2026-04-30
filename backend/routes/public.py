from fastapi import APIRouter, Query
from db import db
from datetime import datetime, timezone, timedelta
from collections import defaultdict
from typing import Optional

router = APIRouter(prefix="/api/public", tags=["public"])

@router.get("/stats")
async def get_public_stats():
    """
    Get public statistics about complaints
    No authentication required, excludes personal data
    """
    try:
        collection = db.get_collection("complaints")
        
        # Total complaints
        total_complaints = collection.count_documents({})
        
        # Status breakdown
        status_pipeline = [
            {"$group": {"_id": "$status", "count": {"$sum": 1}}},
            {"$sort": {"count": -1}}
        ]
        status_breakdown = list(collection.aggregate(status_pipeline))
        
        # Category breakdown
        category_pipeline = [
            {"$group": {"_id": "$category", "count": {"$sum": 1}}},
            {"$sort": {"count": -1}}
        ]
        category_breakdown = list(collection.aggregate(category_pipeline))
        
        # Priority breakdown
        priority_pipeline = [
            {"$group": {"_id": "$priority", "count": {"$sum": 1}}},
            {"$sort": {"count": -1}}
        ]
        priority_breakdown = list(collection.aggregate(priority_pipeline))
        
        # Regional breakdown (top 10)
        region_pipeline = [
            {"$group": {"_id": "$region", "count": {"$sum": 1}}},
            {"$sort": {"count": -1}},
            {"$limit": 10}
        ]
        region_breakdown = list(collection.aggregate(region_pipeline))
        
        # Last 30 days trends
        thirty_days_ago = (datetime.now(timezone.utc) - timedelta(days=30)).isoformat()
        recent_pipeline = [
            {"$match": {"createdAt": {"$gte": thirty_days_ago}}},
            {"$group": {
                "_id": {"$dateToString": {"format": "%Y-%m-%d", "date": "$createdAt"}},
                "count": {"$sum": 1}
            }},
            {"$sort": {"_id": 1}}
        ]
        daily_trends = list(collection.aggregate(recent_pipeline))
        
        # Resolution stats (excluding personal data)
        resolved_pipeline = [
            {"$match": {"status": {"$in": ["resolved", "closed"]}}},
            {"$group": {
                "_id": None,
                "total_resolved": {"$sum": 1},
                "avg_resolution_time": {"$avg": "$resolution_time_hours"}
            }}
        ]
        resolution_stats = list(collection.aggregate(resolved_pipeline))
        
        return {
            "success": True,
            "data": {
                "total_complaints": total_complaints,
                "status_breakdown": [
                    {"status": item["_id"], "count": item["count"]}
                    for item in status_breakdown
                ],
                "category_breakdown": [
                    {"category": item["_id"], "count": item["count"]}
                    for item in category_breakdown
                ],
                "priority_breakdown": [
                    {"priority": item["_id"], "count": item["count"]}
                    for item in priority_breakdown
                ],
                "top_regions": [
                    {"region": item["_id"], "count": item["count"]}
                    for item in region_breakdown
                ],
                "daily_trends_last_30_days": daily_trends,
                "resolution_stats": resolution_stats[0] if resolution_stats else None,
                "last_updated": datetime.now(timezone.utc).isoformat()
            }
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "message": "Failed to fetch public statistics"
        }

@router.get("/heatmap")
async def get_public_heatmap(
    days: int = Query(30, ge=1, le=365, description="Number of days to include"),
    category: Optional[str] = Query(None, description="Filter by category")
):
    """
    Get public heatmap data for geographic visualization
    Returns aggregated location data without personal identifiers
    """
    try:
        collection = db.get_collection("complaints")
        
        # Date filter
        start_date = (datetime.now(timezone.utc) - timedelta(days=days)).isoformat()
        
        # Build query
        query = {
            "createdAt": {"$gte": start_date},
            "latitude": {"$exists": True, "$ne": None},
            "longitude": {"$exists": True, "$ne": None}
        }
        
        if category:
            query["category"] = category
        
        # Get location data
        complaints = list(collection.find(
            query,
            {
                "latitude": 1,
                "longitude": 1,
                "category": 1,
                "priority": 1,
                "status": 1,
                "_id": 0
            }
        ).limit(10000))  # Limit for performance
        
        # Aggregate data for heatmap
        heatmap_data = []
        for complaint in complaints:
            heatmap_data.append({
                "lat": complaint["latitude"],
                "lng": complaint["longitude"],
                "weight": get_priority_weight(complaint.get("priority", "medium")),
                "category": complaint["category"],
                "status": complaint["status"]
            })
        
        # Create intensity grid (simplified clustering)
        grid_size = 0.01  # Approximately 1km grid
        intensity_grid = defaultdict(lambda: {"count": 0, "total_weight": 0, "categories": defaultdict(int)})
        
        for point in heatmap_data:
            lat_grid = round(point["lat"] / grid_size) * grid_size
            lng_grid = round(point["lng"] / grid_size) * grid_size
            grid_key = f"{lat_grid:.3f},{lng_grid:.3f}"
            
            intensity_grid[grid_key]["count"] += 1
            intensity_grid[grid_key]["total_weight"] += point["weight"]
            intensity_grid[grid_key]["categories"][point["category"]] += 1
        
        # Convert to heatmap format
        heatmap_points = []
        for grid_key, data in intensity_grid.items():
            if data["count"] >= 2:  # Only show areas with multiple complaints
                lat, lng = map(float, grid_key.split(","))
                
                # Get dominant category
                dominant_category = max(data["categories"].items(), key=lambda x: x[1])[0]
                
                heatmap_points.append({
                    "lat": lat,
                    "lng": lng,
                    "intensity": min(data["total_weight"] / data["count"], 4.0),  # Normalize to 0-4
                    "count": data["count"],
                    "dominant_category": dominant_category,
                    "categories": dict(data["categories"])
                })
        
        return {
            "success": True,
            "data": {
                "heatmap_points": heatmap_points,
                "total_points": len(heatmap_points),
                "time_period_days": days,
                "category_filter": category,
                "generated_at": datetime.now(timezone.utc).isoformat()
            }
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "message": "Failed to generate heatmap data"
        }

@router.get("/trends")
async def get_public_trends(
    days: int = Query(90, ge=7, le=365, description="Number of days to analyze"),
    group_by: str = Query("day", regex="^(day|week|month)$", description="Group by period")
):
    """
    Get public trend data over time
    """
    try:
        collection = db.get_collection("complaints")
        
        start_date = (datetime.now(timezone.utc) - timedelta(days=days)).isoformat()
        
        # Group by period
        if group_by == "week":
            date_format = "%Y-%U"  # Year-Week
        elif group_by == "month":
            date_format = "%Y-%m"  # Year-Month
        else:  # day
            date_format = "%Y-%m-%d"
        
        pipeline = [
            {"$match": {"createdAt": {"$gte": start_date}}},
            {"$group": {
                "_id": {"$dateToString": {"format": date_format, "date": "$createdAt"}},
                "count": {"$sum": 1},
                "categories": {"$push": "$category"}
            }},
            {"$sort": {"_id": 1}}
        ]
        
        trends = list(collection.aggregate(pipeline))
        
        # Add category diversity to each period
        for trend in trends:
            unique_categories = len(set(trend["categories"]))
            trend["category_diversity"] = unique_categories
            trend["categories"] = None  # Remove detailed categories for privacy
        
        return {
            "success": True,
            "data": {
                "trends": trends,
                "period": group_by,
                "days_analyzed": days,
                "generated_at": datetime.now(timezone.utc).isoformat()
            }
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "message": "Failed to generate trend data"
        }

def get_priority_weight(priority: str) -> float:
    """Convert priority to numerical weight for heatmap intensity"""
    weights = {
        "emergency": 4.0,
        "high": 3.0,
        "medium": 2.0,
        "low": 1.0
    }
    return weights.get(priority.lower(), 2.0)
