from typing import Dict, Any, List, Optional
from datetime import datetime, timezone, timedelta
from db import db
import statistics
from collections import defaultdict

async def get_complaint_predictions(
    days_ahead: int = 30,
    region: Optional[str] = None,
    category: Optional[str] = None
) -> Dict[str, Any]:
    """
    Generate predictive analytics for complaints
    
    Args:
        days_ahead: Number of days to predict ahead
        region: Filter by region (optional)
        category: Filter by category (optional)
        
    Returns:
        Dict containing predictions and hotspot zones
    """
    try:
        collection = db.get_collection("complaints")
        
        # Build query
        query = {}
        if region:
            query["region"] = region
        if category:
            query["category"] = category
        
        # Get historical data (last 90 days)
        start_date = datetime.now(timezone.utc) - timedelta(days=90)
        historical_complaints = list(collection.find({
            **query,
            "createdAt": {"$gte": start_date.isoformat()}
        }).sort("createdAt", 1))
        
        if len(historical_complaints) < 10:
            return {
                "success": False,
                "message": "Insufficient historical data for predictions",
                "data_points": len(historical_complaints)
            }
        
        # Calculate moving averages
        predictions = calculate_moving_averages(historical_complaints, days_ahead)
        
        # Identify hotspot zones
        hotspots = identify_hotspot_zones(historical_complaints)
        
        # Predict by category
        category_predictions = predict_by_category(historical_complaints, days_ahead)
        
        # Predict by priority
        priority_predictions = predict_by_priority(historical_complaints, days_ahead)
        
        return {
            "success": True,
            "predictions": predictions,
            "hotspot_zones": hotspots,
            "category_breakdown": category_predictions,
            "priority_breakdown": priority_predictions,
            "data_points": len(historical_complaints),
            "prediction_period_days": days_ahead,
            "confidence_score": calculate_confidence_score(len(historical_complaints)),
            "generated_at": datetime.now(timezone.utc).isoformat()
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "message": "Failed to generate predictions"
        }

def calculate_moving_averages(
    complaints: List[Dict], 
    days_ahead: int
) -> Dict[str, Any]:
    """Calculate moving average predictions"""
    
    # Group complaints by day
    daily_counts = defaultdict(int)
    for complaint in complaints:
        if "createdAt" in complaint:
            date_str = complaint["createdAt"][:10]  # YYYY-MM-DD
            daily_counts[date_str] += 1
    
    # Calculate 7-day and 30-day moving averages
    dates = sorted(daily_counts.keys())
    counts = [daily_counts[date] for date in dates]
    
    if len(counts) < 7:
        # Not enough data for moving averages
        avg_daily = statistics.mean(counts) if counts else 0
        predicted_total = avg_daily * days_ahead
    else:
        # 7-day moving average
        ma7 = statistics.mean(counts[-7:])
        predicted_total = ma7 * days_ahead
    
    return {
        "predicted_total_complaints": round(predicted_total, 1),
        "average_daily": round(predicted_total / days_ahead, 1),
        "moving_average_7day": round(statistics.mean(counts[-7:]) if len(counts) >= 7 else 0, 1),
        "moving_average_30day": round(statistics.mean(counts[-30:]) if len(counts) >= 30 else 0, 1),
        "trend": calculate_trend(counts[-14:]) if len(counts) >= 14 else "stable"
    }

def identify_hotspot_zones(complaints: List[Dict]) -> List[Dict[str, Any]]:
    """Identify geographic hotspot zones"""
    
    # Group by region
    region_counts = defaultdict(int)
    region_categories = defaultdict(lambda: defaultdict(int))
    
    for complaint in complaints:
        region = complaint.get("region", "Unknown")
        category = complaint.get("category", "Unknown")
        
        region_counts[region] += 1
        region_categories[region][category] += 1
    
    # Calculate hotspot score for each region
    hotspots = []
    total_complaints = len(complaints)
    
    for region, count in region_counts.items():
        if count < 5:  # Skip regions with very few complaints
            continue
            
        # Hotspot score based on complaint density and diversity
        diversity_score = len(region_categories[region]) / max(len(region_categories[region]), 1)
        density_score = count / total_complaints
        hotspot_score = (density_score * 0.7) + (diversity_score * 0.3)
        
        # Get top categories for this region
        top_categories = sorted(
            region_categories[region].items(),
            key=lambda x: x[1],
            reverse=True
        )[:3]
        
        hotspots.append({
            "region": region,
            "complaint_count": count,
            "hotspot_score": round(hotspot_score, 3),
            "percentage_of_total": round((count / total_complaints) * 100, 1),
            "top_categories": [
                {"category": cat, "count": cnt}
                for cat, cnt in top_categories
            ],
            "severity": classify_severity(hotspot_score)
        })
    
    # Sort by hotspot score
    hotspots.sort(key=lambda x: x["hotspot_score"], reverse=True)
    
    return hotspots[:10]  # Return top 10 hotspots

