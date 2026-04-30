from fastapi import APIRouter, Depends, Query
from services.prediction_service import get_complaint_predictions, get_resolution_time_predictions
from dependencies import require_officer_or_admin
from typing import Optional

router = APIRouter(prefix="/api/analytics", tags=["analytics"])

@router.get("/predictions")
async def get_predictions(
    days_ahead: int = Query(30, ge=1, le=365, description="Number of days to predict ahead"),
    region: Optional[str] = Query(None, description="Filter by region"),
    category: Optional[str] = Query(None, description="Filter by category"),
    user: dict = Depends(require_officer_or_admin)
):
    """
    Get predictive analytics for complaints
    Includes moving averages, hotspot zones, and category/priority breakdowns
    """
    result = await get_complaint_predictions(
        days_ahead=days_ahead,
        region=region,
        category=category
    )
    
    if not result.get("success"):
        return {
            "success": False,
            "message": result.get("message", "Failed to generate predictions"),
            "error": result.get("error")
        }
    
    return {
        "success": True,
        "data": result,
        "message": f"Predictions generated for next {days_ahead} days"
    }

@router.get("/resolution-time-predictions")
async def get_resolution_predictions(
    region: Optional[str] = Query(None, description="Filter by region"),
    category: Optional[str] = Query(None, description="Filter by category"),
    user: dict = Depends(require_officer_or_admin)
):
    """
    Get predicted resolution times based on historical data
    """
    result = await get_resolution_time_predictions(
        region=region,
        category=category
    )
    
    if not result.get("success"):
        return {
            "success": False,
            "message": result.get("message", "Failed to generate resolution predictions"),
            "error": result.get("error")
        }
    
    return {
        "success": True,
        "data": result,
        "message": "Resolution time predictions calculated successfully"
    }
