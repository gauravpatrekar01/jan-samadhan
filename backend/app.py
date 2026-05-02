import logging
import time
from pythonjsonlogger import jsonlogger
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from jose import JWTError
import os
from routes import auth, complaints, admin, ngo, analytics, translations, chatbot, reports, predictions, public, kpis
from db import db
from config import settings
from limiter import limiter
from slowapi import _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from errors import APIError

# ── Structured Logging ──
logger = logging.getLogger()
logHandler = logging.StreamHandler()
formatter = jsonlogger.JsonFormatter('%(asctime)s %(levelname)s %(name)s %(message)s')
logHandler.setFormatter(formatter)
logger.addHandler(logHandler)
logger.setLevel(logging.INFO)

app = FastAPI(title="JanSamadhan API", version="2.0.0")

# ── Rate Limiting ──
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

# ── Security Headers Middleware (Helmet-like) ──
@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    try:
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        return response
    except Exception as e:
        logger.error({
            "type": "security_headers_middleware_error",
            "path": request.url.path,
            "error": str(e)
        })
        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "error": {
                    "code": "MIDDLEWARE_ERROR",
                    "message": "Internal server error in security middleware"
                }
            }
        )


@app.middleware("http")
async def detect_user_language(request: Request, call_next):
    try:
        raw_lang = request.headers.get("Accept-Language", "en")
        normalized = (raw_lang.split(",")[0].split("-")[0] or "en").lower()
        if normalized not in {"en", "mr", "hi"}:
            normalized = "en"
        request.state.preferred_language = normalized
        response = await call_next(request)
        response.headers["Content-Language"] = normalized
        return response
    except Exception as e:
        logger.error({
            "type": "language_detection_middleware_error",
            "path": request.url.path,
            "error": str(e)
        })
        # Fallback to English
        request.state.preferred_language = "en"
        response = await call_next(request)
        response.headers["Content-Language"] = "en"
        return response


# ── Exception Handlers ──
@app.exception_handler(APIError)
async def api_error_handler(request: Request, exc: APIError):
    return JSONResponse(status_code=exc.status_code, content=exc.detail)


@app.exception_handler(RateLimitExceeded)
async def rate_limit_handler(request: Request, exc: RateLimitExceeded):
    logger.warning({"type": "rate_limit_exceeded", "ip": get_remote_address(request), "path": request.url.path})
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

# ── Request Logging Middleware ──
@app.middleware("http")
async def log_requests(request: Request, call_next):
    try:
        start_time = time.time()
        response = await call_next(request)
        process_time = time.time() - start_time
        
        log_data = {
            "method": request.method,
            "path": request.url.path,
            "duration": f"{process_time:.4f}s",
            "status_code": response.status_code,
            "client": request.client.host if request.client else "unknown"
        }
        
        if response.status_code >= 400:
            logger.error(log_data)
        else:
            logger.info(log_data)
            
        response.headers["X-Process-Time"] = str(process_time)
        return response
    except Exception as e:
        logger.error({
            "type": "request_logging_middleware_error",
            "path": request.url.path if request else "unknown",
            "error": str(e)
        })
        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "error": {
                    "code": "MIDDLEWARE_ERROR",
                    "message": "Internal server error in logging middleware"
                }
            }
        )


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error({
        "type": "unhandled_exception",
        "path": request.url.path,
        "method": request.method,
        "error": str(exc),
        "error_type": type(exc).__name__
    })
    
    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "error": {
                "code": "INTERNAL_SERVER_ERROR",
                "message": "Internal Server Error",
                "details": str(exc) if os.getenv("DEBUG") else None,
            },
        },
    )

@app.exception_handler(JWTError)
async def jwt_exception_handler(request: Request, exc: JWTError):
    logger.warning({
        "type": "jwt_error",
        "path": request.url.path,
        "method": request.method,
        "error": str(exc)
    })
    
    return JSONResponse(
        status_code=401,
        content={
            "success": False,
            "error": {
                "code": "TOKEN_INVALID",
                "message": "Invalid token format or signature"
            }
        }
    )

@app.exception_handler(ValueError)
async def value_error_handler(request: Request, exc: ValueError):
    logger.warning({
        "type": "value_error",
        "path": request.url.path,
        "method": request.method,
        "error": str(exc)
    })
    
    return JSONResponse(
        status_code=400,
        content={
            "success": False,
            "error": {
                "code": "VALIDATION_ERROR",
                "message": str(exc)
            }
        }
    )

