import os
import logging
from typing import Dict, Any, Optional
import aiosmtplib
from email.message import EmailMessage
from email.utils import formataddr
from jinja2 import Environment, FileSystemLoader, select_autoescape
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)

class EmailService:
    def __init__(self):
        self.smtp_host = os.getenv("SMTP_HOST", "smtp.gmail.com")
        self.smtp_port = int(os.getenv("SMTP_PORT", 587))
        self.smtp_user = os.getenv("SMTP_USER")
        self.smtp_password = os.getenv("SMTP_PASSWORD")
        self.smtp_from = os.getenv("SMTP_FROM_EMAIL", self.smtp_user)
        self.smtp_from_name = os.getenv("SMTP_FROM_NAME", "JanSamadhan")

        # Setup Jinja2 environment for templates
        template_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "templates", "email")
        
        # Ensure the templates directory exists to avoid errors on init
        os.makedirs(template_dir, exist_ok=True)
        
        self.jinja_env = Environment(
            loader=FileSystemLoader(template_dir),
            autoescape=select_autoescape(['html', 'xml'])
        )

    def _is_configured(self) -> bool:
        """Check if SMTP is properly configured."""
        if not self.smtp_user or not self.smtp_password:
            logger.warning("SMTP credentials not configured. Email will not be sent.")
            return False
        return True

    def render_template(self, template_name: str, context: Dict[str, Any]) -> str:
        """Render an HTML email template with given context variables."""
        try:
            template = self.jinja_env.get_template(f"{template_name}.html")
            return template.render(**context)
        except Exception as e:
            logger.error(f"Failed to render email template {template_name}: {e}")
            # Fallback text if template fails
            return f"Notification: {template_name}\n\nData: {context}"

    async def send_email(
        self, 
        to_email: str, 
        subject: str, 
        template_name: str, 
        context: Dict[str, Any],
        max_retries: int = 3
    ) -> Dict[str, Any]:
        """
        Send an email asynchronously using SMTP.
        Returns a dict with success boolean and details.
        """
        if not self._is_configured():
            return {
                "success": False,
                "error": "SMTP_NOT_CONFIGURED",
                "message": "SMTP credentials are missing in the environment."
            }

        # Render HTML content
        html_content = self.render_template(template_name, context)

        # Prepare message
        message = EmailMessage()
        message["From"] = formataddr((self.smtp_from_name, self.smtp_from))
        message["To"] = to_email
        message["Subject"] = subject
        
        # We can add plain text fallback here if needed, but HTML is standard now
        message.add_alternative(html_content, subtype="html")

        # Retry logic
        for attempt in range(1, max_retries + 1):
            try:
                # Use aiosmtplib for async sending
                await aiosmtplib.send(
                    message,
                    hostname=self.smtp_host,
                    port=self.smtp_port,
                    username=self.smtp_user,
                    password=self.smtp_password,
                    start_tls=True,
                    timeout=10.0
                )
                
                logger.info(f"Email sent successfully to {to_email} (Attempt {attempt})")
                return {
                    "success": True,
                    "message": "Email sent successfully",
                    "retries": attempt - 1
                }
                
            except Exception as e:
                error_msg = str(e)
                logger.error(f"Email failed to send to {to_email} (Attempt {attempt}/{max_retries}): {error_msg}")
                
                if attempt == max_retries:
                    return {
                        "success": False,
                        "error": "SMTP_ERROR",
                        "message": f"Failed to send email after {max_retries} attempts: {error_msg}",
                        "retries": attempt
                    }
        
        return {"success": False, "error": "UNKNOWN", "message": "Unexpected error in send_email"}

email_service = EmailService()
