import logging
from apscheduler.schedulers.background import BackgroundScheduler
from services.escalation_service import EscalationService

logger = logging.getLogger(__name__)

scheduler = BackgroundScheduler()

def start_scheduler():
    try:
        # Run daily check at midnight or every hour
        scheduler.add_job(
            EscalationService.check_and_escalate_complaints,
            'interval',
            hours=24,  # Adjust as needed (e.g. daily)
            id='escalation_job',
            replace_existing=True
        )
        scheduler.start()
        logger.info("Scheduler started successfully for background tasks.")
    except Exception as e:
        logger.error(f"Error starting scheduler: {e}")

def shutdown_scheduler():
    try:
        scheduler.shutdown()
        logger.info("Scheduler shut down successfully.")
    except Exception as e:
        logger.error(f"Error shutting down scheduler: {e}")
