import logging
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from flask import Flask
from models import db, ScheduleConfig
from screenshot_manager import capture_screenshot
from ocr_processor import process_screenshot
from data_aggregator import aggregate_data

logger = logging.getLogger(__name__)

def init_scheduler(app: Flask):
    """
    Initialize the APScheduler for scheduled tasks.
    
    Args:
        app (Flask): Flask application instance
        
    Returns:
        BackgroundScheduler: Initialized scheduler
    """
    scheduler = BackgroundScheduler()
    scheduler.start()
    
    # Register shutdown function with Flask
    app.scheduler = scheduler
    
    @app.teardown_appcontext
    def shutdown_scheduler(exception=None):
        if hasattr(app, 'scheduler'):
            try:
                app.scheduler.shutdown(wait=False)
            except Exception as e:
                logger.debug(f"Scheduler shutdown exception: {str(e)}")
    
    logger.info("Scheduler initialized")
    return scheduler

def schedule_task(scheduler, config):
    """
    Schedule a task based on configuration.
    
    Args:
        scheduler: The scheduler instance
        config: ScheduleConfig instance with scheduling details
    """
    if not config.active:
        logger.info(f"Skipping inactive schedule for {config.lottery_type}")
        return
    
    # Create job ID
    job_id = f"lottery_task_{config.id}"
    
    # Remove any existing job with this ID
    if scheduler.get_job(job_id):
        scheduler.remove_job(job_id)
    
    # Schedule the task
    trigger = CronTrigger(hour=config.hour, minute=config.minute)
    
    scheduler.add_job(
        func=run_lottery_task,
        trigger=trigger,
        args=[config.url, config.lottery_type],
        id=job_id,
        name=f"Capture {config.lottery_type}",
        replace_existing=True
    )
    
    logger.info(f"Scheduled {config.lottery_type} task to run at {config.hour:02d}:{config.minute:02d}")

def remove_task(scheduler, config_id):
    """
    Remove a scheduled task.
    
    Args:
        scheduler: The scheduler instance
        config_id: ID of the ScheduleConfig
    """
    job_id = f"lottery_task_{config_id}"
    
    if scheduler.get_job(job_id):
        scheduler.remove_job(job_id)
        logger.info(f"Removed scheduled task with ID {job_id}")

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
        logger.info(f"Running scheduled task for {lottery_type}")
        
        # Step 1: Capture screenshot
        screenshot_path = capture_screenshot(url, lottery_type)
        if not screenshot_path:
            logger.error(f"Failed to capture screenshot for {lottery_type}")
            return
        
        # Step 2: Process screenshot with OCR
        extracted_data = process_screenshot(screenshot_path, lottery_type)
        if not extracted_data:
            logger.error(f"Failed to extract data from screenshot for {lottery_type}")
            return
        
        # Step 3: Aggregate data
        aggregate_data(extracted_data, lottery_type, url)
        
        logger.info(f"Successfully completed task for {lottery_type}")
    
    except Exception as e:
        logger.error(f"Error running lottery task: {str(e)}")
