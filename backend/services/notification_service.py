import logging
from typing import Dict, Any, Optional
from datetime import datetime
from services.email_service import email_service
from db import db
import asyncio

logger = logging.getLogger(__name__)

class NotificationService:
    @staticmethod
    def log_notification(recipient: str, message: str, status: str, error: Optional[str] = None, complaint_id: Optional[str] = None, channel: str = "email", extra_response: Optional[Dict[str, Any]] = None):
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
                
            db.get_collection("notification_logs").insert_one(log_entry)
        except Exception as e:
            logger.error(f"Error logging notification: {e}")

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