def predict_by_category(
    complaints: List[Dict], 
    days_ahead: int
) -> List[Dict[str, Any]]:
    """Predict complaints by category"""
    
    category_counts = defaultdict(int)
    category_trends = defaultdict(list)
    
    # Group by category and track trends
    for complaint in complaints:
        category = complaint.get("category", "Unknown")
        category_counts[category] += 1
        
        # For trend analysis, we'd need date-based grouping
        # Simplified: just use current proportions
        category_trends[category].append(1)
    
    total_complaints = len(complaints)
    predictions = []
    
    for category, count in category_counts.items():
        if count < 3:  # Skip categories with very few complaints
            continue
            
        proportion = count / total_complaints
        predicted_count = proportion * (total_complaints / 90) * days_ahead  # Daily rate * days
        
        predictions.append({
            "category": category,
            "historical_count": count,
            "predicted_count": round(predicted_count, 1),
            "percentage_of_historical": round((count / total_complaints) * 100, 1),
            "trend": "stable"  # Simplified - would need proper time series analysis
        })
    
    return sorted(predictions, key=lambda x: x["predicted_count"], reverse=True)

def predict_by_priority(
    complaints: List[Dict], 
    days_ahead: int
) -> List[Dict[str, Any]]:
    """Predict complaints by priority level"""
    
    priority_counts = defaultdict(int)
    for complaint in complaints:
        priority = complaint.get("priority", "medium")
        priority_counts[priority] += 1
    
    total_complaints = len(complaints)
    predictions = []
    
    for priority in ["emergency", "high", "medium", "low"]:
        count = priority_counts.get(priority, 0)
        proportion = count / total_complaints if total_complaints > 0 else 0
        predicted_count = proportion * (total_complaints / 90) * days_ahead
        
        predictions.append({
            "priority": priority,
            "historical_count": count,
            "predicted_count": round(predicted_count, 1),
            "percentage_of_historical": round(proportion * 100, 1)
        })
    
    return predictions

def calculate_trend(values: List[float]) -> str:
    """Calculate trend from recent values"""
    if len(values) < 2:
        return "stable"
    
    # Simple linear regression
    x = list(range(len(values)))
    n = len(values)
    
    sum_x = sum(x)
    sum_y = sum(values)
    sum_xy = sum(x[i] * values[i] for i in range(n))
    sum_x2 = sum(x[i] ** 2 for i in range(n))
    
    if n * sum_x2 - sum_x ** 2 == 0:
        return "stable"
    
    slope = (n * sum_xy - sum_x * sum_y) / (n * sum_x2 - sum_x ** 2)
    
    if slope > 0.1:
        return "increasing"
    elif slope < -0.1:
        return "decreasing"
    else:
        return "stable"

def classify_severity(score: float) -> str:
    """Classify hotspot severity"""
    if score >= 0.15:
        return "critical"
    elif score >= 0.10:
        return "high"
    elif score >= 0.05:
        return "medium"
    else:
        return "low"

def calculate_confidence_score(data_points: int) -> float:
    """Calculate confidence score based on data points"""
    if data_points < 10:
        return 0.2
    elif data_points < 25:
        return 0.4
    elif data_points < 50:
        return 0.6
    elif data_points < 100:
        return 0.8
    else:
        return 0.95

async def get_resolution_time_predictions(
    region: Optional[str] = None,
    category: Optional[str] = None
) -> Dict[str, Any]:
    """
    Predict average resolution times based on historical data
    """
    try:
        collection = db.get_collection("complaints")
        
        query = {
            "status": {"$in": ["resolved", "closed"]},
            "timeline.stage": "Resolved"
        }
        
        if region:
            query["region"] = region
        if category:
            query["category"] = category
        
        resolved_complaints = list(collection.find(query))
        
        if len(resolved_complaints) < 5:
            return {
                "success": False,
                "message": "Insufficient resolution data"
            }
        
        resolution_times = []
        for complaint in resolved_complaints:
            timeline = complaint.get("timeline", [])
            created_time = None
            resolved_time = None
            
            for event in timeline:
                if event.get("stage") == "Submitted":
                    created_time = event.get("timestamp")
                elif event.get("stage") == "Resolved":
                    resolved_time = event.get("timestamp")
            
            if created_time and resolved_time:
                try:
                    created = datetime.fromisoformat(created_time.replace('Z', '+00:00'))
                    resolved = datetime.fromisoformat(resolved_time.replace('Z', '+00:00'))
                    resolution_hours = (resolved - created).total_seconds() / 3600
                    resolution_times.append(resolution_hours)
                except:
                    continue
        
        if not resolution_times:
            return {
                "success": False,
                "message": "No valid resolution times found"
            }
        
        return {
            "success": True,
            "average_resolution_hours": round(statistics.mean(resolution_times), 1),
            "median_resolution_hours": round(statistics.median(resolution_times), 1),
            "min_resolution_hours": round(min(resolution_times), 1),
            "max_resolution_hours": round(max(resolution_times), 1),
            "sample_size": len(resolution_times),
            "sla_compliance_rate": calculate_sla_compliance(resolution_times)
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "message": "Failed to calculate resolution time predictions"
        }

def calculate_sla_compliance(resolution_times: List[float]) -> float:
    """Calculate SLA compliance rate"""
    sla_hours = {"emergency": 24, "high": 48, "medium": 72, "low": 120}
    
    # Simplified: assume medium priority for SLA calculation
    target_sla = sla_hours["medium"]
    compliant_count = sum(1 for time in resolution_times if time <= target_sla)
    
    return round((compliant_count / len(resolution_times)) * 100, 1) if resolution_times else 0
