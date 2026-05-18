import logging
from typing import Dict, Any, Optional
from datetime import datetime
from services.sms_service import SMSService
from utils.sms_helpers import format_sms_message
from db import db

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
    def log_notification(phone: str, message: str, status: str, error: Optional[str] = None, complaint_id: Optional[str] = None, sms_response: Optional[Dict[str, Any]] = None):
        """
        Log the notification status in the database.
        """
        try:
            log_entry = {
                "recipient_phone": phone,
                "message_content": message,
                "status": status,
                "error_message": error,
                "related_complaint_id": complaint_id,
                "created_at": datetime.utcnow()
            }
            if sms_response:
                log_entry.update({
                    "gateway_response": sms_response.get("response"),
                    "status_code": sms_response.get("status_code"),
                    "retries": sms_response.get("retries"),
                    "normalized_phone": sms_response.get("phone")
                })
            db.get_collection("notification_logs").insert_one(log_entry)
        except Exception as e:
            logger.error(f"Error logging notification: {e}")

    @staticmethod
    def send_notification_async(phone: str, template_name: str, data: Dict[str, Any], language: str = "en", complaint_id: Optional[str] = None):
        """
        Send a notification asynchronously. Should be called with BackgroundTasks.
        """
        try:
            template_content = NotificationService.get_template(template_name, language)
            message = format_sms_message(template_content, data)
            
            res = SMSService.send_sms(phone, message)
            status = "SENT" if res.get("success") else "FAILED"
            
            NotificationService.log_notification(
                phone, 
                message, 
                status, 
                error=res.get("error"), 
                complaint_id=complaint_id,
                sms_response=res
            )
        except Exception as e:
            logger.error(f"Error in send_notification_async: {e}")
            NotificationService.log_notification(phone, f"Template: {template_name}", "FAILED", error=str(e), complaint_id=complaint_id)
