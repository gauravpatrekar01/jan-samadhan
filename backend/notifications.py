import logging
import threading
import asyncio
from datetime import datetime, timezone
from config import settings
from services.notification_service import NotificationService

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("notifications")

def _send_sms_thread(phone: str, message: str, complaint_id: str = None):
    try:
        from services.sms_service import SMSService
        logger.info(f"[BG_TASK] Starting SMS thread for {phone}")
        res = SMSService.send_sms(phone, message)
        status = "SENT" if res.get("success") else "FAILED"
        extra = {
            "gateway_response": res.get("response"),
            "status_code": res.get("status_code"),
            "retries": res.get("retries"),
            "normalized_phone": res.get("phone")
        }
        NotificationService.log_notification(phone, message, status, error=res.get("error"), complaint_id=complaint_id, channel="sms", extra_response=extra)
        logger.info(f"[BG_TASK] Completed SMS thread for {phone}. Status: {status}")
    except Exception as e:
        logger.error(f"[BG_TASK] Error in background SMS thread: {e}")

def _dispatch_email(email: str, subject: str, template: str, context: dict, complaint_id: str = None):
    """Fire and forget email sender wrapper."""
    try:
        loop = asyncio.get_running_loop()
        loop.create_task(NotificationService.send_email_async(email, subject, template, context, complaint_id))
    except RuntimeError:
        # If no event loop (e.g. running outside FastAPI), use a new loop
        asyncio.run(NotificationService.send_email_async(email, subject, template, context, complaint_id))

def send_notification(user_email: str, subject: str, message: str, channel: str = "email", phone: str = None, complaint_id: str = None):
    """
    Backward compatible notification sender.
    If called with channel="email", falls back to legacy string message context for the generic template,
    but it's recommended to use the specific notify_* functions which use proper HTML templates.
    """
    now = datetime.now(timezone.utc).isoformat()
    
    if channel.lower() == "email":
        logger.info(f"[{now}] 📧 Queuing Email -> {user_email}")
        _dispatch_email(user_email, subject, "base", {"content": message}, complaint_id)
             
    elif channel.lower() == "sms":
        logger.info(f"[{now}] 📱 Queuing SMS to {phone or user_email}")
        target_phone = phone if phone else user_email 
        threading.Thread(target=_send_sms_thread, args=(target_phone, message, complaint_id), daemon=True).start()
    else:
        logger.warning(f"Unknown notification channel: {channel}")
        
    return True

def notify_assignment(officer_email: str, complaint_id: str, officer_name: str, category: str = "General", department: str = "General", deadline: str = "Pending", phone: str = None):
    subject = f"New Grievance Assigned: {complaint_id}"
    
    # 1. Send Email using the new specific template
    context = {
        "complaint_id": complaint_id,
        "officer_name": officer_name,
        "category": category,
        "department": department,
        "deadline": deadline,
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
    
    _dispatch_email(officer_email, subject, "complaint_assigned", context, complaint_id)
    
    # 2. Trigger Android SMS Gateway
    sms_message = f"Grievance {complaint_id} assigned to you. JanSamadhan"
    send_notification(officer_email, subject, sms_message, channel="sms", phone=phone, complaint_id=complaint_id)

def notify_status_change(user_email: str, complaint_id: str, new_status: str, remarks: str = "", phone: str = None):
    subject = f"Update on your Grievance {complaint_id}"
    
    # 1. Send Email using the new specific template
    context = {
        "complaint_id": complaint_id,
        "new_status": new_status,
        "remarks": remarks,
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
    
    if new_status.lower() == "resolved":
        _dispatch_email(user_email, subject, "complaint_resolved", context, complaint_id)
    else:
        _dispatch_email(user_email, subject, "complaint_updated", context, complaint_id)
    
    # 2. Trigger Android SMS Gateway
    sms_message = f"Grievance {complaint_id} is now {new_status}. JanSamadhan"
    send_notification(user_email, subject, sms_message, channel="sms", phone=phone, complaint_id=complaint_id)

def notify_escalation(officer_email: str, complaint_id: str, new_level: int, phone: str = None):
    subject = f"URGENT: Escalation for Grievance {complaint_id}"
    
    # 1. Send Email
    context = {
        "complaint_id": complaint_id,
        "deadline": "IMMEDIATELY",
        "category": "Escalated Grievance"
    }
    _dispatch_email(officer_email, subject, "sla_breach", context, complaint_id)
    
    # 2. Send SMS
    sms_message = f"URGENT: Grievance {complaint_id} escalated to Level {new_level}. Immediate action required."
    send_notification(officer_email, subject, sms_message, channel="sms", phone=phone, complaint_id=complaint_id)

def notify_complaint_registered(user_email: str, complaint_id: str, citizen_name: str, phone: str = None, priority: str = "Medium", category: str = "General"):
    subject = f"Grievance {complaint_id} Registered"
    
    # 1. Send Email
    context = {
        "citizen_name": citizen_name,
        "complaint_id": complaint_id,
        "category": category,
        "priority": priority,
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
    _dispatch_email(user_email, subject, "complaint_submitted", context, complaint_id)
    
    # 2. Trigger Android SMS Gateway
    sms_message = f"Dear {citizen_name}, your complaint {complaint_id} is registered successfully. JanSamadhan"
    send_notification(user_email, subject, sms_message, channel="sms", phone=phone, complaint_id=complaint_id)
