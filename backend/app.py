from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import os
from routes import auth, complaints, admin
from db import db

app = FastAPI(title="JanSamadhan API", version="1.0.0")

# In production, set ALLOWED_ORIGINS="https://yourfrontend.com" in .env
ALLOWED_ORIGINS = os.getenv("ALLOWED_ORIGINS", "*").split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=500,
        content={"success": False, "error": {"code": 500, "message": "Internal Server Error"}},
    )


app.include_router(auth.router, prefix="/api/auth", tags=["auth"])
app.include_router(complaints.router, prefix="/api/complaints", tags=["complaints"])
app.include_router(admin.router, prefix="/api/admin", tags=["admin"])


@app.get("/")
def read_root():
    return {"message": "JanSamadhan API is running", "version": "1.0.0"}


@app.get("/health")
def health_check():
    return {"status": "ok"}


@app.get("/api/stats")
def public_stats():
    """
    Public endpoint — no auth required.
    Returns aggregate counts for the landing page KPI cards.
    """
    collection = db.get_collection("complaints")
    complaints_list = list(collection.find({}, {"_id": 0, "status": 1, "priority": 1}))

    total = len(complaints_list)
    resolved = sum(1 for c in complaints_list if c.get("status") in {"resolved", "closed"})
    pending = sum(1 for c in complaints_list if c.get("status") == "submitted")
    emergency = sum(1 for c in complaints_list if c.get("priority", "").lower() == "emergency")
    high = sum(1 for c in complaints_list if c.get("priority", "").lower() == "high")
    resolution_rate = round((resolved / total * 100), 1) if total > 0 else 0

    return {
        "success": True,
        "data": {
            "total_complaints": total,
            "resolved_complaints": resolved,
            "resolution_rate": resolution_rate,
            "pending": pending,
            "emergency": emergency,
            "high": high,
            "status_distribution": {
                "submitted": pending,
            },
            "priority_distribution": {
                "emergency": emergency,
                "high": high,
            },
        },
    }
