import logging
import random
from datetime import datetime, timedelta
from config import settings
from db import db
from services.notification_service import NotificationService
from fastapi import BackgroundTasks

logger = logging.getLogger(__name__)

class OTPService:
    @staticmethod
    def generate_otp() -> str:
        return str(random.randint(100000, 999999))

    @staticmethod
    def create_and_send_otp(phone: str, background_tasks: BackgroundTasks, purpose: str = "LOGIN") -> bool:
        """
        Generate OTP, save to DB, and send via SMS using background tasks.
        """
        try:
            otp_code = OTPService.generate_otp()
            expires_at = datetime.utcnow() + timedelta(minutes=settings.OTP_EXPIRY_MINUTES)
            
            otp_record = {
                "phone": phone,
                "otp_code": otp_code,
                "purpose": purpose,
                "created_at": datetime.utcnow(),
                "expires_at": expires_at,
                "is_used": False
            }
            
            # Save to DB
            db.get_collection("otp").insert_one(otp_record)
            
            # Send SMS async
            background_tasks.add_task(
                NotificationService.send_notification_async,
                phone=phone,
                template_name="OTP Verification",
                data={"otp_code": otp_code},
                language=settings.DEFAULT_LANGUAGE
            )
            return True
        except Exception as e:
            logger.error(f"Error creating and sending OTP: {e}")
            return False

    @staticmethod
    def verify_otp(phone: str, otp_code: str, purpose: str = "LOGIN") -> bool:
        """
        Verify OTP.
        """
        try:
            now = datetime.utcnow()
            record = db.get_collection("otp").find_one({
                "phone": phone,
                "otp_code": otp_code,
                "purpose": purpose,
                "is_used": False,
                "expires_at": {"$gt": now}
            })
            
            if record:
                # Mark as used
                db.get_collection("otp").update_one(
                    {"_id": record["_id"]},
                    {"$set": {"is_used": True}}
                )
                return True
            return False
        except Exception as e:
            logger.error(f"Error verifying OTP: {e}")
            return False
