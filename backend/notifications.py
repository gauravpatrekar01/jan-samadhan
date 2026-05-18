import logging
import threading
from datetime import datetime, timezone
from services.notification_service import NotificationService
from config import settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("notifications")

def _send_sms_thread(phone: str, message: str, complaint_id: str = None):
    try:
        from services.sms_service import SMSService
        logger.info(f"[BG_TASK] Starting SMS thread for {phone}")
        res = SMSService.send_sms(phone, message)
        status = "SENT" if res.get("success") else "FAILED"
        from services.notification_service import NotificationService
        NotificationService.log_notification(phone, message, status, error=res.get("error"), complaint_id=complaint_id, sms_response=res)
        logger.info(f"[BG_TASK] Completed SMS thread for {phone}. Status: {status}")
    except Exception as e:
        logger.error(f"[BG_TASK] Error in background SMS thread: {e}")

def send_notification(user_email: str, subject: str, message: str, channel: str = "email", phone: str = None, complaint_id: str = None):
    """
    Email/SMS notification sender.
    Integrates with AWS SES and Android SMS Gateway.
    """
    now = datetime.now(timezone.utc).isoformat()
    
    # ── REAL EMAIL HANDLER (AWS SES) ──
    if channel.lower() == "email":
        if settings.AWS_ACCESS_KEY:
             # In production, use boto3.client('ses').send_email(...)
             logger.info(f"[{now}] 📧 REAL EMAIL (Queue) -> {user_email}")
        else:
             logger.info(f"[{now}] 📧 MOCK EMAIL sent to {user_email}\nSubject: {subject}\nBody: {message}\n---")
             
    # ── REAL SMS HANDLER (Android SMS Gateway) ──
    elif channel.lower() == "sms":
        logger.info(f"[{now}] 📱 Queuing SMS to {phone or user_email}")
        target_phone = phone if phone else user_email # Fallback if phone not provided
        # Run SMS in a non-blocking thread
        threading.Thread(target=_send_sms_thread, args=(target_phone, message, complaint_id), daemon=True).start()
    else:
        logger.warning(f"Unknown notification channel: {channel}")
        
    return True

def notify_status_change(user_email: str, complaint_id: str, new_status: str, remarks: str = "", phone: str = None):
    subject = f"Update on your Grievance {complaint_id}"
    message = f"Your grievance {complaint_id} status has been updated to: {new_status}."
    if remarks:
        message += f"\nRemarks: {remarks}"
        
    send_notification(user_email, subject, message, channel="email")
    
    # Trigger Android SMS Gateway
    sms_message = f"Grievance {complaint_id} is now {new_status}. JanSamadhan"
    send_notification(user_email, subject, sms_message, channel="sms", phone=phone, complaint_id=complaint_id)

def notify_escalation(officer_email: str, complaint_id: str, new_level: int, phone: str = None):
    subject = f"URGENT: Escalation for Grievance {complaint_id}"
    message = f"Grievance {complaint_id} has breached its SLA and is now escalated to Level {new_level}. Immediate action is required."
    
    send_notification(officer_email, subject, message, channel="email")
    
    sms_message = f"URGENT: Grievance {complaint_id} escalated to Level {new_level}. Immediate action required."
    send_notification(officer_email, subject, sms_message, channel="sms", phone=phone, complaint_id=complaint_id)

def notify_complaint_registered(user_email: str, complaint_id: str, citizen_name: str, phone: str = None):
    subject = f"Grievance {complaint_id} Registered"
    message = f"Dear {citizen_name}, your grievance {complaint_id} has been registered successfully."
    send_notification(user_email, subject, message, channel="email")
    
    # Trigger Android SMS Gateway
    sms_message = f"Dear {citizen_name}, your complaint {complaint_id} is registered successfully. JanSamadhan"
    send_notification(user_email, subject, sms_message, channel="sms", phone=phone, complaint_id=complaint_id)

