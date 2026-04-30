from fastapi import APIRouter, Depends
from pydantic import BaseModel
from datetime import datetime, timedelta, timezone
from dependencies import require_role
from db import db
from services.report_service import build_pdf_report, save_report_file

router = APIRouter()


class ReportRequest(BaseModel):
    days: int = 30
    region: str | None = None
    category: str | None = None


@router.post("/generate")
def generate_report(payload: ReportRequest, user: dict = Depends(require_role(["admin", "officer"]))):
    collection = db.get_collection("complaints")
    q = {}
    if payload.region:
        q["region"] = payload.region
    if payload.category:
        q["category"] = payload.category
    since = datetime.now(timezone.utc) - timedelta(days=payload.days)
    q["createdAt"] = {"$gte": since.isoformat()}

    docs = list(collection.find(q, {"_id": 0, "status": 1, "priority": 1, "category": 1}))
    total = len(docs)
    resolved = len([d for d in docs if (d.get("status") or "").lower() in {"resolved", "closed"}])
    pending = total - resolved
    emergencies = len([d for d in docs if (d.get("priority") or "").lower() == "emergency"])

    report_payload = {
        "generated_by": user.get("sub"),
        "window_days": payload.days,
        "filters": {"region": payload.region, "category": payload.category},
        "total_complaints": total,
        "resolved_complaints": resolved,
        "pending_complaints": pending,
        "resolution_rate": round((resolved / total * 100), 2) if total else 0,
        "emergency_cases": emergencies,
    }
    pdf_bytes = build_pdf_report(report_payload)
    report_url = save_report_file(pdf_bytes)
    return {"success": True, "data": {"report_url": report_url, "metrics": report_payload}}

