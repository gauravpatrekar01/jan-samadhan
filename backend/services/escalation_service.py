import logging
from datetime import datetime, timedelta
from db import db
from services.notification_service import NotificationService
from config import settings

logger = logging.getLogger(__name__)

class EscalationService:
    @staticmethod
    def check_and_escalate_complaints():
        """
        Find unresolved complaints past SLA and trigger escalation notifications.
        """
        try:
            logger.info("Running scheduled escalation checks...")
            now = datetime.utcnow()
            
            # Find open complaints that are past their SLA deadline and not yet escalated
            query = {
                "status": {"$nin": ["Resolved", "Closed", "Rejected"]},
                "sla_deadline": {"$lt": now},
                "is_escalated": {"$ne": True}
            }
            
            past_due_complaints = db.get_collection("complaints").find(query)
            
            for complaint in past_due_complaints:
                complaint_id = complaint.get("grievanceID", complaint.get("id"))
                
                # Mark as escalated to avoid duplicate alerts
                db.get_collection("complaints").update_one(
                    {"_id": complaint["_id"]},
                    {"$set": {"is_escalated": True}}
                )
                
                # Try to get officer's phone number to notify
                officer_id = complaint.get("assigned_officer")
                if officer_id:
                    officer = db.get_collection("users").find_one({"email": officer_id})
                    if officer and officer.get("phone"):
                        # Send SMS to officer
                        NotificationService.send_notification_async(
                            phone=officer.get("phone"),
                            template_name="Complaint Escalated",
                            data={"complaint_id": complaint_id},
                            language=settings.DEFAULT_LANGUAGE,
                            complaint_id=complaint_id
                        )
                
                # Optionally notify citizen too
                citizen_phone = complaint.get("citizen_phone", complaint.get("phone"))
                if citizen_phone:
                    NotificationService.send_notification_async(
                        phone=citizen_phone,
                        template_name="Complaint Escalated",
                        data={"complaint_id": complaint_id},
                        language=settings.DEFAULT_LANGUAGE,
                        complaint_id=complaint_id
                    )
            
            logger.info("Scheduled escalation check completed successfully.")
        except Exception as e:
            logger.error(f"Error in EscalationService: {e}")
