from fastapi import APIRouter, Query
from db import db
from datetime import datetime, timezone, timedelta
from collections import defaultdict
from typing import Optional

router = APIRouter(prefix="/api/public", tags=["public"])

@router.get("/stats")
async def get_public_stats():
    """
    Get comprehensive public statistics and KPIs about complaints
    No authentication required, excludes personal data
    """
    try:
        collection = db.get_collection("complaints")
        
        # Time-based calculations
        now = datetime.now(timezone.utc)
        thirty_days_ago = (now - timedelta(days=30)).isoformat()
        seven_days_ago = (now - timedelta(days=7)).isoformat()
        one_day_ago = (now - timedelta(days=1)).isoformat()
        
        # Total complaints
        total_complaints = collection.count_documents({})
        
        # Recent activity KPIs
        complaints_last_24h = collection.count_documents({"createdAt": {"$gte": one_day_ago}})
        complaints_last_7d = collection.count_documents({"createdAt": {"$gte": seven_days_ago}})
        complaints_last_30d = collection.count_documents({"createdAt": {"$gte": thirty_days_ago}})
        
        # Status breakdown with percentages
        status_pipeline = [
            {"$group": {"_id": "$status", "count": {"$sum": 1}}},
            {"$sort": {"count": -1}}
        ]
        status_breakdown = list(collection.aggregate(status_pipeline))
        
        # Calculate percentages
        status_distribution = []
        for item in status_breakdown:
            percentage = (item["count"] / total_complaints * 100) if total_complaints > 0 else 0
            status_distribution.append({
                "status": item["_id"],
                "count": item["count"],
                "percentage": round(percentage, 2)
            })
        
        # Priority breakdown with percentages
        priority_pipeline = [
            {"$group": {"_id": "$priority", "count": {"$sum": 1}}},
            {"$sort": {"count": -1}}
        ]
        priority_breakdown = list(collection.aggregate(priority_pipeline))
        
        priority_distribution = []
        for item in priority_breakdown:
            percentage = (item["count"] / total_complaints * 100) if total_complaints > 0 else 0
            priority_distribution.append({
                "priority": item["_id"],
                "count": item["count"],
                "percentage": round(percentage, 2)
            })
        
        # Category breakdown with percentages
        category_pipeline = [
            {"$group": {"_id": "$category", "count": {"$sum": 1}}},
            {"$sort": {"count": -1}}
        ]
        category_breakdown = list(collection.aggregate(category_pipeline))
        
        category_distribution = []
        for item in category_breakdown:
            percentage = (item["count"] / total_complaints * 100) if total_complaints > 0 else 0
            category_distribution.append({
                "category": item["_id"],
                "count": item["count"],
                "percentage": round(percentage, 2)
            })
        
        # Resolution KPIs
        resolved_complaints = collection.count_documents({"status": {"$in": ["resolved", "closed"]}})
        pending_complaints = collection.count_documents({"status": "submitted"})
        in_progress_complaints = collection.count_documents({"status": {"$in": ["under_review", "in_progress"]}})
        
        # Resolution rate
        resolution_rate = (resolved_complaints / total_complaints * 100) if total_complaints > 0 else 0
        
        # Average resolution time
        resolution_pipeline = [
            {"$match": {"status": {"$in": ["resolved", "closed"]}, "resolution_time_hours": {"$exists": True, "$ne": None}}},
            {"$group": {
                "_id": None,
                "avg_resolution_time": {"$avg": "$resolution_time_hours"},
                "min_resolution_time": {"$min": "$resolution_time_hours"},
                "max_resolution_time": {"$max": "$resolution_time_hours"}
            }}
        ]
        resolution_time_stats = list(collection.aggregate(resolution_pipeline))
        
        # SLA compliance
        sla_met_pipeline = [
            {"$match": {"status": {"$in": ["resolved", "closed"]}, "sla_met": {"$exists": True}}},
            {"$group": {
                "_id": None,
                "total": {"$sum": 1},
                "sla_met": {"$sum": {"$cond": [{"$eq": ["$sla_met", True]}, 1, 0]}}
            }}
        ]
        sla_stats = list(collection.aggregate(sla_met_pipeline))
        
        sla_compliance_rate = 0
        if sla_stats and sla_stats[0]["total"] > 0:
            sla_compliance_rate = (sla_stats[0]["sla_met"] / sla_stats[0]["total"] * 100)
        
        # Regional breakdown (top 10)
        region_pipeline = [
            {"$group": {"_id": "$region", "count": {"$sum": 1}}},
            {"$sort": {"count": -1}},
            {"$limit": 10}
        ]
        region_breakdown = list(collection.aggregate(region_pipeline))
        
        # Daily trends for last 30 days
        daily_trends_pipeline = [
            {"$match": {"createdAt": {"$gte": thirty_days_ago}}},
            {"$group": {
                "_id": {"$dateToString": {"format": "%Y-%m-%d", "date": "$createdAt"}},
                "count": {"$sum": 1},
                "resolved": {"$sum": {"$cond": [{"$in": ["$status", ["resolved", "closed"]]}, 1, 0]}}
            }},
            {"$sort": {"_id": 1}}
        ]
        daily_trends = list(collection.aggregate(daily_trends_pipeline))
        
        # Emergency/high priority alerts
        emergency_complaints = collection.count_documents({"priority": "emergency", "status": {"$ne": "resolved"}})
        high_priority_complaints = collection.count_documents({"priority": "high", "status": {"$ne": "resolved"}})
        
        # Performance KPIs
        avg_complaints_per_day = complaints_last_30d / 30
        growth_rate_7d = ((complaints_last_7d - complaints_last_30d/4) / (complaints_last_30d/4) * 100) if complaints_last_30d > 0 else 0
        
        return {
            "success": True,
            "data": {
                # Core KPIs
                "total_complaints": total_complaints,
                "resolved_complaints": resolved_complaints,
                "pending_complaints": pending_complaints,
                "in_progress_complaints": in_progress_complaints,
                "resolution_rate": round(resolution_rate, 2),
                
                # Activity KPIs
                "complaints_last_24h": complaints_last_24h,
                "complaints_last_7d": complaints_last_7d,
                "complaints_last_30d": complaints_last_30d,
                "avg_complaints_per_day": round(avg_complaints_per_day, 2),
                "growth_rate_7d": round(growth_rate_7d, 2),
                
                # Priority KPIs
                "emergency_complaints": emergency_complaints,
                "high_priority_complaints": high_priority_complaints,
                "priority_distribution": priority_distribution,
                
                # Performance KPIs
                "sla_compliance_rate": round(sla_compliance_rate, 2),
                "resolution_time_stats": resolution_time_stats[0] if resolution_time_stats else None,
                
                # Breakdown data
                "status_distribution": status_distribution,
                "category_distribution": category_distribution,
                "top_regions": [
                    {"region": item["_id"], "count": item["count"]}
                    for item in region_breakdown
                ],
                "daily_trends_last_30_days": daily_trends,
                
                # Metadata
                "last_updated": now.isoformat()
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
