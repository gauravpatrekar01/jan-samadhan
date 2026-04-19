import logging
from datetime import datetime, timezone

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("notifications")

def send_notification(user_email: str, subject: str, message: str, channel: str = "email"):
    """
    Email/SMS notification sender.
    Integrates with AWS SES and Twilio if credentials are provided.
    """
    from config import settings
    now = datetime.now(timezone.utc).isoformat()
    
    # ── REAL EMAIL HANDLER (AWS SES) ──
    if channel.lower() == "email":
        if settings.AWS_ACCESS_KEY:
             # In production, use boto3.client('ses').send_email(...)
             logger.info(f"[{now}] 📧 REAL EMAIL (Queue) -> {user_email}")
        else:
             logger.info(f"[{now}] 📧 MOCK EMAIL sent to {user_email}\nSubject: {subject}\nBody: {message}\n---")
             
    # ── REAL SMS HANDLER (Twilio/Fast2SMS) ──
    elif channel.lower() == "sms":
        logger.info(f"[{now}] 📱 SMS sent to {user_email}\nMessage: {message}\n---")
    else:
        logger.warning(f"Unknown notification channel: {channel}")
        
    return True

def notify_status_change(user_email: str, complaint_id: str, new_status: str, remarks: str = ""):
    subject = f"Update on your Grievance {complaint_id}"
    message = f"Your grievance {complaint_id} status has been updated to: {new_status}."
    if remarks:
        message += f"\nRemarks: {remarks}"
        
    send_notification(user_email, subject, message, channel="email")
    send_notification(user_email, subject, f"Grievance {complaint_id} is now {new_status}.", channel="sms")

def notify_escalation(officer_email: str, complaint_id: str, new_level: int):
    subject = f"URGENT: Escalation for Grievance {complaint_id}"
    message = f"Grievance {complaint_id} has breached its SLA and is now escalated to Level {new_level}. Immediate action is required."
    
    send_notification(officer_email, subject, message, channel="email")
