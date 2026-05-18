import logging
import requests
from typing import List, Optional, Dict, Any
from config import settings
import traceback

logger = logging.getLogger(__name__)

class SMSService:
    @staticmethod
    def format_mobile_number(phone: str) -> str:
        """
        Normalize Indian mobile number format.
        """
        if not phone:
            return ""
        # Remove spaces, dashes, and other non-numeric characters except +
        phone = "".join(c for c in phone if c.isdigit() or c == "+")
        if phone.startswith("+91"):
            phone = phone[3:]
        elif phone.startswith("91") and len(phone) == 12:
            phone = phone[2:]
        elif phone.startswith("0") and len(phone) == 11:
            phone = phone[1:]
        return phone

    @staticmethod
    def validate_mobile_number(phone: str) -> bool:
        """
        Basic Indian mobile number validation.
        """
        normalized = SMSService.format_mobile_number(phone)
        if normalized.isdigit() and len(normalized) == 10:
            return True
        return False

    @staticmethod
    def send_sms(phone: str, message: str, device_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Send a single SMS using the Android SMS Gateway.
        Returns a dict with delivery status and diagnostic info.
        """
        normalized_phone = SMSService.format_mobile_number(phone)
        
        result = {
            "success": False,
            "phone": normalized_phone,
            "original_phone": phone,
            "retries": 0,
            "error": None,
            "response": None,
            "status_code": None
        }

        if not normalized_phone or not message:
            error_msg = "Phone number and message are required."
            logger.error(error_msg)
            result["error"] = error_msg
            return result

        if not SMSService.validate_mobile_number(normalized_phone):
            logger.warning(f"Invalid mobile number format: {phone}")
            # We still attempt sending in case the gateway accepts other formats,
            # but we log the warning.

        device_id = device_id or settings.DEVICE_ID

        # Add both 'phone' and 'number' for maximum compatibility with different gateway versions
        payload = {
            "device_id": device_id,
            "phone": normalized_phone,
            "number": normalized_phone, 
            "message": message
        }
        
        headers = {}
        if settings.SMS_GATEWAY_TOKEN:
            headers["Authorization"] = f"Bearer {settings.SMS_GATEWAY_TOKEN}"

        if settings.SMS_DEBUG:
            logger.info(f"[SMS_DEBUG] URL: {settings.SMS_GATEWAY_URL}")
            logger.info(f"[SMS_DEBUG] Payload: {payload}")

        for attempt in range(settings.MAX_SMS_RETRIES):
            result["retries"] = attempt + 1
            try:
                response = requests.post(
                    settings.SMS_GATEWAY_URL,
                    json=payload,
                    headers=headers,
                    timeout=settings.SMS_TIMEOUT_SECONDS
                )
                
                result["status_code"] = response.status_code
                result["response"] = response.text
                
                if settings.SMS_DEBUG:
                    logger.info(f"[SMS_DEBUG] Response Status: {response.status_code}")
                    logger.info(f"[SMS_DEBUG] Response Body: {response.text}")
                
                if response.status_code in [200, 201, 202]:
                    logger.info(f"SMS sent successfully to {normalized_phone}")
                    result["success"] = True
                    return result
                else:
                    logger.warning(f"SMS sending failed (attempt {attempt + 1}): HTTP {response.status_code} - {response.text}")
                    result["error"] = f"HTTP {response.status_code}: {response.text}"
                    
            except requests.exceptions.Timeout as e:
                logger.error(f"SMS Timeout on attempt {attempt + 1}: {e}")
                result["error"] = "Connection Timeout"
            except requests.exceptions.ConnectionError as e:
                logger.error(f"SMS Connection Error on attempt {attempt + 1}: {e}")
                result["error"] = "Connection Refused/Unreachable"
            except requests.exceptions.RequestException as e:
                logger.error(f"SMS Request Exception on attempt {attempt + 1}: {e}")
                result["error"] = str(e)
            except Exception as e:
                logger.error(f"Unexpected SMS Error on attempt {attempt + 1}: {e}")
                logger.debug(traceback.format_exc())
                result["error"] = str(e)
                
        logger.error(f"Failed to send SMS to {normalized_phone} after {settings.MAX_SMS_RETRIES} attempts. Last error: {result['error']}")
        return result

    @staticmethod
    def send_bulk_sms(messages: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Send multiple SMS messages safely.
        messages = [{"phone": "123", "message": "msg"}]
        """
        results = {"success": 0, "failed": 0, "errors": []}
        for item in messages:
            try:
                res = SMSService.send_sms(item.get("phone"), item.get("message"), item.get("device_id"))
                if res["success"]:
                    results["success"] += 1
                else:
                    results["failed"] += 1
                    results["errors"].append({"phone": item.get("phone"), "error": res["error"]})
            except Exception as e:
                logger.error(f"Error in bulk SMS for {item.get('phone')}: {e}")
                results["failed"] += 1
                results["errors"].append({"phone": item.get("phone"), "error": str(e)})
        return results

    @staticmethod
    def retry_failed_sms(failed_logs: List[Dict[str, Any]]):
        """
        Retry failed SMS from logs.
        """
        return SMSService.send_bulk_sms(failed_logs)
