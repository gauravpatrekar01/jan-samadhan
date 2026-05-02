from fastapi import APIRouter, Query, Depends
from db import db
from datetime import datetime, timezone, timedelta
from dependencies import require_officer_or_admin
from typing import Optional

router = APIRouter(prefix="/api/kpis", tags=["kpis"])

@router.get("/dashboard")
async def get_dashboard_kpis(
    user: dict = Depends(require_officer_or_admin),
    days: int = Query(30, ge=1, le=365, description="Number of days for KPI calculation")
):
    """
    Get comprehensive KPIs for officer/admin dashboard
    Includes performance metrics, trends, and actionable insights
    """
    try:
        collection = db.get_collection("complaints")
        
        # Time-based calculations
        now = datetime.now(timezone.utc)
        start_date = (now - timedelta(days=days)).isoformat()
        last_week = (now - timedelta(days=7)).isoformat()
        yesterday = (now - timedelta(days=1)).isoformat()
        
        # User-specific filtering for officers
        user_filter = {}
        if user.get("role") == "officer":
            user_filter = {"assigned_officer": user.get("sub")}
        
        # Core Performance KPIs
        total_complaints = collection.count_documents({"createdAt": {"$gte": start_date}, **user_filter})
        resolved_complaints = collection.count_documents({
            "createdAt": {"$gte": start_date}, 
            "status": {"$in": ["resolved", "closed"]},
            **user_filter
        })
        
        # Resolution metrics
        resolution_rate = (resolved_complaints / total_complaints * 100) if total_complaints > 0 else 0
        
        # Average resolution time
        resolution_time_pipeline = [
            {"$match": {
                "createdAt": {"$gte": start_date},
                "status": {"$in": ["resolved", "closed"]},
                "resolution_time_hours": {"$exists": True, "$ne": None},
                **user_filter
            }},
            {"$group": {
                "_id": None,
                "avg_resolution_time": {"$avg": "$resolution_time_hours"},
                "median_resolution_time": {"$median": "$resolution_time_hours"},
                "min_resolution_time": {"$min": "$resolution_time_hours"},
                "max_resolution_time": {"$max": "$resolution_time_hours"}
            }}
        ]
        resolution_stats = list(collection.aggregate(resolution_time_pipeline))
        
        # SLA Performance
        sla_pipeline = [
            {"$match": {
                "createdAt": {"$gte": start_date},
                "status": {"$in": ["resolved", "closed"]},
                "sla_met": {"$exists": True},
                **user_filter
            }},
            {"$group": {
                "_id": None,
                "total": {"$sum": 1},
                "sla_met": {"$sum": {"$cond": [{"$eq": ["$sla_met", True]}, 1, 0]}}
            }}
        ]
        sla_stats = list(collection.aggregate(sla_pipeline))
        
        sla_compliance_rate = 0
        if sla_stats and sla_stats[0]["total"] > 0:
            sla_compliance_rate = (sla_stats[0]["sla_met"] / sla_stats[0]["total"] * 100)
        
        # Priority-based KPIs
        priority_kpis = {}
        for priority in ["emergency", "high", "medium", "low"]:
            total = collection.count_documents({
                "createdAt": {"$gte": start_date},
                "priority": priority,
                **user_filter
            })
            resolved = collection.count_documents({
                "createdAt": {"$gte": start_date},
                "priority": priority,
                "status": {"$in": ["resolved", "closed"]},
                **user_filter
            })
            
            priority_kpis[priority] = {
                "total": total,
                "resolved": resolved,
                "resolution_rate": (resolved / total * 100) if total > 0 else 0,
                "pending": total - resolved
            }
        
        # Category Performance
        category_pipeline = [
            {"$match": {"createdAt": {"$gte": start_date}, **user_filter}},
            {"$group": {
                "_id": "$category",
                "total": {"$sum": 1},
                "resolved": {"$sum": {"$cond": [{"$in": ["$status", ["resolved", "closed"]]}, 1, 0]}},
                "avg_resolution_time": {"$avg": "$resolution_time_hours"}
            }},
            {"$sort": {"total": -1}}
        ]
        category_performance = list(collection.aggregate(category_pipeline))
        
        # Weekly Trends
        weekly_pipeline = [
            {"$match": {"createdAt": {"$gte": start_date}, **user_filter}},
            {"$addFields": {
                "createdAtDate": {
                    "$cond": {
                        "if": {"$eq": [{"$type": "$createdAt"}, "string"]},
                        "then": {"$dateFromString": {"dateString": "$createdAt"}},
                        "else": "$createdAt"
                    }
                }
            }},
            {"$group": {
                "_id": {"$dateToString": {"format": "%Y-%W", "date": "$createdAtDate"}},
                "week_start": {"$min": "$createdAtDate"},
                "complaints_received": {"$sum": 1},
                "complaints_resolved": {"$sum": {"$cond": [{"$in": ["$status", ["resolved", "closed"]]}, 1, 0]}}
            }},
            {"$sort": {"_id": 1}}
        ]
        weekly_trends = list(collection.aggregate(weekly_pipeline))
        
        # Recent Activity (Last 24h, 7d)
        recent_24h = collection.count_documents({"createdAt": {"$gte": yesterday}, **user_filter})
        recent_7d = collection.count_documents({"createdAt": {"$gte": last_week}, **user_filter})
        
        # Escalation Metrics
        escalated_complaints = collection.count_documents({
            "createdAt": {"$gte": start_date},
            "escalated": True,
            **user_filter
        })
        
        escalation_rate = (escalated_complaints / total_complaints * 100) if total_complaints > 0 else 0
        
        # Customer Satisfaction (if available)
        satisfaction_pipeline = [
            {"$match": {
                "createdAt": {"$gte": start_date},
                "status": {"$in": ["resolved", "closed"]},
                "feedbackAverage": {"$exists": True, "$ne": None},
                **user_filter
            }},
            {"$group": {
                "_id": None,
                "avg_satisfaction": {"$avg": "$feedbackAverage"},
                "total_feedback": {"$sum": {"$cond": [{"$gt": ["$feedbackCount", 0]}, 1, 0]}}
            }}
        ]
        satisfaction_stats = list(collection.aggregate(satisfaction_pipeline))
        
        # Performance Score (0-100)
        performance_score = 0
        weights = {
            "resolution_rate": 0.3,
            "sla_compliance": 0.25,
            "avg_resolution_time": 0.2,
            "escalation_rate": 0.15,
            "satisfaction": 0.1
        }
        
        # Resolution rate score
        resolution_score = min(resolution_rate, 100)
        
        # SLA compliance score
        sla_score = min(sla_compliance_rate, 100)
        
        # Resolution time score (inverse - lower is better)
        avg_resolution_time = resolution_stats[0]["avg_resolution_time"] if resolution_stats else 0
        resolution_time_score = max(0, 100 - (avg_resolution_time * 2))  # 2 points per hour over ideal
        
        # Escalation score (inverse - lower is better)
        escalation_score = max(0, 100 - escalation_rate)
        
        # Satisfaction score
        satisfaction_score = satisfaction_stats[0]["avg_satisfaction"] if satisfaction_stats else 80
        
        performance_score = (
            resolution_score * weights["resolution_rate"] +
            sla_score * weights["sla_compliance"] +
            resolution_time_score * weights["avg_resolution_time"] +
            escalation_score * weights["escalation_rate"] +
            satisfaction_score * weights["satisfaction"]
        )
        
        return {
            "success": True,
            "data": {
                # Overall Performance
                "performance_score": round(performance_score, 2),
                "total_complaints": total_complaints,
                "resolved_complaints": resolved_complaints,
                "resolution_rate": round(resolution_rate, 2),
                
                # Time-based Metrics
                "avg_resolution_time_hours": resolution_stats[0]["avg_resolution_time"] if resolution_stats else 0,
                "median_resolution_time_hours": resolution_stats[0]["median_resolution_time"] if resolution_stats else 0,
                "sla_compliance_rate": round(sla_compliance_rate, 2),
                
                # Recent Activity
                "complaints_last_24h": recent_24h,
                "complaints_last_7d": recent_7d,
                "escalated_complaints": escalated_complaints,
                "escalation_rate": round(escalation_rate, 2),
                
                # Priority Breakdown
                "priority_performance": priority_kpis,
                
                # Category Performance
                "category_performance": [
                    {
                        "category": item["_id"],
                        "total": item["total"],
                        "resolved": item["resolved"],
                        "resolution_rate": round((item["resolved"] / item["total"] * 100) if item["total"] > 0 else 0, 2),
                        "avg_resolution_time": round(item["avg_resolution_time"], 2) if item["avg_resolution_time"] else 0
                    }
                    for item in category_performance
                ],
                
                # Trends
                "weekly_trends": weekly_trends,
                
                # Customer Satisfaction
                "customer_satisfaction": {
                    "avg_satisfaction": round(satisfaction_stats[0]["avg_satisfaction"], 2) if satisfaction_stats else 0,
                    "total_feedback": satisfaction_stats[0]["total_feedback"] if satisfaction_stats else 0
                },
                
                # Metadata
                "period_days": days,
                "calculated_at": now.isoformat(),
                "user_role": user.get("role"),
                "user_email": user.get("sub")
            }
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "message": "Failed to fetch dashboard KPIs"
        }

