import logging
from typing import Dict, Any, Optional
from datetime import datetime
from services.sms_service import SMSService
from services.email_service import email_service
from utils.sms_helpers import format_sms_message
from db import db
import asyncio

logger = logging.getLogger(__name__)

class NotificationService:
    @staticmethod
    def get_template(name: str, language: str = "en") -> str:
        """
        Fetch SMS template from the database, or return default templates if not found.
        """
        try:
            template_doc = db.get_collection("sms_templates").find_one({"name": name, "language": language})
            if template_doc and "content" in template_doc:
                return template_doc["content"]
        except Exception as e:
            logger.error(f"Error fetching template {name}: {e}")

        # Default templates
        defaults = {
            "Complaint Registered": "Your complaint {complaint_id} is registered successfully.",
            "Complaint Assigned": "Your complaint {complaint_id} has been assigned to {officer_name}.",
            "Complaint Status Updated": "The status of your complaint {complaint_id} is now {status}.",
            "Complaint Resolved": "Your complaint {complaint_id} is resolved.",
            "Complaint Escalated": "Complaint {complaint_id} has been escalated.",
            "OTP Verification": "Your OTP is {otp_code}. Valid for 5 minutes.",
            "AI Report Generated": "An AI summary for complaint {complaint_id} has been generated."
        }
        return defaults.get(name, "Notification from JanSamadhan.")

    @staticmethod
    def log_notification(recipient: str, message: str, status: str, error: Optional[str] = None, complaint_id: Optional[str] = None, channel: str = "sms", extra_response: Optional[Dict[str, Any]] = None):
        """
        Log the notification status in the database.
        """
        try:
            log_entry = {
                "recipient": recipient,
                "message_content": message,
                "status": status,
                "error_message": error,
                "related_complaint_id": complaint_id,
                "channel": channel,
                "created_at": datetime.utcnow()
            }
            if extra_response:
                log_entry.update(extra_response)
                
            # Maintain backward compatibility for sms
            if channel == "sms":
                log_entry["recipient_phone"] = recipient
                
            db.get_collection("notification_logs").insert_one(log_entry)
        except Exception as e:
            logger.error(f"Error logging notification: {e}")

    @staticmethod
    def send_notification_async(phone: str, template_name: str, data: Dict[str, Any], language: str = "en", complaint_id: Optional[str] = None):
        """
        Backward compatible SMS notification method.
        """
        try:
            template_content = NotificationService.get_template(template_name, language)
            message = format_sms_message(template_content, data)
            
            res = SMSService.send_sms(phone, message)
            status = "SENT" if res.get("success") else "FAILED"
            
            extra = {
                "gateway_response": res.get("response"),
                "status_code": res.get("status_code"),
                "retries": res.get("retries"),
                "normalized_phone": res.get("phone")
            }
            
            NotificationService.log_notification(
                phone, 
                message, 
                status, 
                error=res.get("error"), 
                complaint_id=complaint_id,
                channel="sms",
                extra_response=extra
            )
        except Exception as e:
            logger.error(f"Error in send_notification_async: {e}")
            NotificationService.log_notification(phone, f"Template: {template_name}", "FAILED", error=str(e), complaint_id=complaint_id, channel="sms")

    @staticmethod
    async def send_email_async(email: str, subject: str, template_name: str, context: Dict[str, Any], complaint_id: Optional[str] = None):
        """
        Send an email asynchronously and log it.
        """
        if not email:
            logger.warning("Attempted to send email but no email address provided.")
            return

        try:
            res = await email_service.send_email(email, subject, template_name, context)
            status = "SENT" if res.get("success") else "FAILED"
            
            extra = {
                "retries": res.get("retries"),
                "template": template_name
            }
            
            NotificationService.log_notification(
                email, 
                f"Subject: {subject} | Template: {template_name}", 
                status, 
                error=res.get("error") or res.get("message"), 
                complaint_id=complaint_id,
                channel="email",
                extra_response=extra
            )
        except Exception as e:
            logger.error(f"Error in send_email_async: {e}")
            NotificationService.log_notification(email, f"Subject: {subject} | Template: {template_name}", "FAILED", error=str(e), complaint_id=complaint_id, channel="email")

    @staticmethod
    def trigger_email_background(background_tasks, email: str, subject: str, template_name: str, context: Dict[str, Any], complaint_id: Optional[str] = None):
        """
        Helper to safely add send_email_async to FastAPI background tasks.
        """
        background_tasks.add_task(
            NotificationService.send_email_async,
            email,
            subject,
            template_name,
            context,
            complaint_id
        )
