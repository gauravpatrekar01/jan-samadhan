from datetime import datetime, timezone
from io import BytesIO
import os


def build_pdf_report(data: dict) -> bytes:
    """
    Generate a simple PDF report.
    Falls back to plain-text PDF-like bytes when ReportLab is unavailable.
    """
    try:
        from reportlab.lib.pagesizes import A4
        from reportlab.pdfgen import canvas

        buffer = BytesIO()
        c = canvas.Canvas(buffer, pagesize=A4)
        y = 800
        c.setFont("Helvetica-Bold", 14)
        c.drawString(40, y, "JanSamadhan Analytics Report")
        y -= 24
        c.setFont("Helvetica", 10)
        c.drawString(40, y, f"Generated at: {datetime.now(timezone.utc).isoformat()}")
        y -= 24
        for k, v in data.items():
            c.drawString(40, y, f"{k}: {v}")
            y -= 16
            if y < 60:
                c.showPage()
                y = 800
        c.save()
        return buffer.getvalue()
    except Exception:
        text = "JanSamadhan Report\n" + "\n".join([f"{k}: {v}" for k, v in data.items()])
        return text.encode("utf-8")


def save_report_file(content: bytes, reports_dir: str = "static/reports") -> str:
    os.makedirs(reports_dir, exist_ok=True)
    filename = f"report-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}.pdf"
    path = os.path.join(reports_dir, filename)
    with open(path, "wb") as f:
        f.write(content)
    return f"/static/reports/{filename}"

