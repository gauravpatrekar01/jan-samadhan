from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import os
from routes import auth, complaints, admin
from db import db
from config import settings
from slowapi import Limiter
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from errors import APIError

app = FastAPI(title="JanSamadhan API", version="2.0.0")

# ── Rate Limiting ──
limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter

# ── CORS Configuration ──
# For development, allow all origins to enable local development
ALLOWED_ORIGINS = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization"],
)


# ── Exception Handlers ──
@app.exception_handler(APIError)
async def api_error_handler(request: Request, exc: APIError):
    return JSONResponse(status_code=exc.status_code, content=exc.detail)


@app.exception_handler(RateLimitExceeded)
async def rate_limit_handler(request: Request, exc: RateLimitExceeded):
    return JSONResponse(
        status_code=429,
        content={
            "success": False,
            "error": {
                "code": "RATE_LIMIT_EXCEEDED",
                "message": "Too many requests. Please try again later.",
            },
        },
    )


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "error": {
                "code": 500,
                "message": "Internal Server Error",
                "details": str(exc) if os.getenv("DEBUG") else None,
            },
        },
    )


# ── Health Check Middleware ──
@app.middleware("http")
async def health_check_middleware(request: Request, call_next):
    response = await call_next(request)
    return response


# ── Routes ──
app.include_router(auth.router, prefix="/api/auth", tags=["auth"])
app.include_router(complaints.router, prefix="/api/complaints", tags=["complaints"])
app.include_router(admin.router, prefix="/api/admin", tags=["admin"])


# ── Root Endpoints ──
@app.get("/")
def read_root():
    return {"message": "JanSamadhan API", "version": "2.0.0", "status": "operational"}


@app.get("/health")
def health_check():
    return {"status": "ok", "version": "2.0.0"}


@app.get("/api/stats")
def public_stats():
    """
    Public endpoint — no auth required.
    Returns aggregate counts for the landing page KPI cards.
    Uses optimized MongoDB aggregation for performance.
    """
    collection = db.get_collection("complaints")
    
    # Use MongoDB aggregation pipeline for efficiency
    pipeline = [
        {
            "$facet": {
                "total_count": [{"$count": "count"}],
                "status_stats": [
                    {
                        "$group": {
                            "_id": "$status",
                            "count": {"$sum": 1}
                        }
                    }
                ],
                "priority_stats": [
                    {
                        "$group": {
                            "_id": {"$toLower": "$priority"},
                            "count": {"$sum": 1}
                        }
                    }
                ]
            }
        }
    ]
    
    result = list(collection.aggregate(pipeline))
    
    if not result:
        return {
            "success": True,
            "data": {
                "total_complaints": 0,
                "resolved_complaints": 0,
                "resolution_rate": 0,
                "pending": 0,
                "emergency": 0,
                "high": 0,
                "status_distribution": {
                    "submitted": 0,
                    "under_review": 0,
                    "in_progress": 0,
                    "resolved": 0,
                    "closed": 0
                },
                "priority_distribution": {"emergency": 0, "high": 0, "medium": 0, "low": 0},
            },
        }
    
    data = result[0]
    total = data["total_count"][0]["count"] if data["total_count"] else 0
    
    # Parse status statistics
    status_map = {s["_id"]: s["count"] for s in data["status_stats"]}
    resolved = status_map.get("resolved", 0) + status_map.get("closed", 0)
    pending = status_map.get("submitted", 0)
    status_distribution = {
        "submitted": status_map.get("submitted", 0),
        "under_review": status_map.get("under_review", 0) + status_map.get("under review", 0),
        "in_progress": status_map.get("in_progress", 0) + status_map.get("in progress", 0),
        "resolved": status_map.get("resolved", 0),
        "closed": status_map.get("closed", 0),
    }

    # Parse priority statistics
    priority_map = {p["_id"]: p["count"] for p in data["priority_stats"]}
    emergency = priority_map.get("emergency", 0)
    high = priority_map.get("high", 0)
    medium = priority_map.get("medium", 0)
    low = priority_map.get("low", 0)
    
    resolution_rate = round((resolved / total * 100), 1) if total > 0 else 0

    # Quick secondary query for average satisfaction
    # Since aggregation pipeline is already complex and satisfaction is simple
    complaints = list(collection.find({}, {"_id": 0, "feedback": 1, "feedbackAverage": 1, "feedbackCount": 1}))
    total_ratings = 0
    total_rating_sum = 0
    for c in complaints:
        count = c.get("feedbackCount") if c.get("feedbackCount") is not None else len(c.get("feedback", []) or [])
        if count > 0:
            if c.get("feedbackAverage") is not None:
                total_rating_sum += c.get("feedbackAverage", 0) * count
            else:
                total_rating_sum += sum(item.get("rating", 0) for item in (c.get("feedback") or []))
            total_ratings += count

    average_satisfaction = round((total_rating_sum / total_ratings), 2) if total_ratings > 0 else 0

    return {
        "success": True,
        "data": {
            "total_complaints": total,
            "resolved_complaints": resolved,
            "resolution_rate": resolution_rate,
            "average_satisfaction": average_satisfaction,
            "pending": pending,
            "emergency": emergency,
            "high": high,
            "status_distribution": status_distribution,
            "priority_distribution": {
                "emergency": emergency,
                "high": high,
                "medium": medium,
                "low": low,
            },
        },
    }
