"""
Report Download Routes — PDF + Excel
NEW file. Registered alongside (not replacing) existing reports.py.
Prefix: /api/reports/download
"""

from fastapi import APIRouter, Depends, Query
from fastapi.responses import StreamingResponse
from io import BytesIO
from datetime import datetime, timedelta, timezone
from typing import Optional

from dependencies import require_role
from db import db
from services.report_generator import (
    generate_pdf_report,
    generate_excel_report,
    compute_distributions,
)

router = APIRouter()


def _fetch_complaints(
    days: int,
    status: Optional[str],
    category: Optional[str],
    region: Optional[str],
    assigned_to: Optional[str] = None,
) -> list:
    """Fetch complaints matching filters. Reuses the DB collection directly."""
    collection = db.get_collection("complaints")
    query = {}

    if days and days > 0:
        since = (datetime.now(timezone.utc) - timedelta(days=days)).isoformat()
        query["createdAt"] = {"$gte": since}
    if status:
        query["status"] = status.lower()
    if category:
        query["category"] = category
    if region:
        query["region"] = region
    if assigned_to:
        query["assigned_officer"] = assigned_to

    # Exclude heavy fields to keep payload lean
    projection = {
        "_id": 0, "votes_history": 0, "timeline": 0, "comments": 0,
    }
    return list(
        collection.find(query, projection)
        .sort("createdAt", -1)
        .limit(5000)
    )


# ──────────────────────────────────────────────────────────
# Admin Report — Full system overview
# ──────────────────────────────────────────────────────────

@router.get("/admin/pdf")
def download_admin_pdf(
    days: int = Query(30, ge=1, le=365),
    status: Optional[str] = Query(None),
    category: Optional[str] = Query(None),
    region: Optional[str] = Query(None),
    user: dict = Depends(require_role(["admin"])),
):
    """Download PDF report for admin — system-wide overview."""
    complaints = _fetch_complaints(days, status, category, region)
    dist = compute_distributions(complaints)

    pdf_bytes = generate_pdf_report(
        title=f"JanSamadhan Admin Report ({days}-Day Window)",
        generated_by=user.get("sub", "admin"),
        kpis=dist["kpis"],
        category_dist=dist["category_dist"],
        status_dist=dist["status_dist"],
        priority_dist=dist["priority_dist"],
        complaints=complaints,
        filters={"days": days, "status": status, "category": category, "region": region},
    )

    filename = f"JanSamadhan_Admin_Report_{datetime.now().strftime('%Y%m%d_%H%M')}.pdf"
    return StreamingResponse(
        BytesIO(pdf_bytes),
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )


@router.get("/admin/excel")
def download_admin_excel(
    days: int = Query(30, ge=1, le=365),
    status: Optional[str] = Query(None),
    category: Optional[str] = Query(None),
    region: Optional[str] = Query(None),
    user: dict = Depends(require_role(["admin"])),
):
    """Download Excel report for admin — system-wide overview."""
    complaints = _fetch_complaints(days, status, category, region)
    dist = compute_distributions(complaints)

    excel_bytes = generate_excel_report(
        title=f"JanSamadhan Admin Report ({days}-Day Window)",
        generated_by=user.get("sub", "admin"),
        kpis=dist["kpis"],
        category_dist=dist["category_dist"],
        status_dist=dist["status_dist"],
        priority_dist=dist["priority_dist"],
        complaints=complaints,
        filters={"days": days, "status": status, "category": category, "region": region},
    )

    filename = f"JanSamadhan_Admin_Report_{datetime.now().strftime('%Y%m%d_%H%M')}.xlsx"
    return StreamingResponse(
        BytesIO(excel_bytes),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )


# ──────────────────────────────────────────────────────────
# Officer Report — Scoped to assigned complaints
# ──────────────────────────────────────────────────────────

@router.get("/officer/pdf")
def download_officer_pdf(
    days: int = Query(30, ge=1, le=365),
    status: Optional[str] = Query(None),
    category: Optional[str] = Query(None),
    user: dict = Depends(require_role(["officer"])),
):
    """Download PDF report for officer — scoped to their assigned complaints."""
    officer_email = user.get("sub", "")
    complaints = _fetch_complaints(days, status, category, region=None, assigned_to=officer_email)
    dist = compute_distributions(complaints)

    pdf_bytes = generate_pdf_report(
        title=f"Officer Performance Report ({days}-Day Window)",
        generated_by=officer_email,
        kpis=dist["kpis"],
        category_dist=dist["category_dist"],
        status_dist=dist["status_dist"],
        priority_dist=dist["priority_dist"],
        complaints=complaints,
        filters={"days": days, "status": status, "category": category, "officer": officer_email},
    )

    filename = f"JanSamadhan_Officer_Report_{datetime.now().strftime('%Y%m%d_%H%M')}.pdf"
    return StreamingResponse(
        BytesIO(pdf_bytes),
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )


@router.get("/officer/excel")
def download_officer_excel(
    days: int = Query(30, ge=1, le=365),
    status: Optional[str] = Query(None),
    category: Optional[str] = Query(None),
    user: dict = Depends(require_role(["officer"])),
):
    """Download Excel report for officer — scoped to their assigned complaints."""
    officer_email = user.get("sub", "")
    complaints = _fetch_complaints(days, status, category, region=None, assigned_to=officer_email)
    dist = compute_distributions(complaints)

    excel_bytes = generate_excel_report(
        title=f"Officer Performance Report ({days}-Day Window)",
        generated_by=officer_email,
        kpis=dist["kpis"],
        category_dist=dist["category_dist"],
        status_dist=dist["status_dist"],
        priority_dist=dist["priority_dist"],
        complaints=complaints,
        filters={"days": days, "status": status, "category": category, "officer": officer_email},
    )

    filename = f"JanSamadhan_Officer_Report_{datetime.now().strftime('%Y%m%d_%H%M')}.xlsx"
    return StreamingResponse(
        BytesIO(excel_bytes),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )
