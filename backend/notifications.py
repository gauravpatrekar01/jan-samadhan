import logging
from datetime import datetime, timezone

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("notifications")

def send_notification(user_email: str, subject: str, message: str, channel: str = "email"):
    """
    Mock Email/SMS notification sender.
    In a real production system, this would integrate with AWS SES, SendGrid, or Twilio.
    """
    now = datetime.now(timezone.utc).isoformat()
    
    if channel.lower() == "email":
        logger.info(f"[{now}] 📧 EMAIL sent to {user_email}\nSubject: {subject}\nBody: {message}\n---")
    elif channel.lower() == "sms":
        logger.info(f"[{now}] 📱 SMS sent to {user_email}\nMessage: {message}\n---")
    else:
        logger.warning(f"Unknown notification channel: {channel}")
        
    # In a full deployment, we could also log this into a DB collection `notifications`
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