@app.exception_handler(KeyError)
async def key_error_handler(request: Request, exc: KeyError):
    logger.error({
        "type": "key_error",
        "path": request.url.path,
        "method": request.method,
        "error": str(exc)
    })
    
    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "error": {
                "code": "DATA_ERROR",
                "message": "Required data field is missing"
            }
        }
    )


# ── Health Check Middleware ──
@app.middleware("http")
async def health_check_middleware(request: Request, call_next):
    response = await call_next(request)
    return response


# ── Background Scheduler (Escalation Hooks) ──
from apscheduler.schedulers.background import BackgroundScheduler
from datetime import datetime, timezone, timedelta
from services.priority_service import escalate_complaint_doc

scheduler = BackgroundScheduler()

def check_escalations():
    try:
        now = datetime.now(timezone.utc)
        jobs_collection = db.get_collection("system_jobs")
        
        # Simple distributed lock check
        last_job = jobs_collection.find_one({"job_name": "escalation_check"})
        if last_job:
            last_run = datetime.fromisoformat(last_job["last_run"])
            if now - last_run < timedelta(minutes=10):
                return # Already run recently
        
        jobs_collection.update_one(
            {"job_name": "escalation_check"},
            {"$set": {"last_run": now.isoformat()}},
            upsert=True
        )

        collection = db.get_collection("complaints")
        # Limit to valid unclosed complaints with an SLA deadline that has passed
        complaints = collection.find({
            "status": {"$nin": ["resolved", "closed", "Rejected"]},
            "sla_deadline": {"$lt": now.isoformat(), "$exists": True},
            "$or": [
                {"last_escalated_at": {"$exists": False}},
                {"last_escalated_at": {"$lt": (now - timedelta(hours=1)).isoformat()}}
            ]
        })

        for complaint in complaints:
            next_doc = escalate_complaint_doc(complaint)
            new_level = next_doc.get("escalation_level", complaint.get("escalation_level", 0) + 1)
            if new_level > 3:
                continue

            escalation_entry = {
                "previous_level": str(new_level - 1),
                "new_level": str(new_level),
                "escalated_at": now.isoformat(),
                "reason": "SLA deadline breached."
            }

            timeline_event = {
                "stage": "Escalated",
                "timestamp": now.isoformat(),
                "updated_by_user_id": "system",
                "remarks": f"System auto-escalated SLA breach to Level {new_level}"
            }

            collection.update_one(
                {"id": complaint["id"]},
                {
                    "$set": {
                        "escalation_level": new_level,
                        "last_escalated_at": now.isoformat(),
                        "priority": next_doc.get("priority", complaint.get("priority", "medium")),
                        "sla_deadline": next_doc.get("sla_deadline", complaint.get("sla_deadline")),
                    },
                    "$push": {
                        "escalation_history": escalation_entry,
                        "timeline": timeline_event
                    }
                }
            )

            # Send Notification
            assigned_officer = complaint.get("assigned_officer")
            if assigned_officer:
                from notifications import notify_escalation
                notify_escalation(assigned_officer, complaint["id"], new_level)
    except Exception as e:
        print("Scheduler error:", str(e))

@app.on_event("startup")
def start_scheduler():
    scheduler.add_job(check_escalations, "interval", minutes=15)
    scheduler.start()
    
@app.on_event("shutdown")
def stop_scheduler():
    scheduler.shutdown()


from fastapi.staticfiles import StaticFiles

# ── Routes ──
app.include_router(auth.router, prefix="/api/auth", tags=["auth"])
app.include_router(complaints.router, prefix="/api/complaints", tags=["complaints"])
app.include_router(admin.router, prefix="/api/admin", tags=["admin"])
app.include_router(ngo.router, prefix="/api/ngo", tags=["ngo"])
app.include_router(analytics.router, prefix="/api/analytics", tags=["analytics"])
app.include_router(predictions.router, prefix="/api/analytics", tags=["predictions"])
app.include_router(public.router, tags=["public"])
app.include_router(kpis.router, tags=["kpis"])
app.include_router(translations.router, prefix="/api/translations", tags=["translations"])
app.include_router(chatbot.router, prefix="/api/chatbot", tags=["chatbot"])
app.include_router(reports.router, prefix="/api/reports", tags=["reports"])

# ── Static Files (Uploads Fallback) ──
os.makedirs("static/uploads", exist_ok=True)
app.mount("/static", StaticFiles(directory="static"), name="static")


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
        "under_review": status_map.get("under_review", 0) + status_map.get("under review", 0) + status_map.get("assigned", 0),
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