@router.get("/department")
async def get_department_kpis(
    user: dict = Depends(require_officer_or_admin),
    department: Optional[str] = Query(None, description="Filter by department"),
    days: int = Query(30, ge=1, le=365, description="Number of days for KPI calculation")
):
    """
    Get department-specific KPIs for comparative analysis
    """
    try:
        collection = db.get_collection("complaints")
        
        # Time-based calculations
        now = datetime.now(timezone.utc)
        start_date = (now - timedelta(days=days)).isoformat()
        
        # Department filtering
        dept_filter = {"department": department} if department else {}
        
        # Department comparison
        dept_pipeline = [
            {"$match": {"createdAt": {"$gte": start_date}, **dept_filter}},
            {"$group": {
                "_id": "$department",
                "total_complaints": {"$sum": 1},
                "resolved_complaints": {"$sum": {"$cond": [{"$in": ["$status", ["resolved", "closed"]]}, 1, 0]}},
                "avg_resolution_time": {"$avg": "$resolution_time_hours"},
                "emergency_cases": {"$sum": {"$cond": [{"$eq": ["$priority", "emergency"]}, 1, 0]}},
                "sla_met": {"$sum": {"$cond": [{"$eq": ["$sla_met", True]}, 1, 0]}}
            }},
            {"$sort": {"total_complaints": -1}}
        ]
        
        department_stats = list(collection.aggregate(dept_pipeline))
        
        # Calculate department rankings
        dept_rankings = []
        for i, dept in enumerate(department_stats):
            resolution_rate = (dept["resolved_complaints"] / dept["total_complaints"] * 100) if dept["total_complaints"] > 0 else 0
            sla_rate = (dept["sla_met"] / dept["total_complaints"] * 100) if dept["total_complaints"] > 0 else 0
            
            dept_rankings.append({
                "department": dept["_id"],
                "rank": i + 1,
                "total_complaints": dept["total_complaints"],
                "resolved_complaints": dept["resolved_complaints"],
                "resolution_rate": round(resolution_rate, 2),
                "avg_resolution_time": round(dept["avg_resolution_time"], 2) if dept["avg_resolution_time"] else 0,
                "emergency_cases": dept["emergency_cases"],
                "sla_compliance_rate": round(sla_rate, 2),
                "performance_score": round((resolution_rate * 0.4 + sla_rate * 0.3 + (100 - min(dept["avg_resolution_time"] * 2, 100)) * 0.3), 2)
            })
        
        return {
            "success": True,
            "data": {
                "department_rankings": dept_rankings,
                "total_departments": len(dept_rankings),
                "period_days": days,
                "calculated_at": now.isoformat()
            }
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "message": "Failed to fetch department KPIs"
        }
