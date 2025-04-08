"""
Scheduler for automating lottery data scraping
"""
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from flask import current_app
import logging
import atexit

from screenshot_manager import capture_screenshot
from ocr_processor import process_screenshot
from data_aggregator import aggregate_data
from models import db, ScheduleConfig

logger = logging.getLogger(__name__)

def init_scheduler(app):
    """
    Initialize the APScheduler for scheduled tasks.
    
    Args:
        app (Flask): Flask application instance
        
    Returns:
        BackgroundScheduler: Initialized scheduler
    """
    scheduler = BackgroundScheduler()
    scheduler.start()
    logger.info("Scheduler initialized")
    
    # Register shutdown function
    def shutdown_scheduler(exception=None):
        try:
            scheduler.shutdown()
        except Exception as e:
            logger.debug(f"Scheduler shutdown exception: {str(e)}")
    
    atexit.register(shutdown_scheduler)
    
    return scheduler

def schedule_task(scheduler, config):
    """
    Schedule a task based on configuration.
    
    Args:
        scheduler: The scheduler instance
        config: ScheduleConfig instance with scheduling details
    """
    if config.frequency == 'daily':
        trigger = CronTrigger(hour=config.hour, minute=config.minute)
        scheduler.add_job(
            func=run_lottery_task,
            trigger=trigger,
            args=[config.url, config.lottery_type],
            id=f"task_{config.id}",
            replace_existing=True
        )
        logger.info(f"Scheduled {config.lottery_type} task to run at {config.hour:02d}:{config.minute:02d}")
    
    # Add more frequency options as needed

def remove_task(scheduler, config_id):
    """
    Remove a scheduled task.
    
    Args:
        scheduler: The scheduler instance
        config_id: ID of the ScheduleConfig
    """
    try:
        scheduler.remove_job(f"task_{config_id}")
    except Exception as e:
        logger.debug(f"Scheduler remove_job exception: {str(e)}")

def run_lottery_task(url, lottery_type):
    """
    Run the lottery task workflow:
    1. Capture screenshot
    2. Process with OCR
    3. Aggregate data
    
    Args:
        url (str): URL to capture
        lottery_type (str): Type of lottery
    """
    try:
        # Step 1: Capture screenshot
        filepath, _ = capture_screenshot(url, lottery_type)
        
        if filepath:
            # Step 2: Process with OCR
            extracted_data = process_screenshot(filepath, lottery_type)
            
            if extracted_data:
                # Step 3: Aggregate data
                aggregate_data(extracted_data, lottery_type, url)
                
                # Update last run time
                with current_app.app_context():
                    config = ScheduleConfig.query.filter_by(url=url).first()
                    if config:
                        from datetime import datetime
                        config.last_run = datetime.now()
                        db.session.commit()
    except Exception as e:
        logger.error(f"Error running lottery task: {str(e)}")
