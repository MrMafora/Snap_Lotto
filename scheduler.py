"""
Scheduler for automating lottery data scraping
"""
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from flask import current_app
import logging
import atexit
import threading
import time
import os

# Import screenshot manager factory to dynamically select implementation
from screenshot_manager_light import get_screenshot_manager
from ocr_processor import process_screenshot
from data_aggregator import aggregate_data
from models import db, ScheduleConfig

logger = logging.getLogger(__name__)

# Thread semaphore to limit concurrent lottery tasks
# This prevents "can't start new thread" errors
MAX_CONCURRENT_TASKS = 2
task_semaphore = threading.Semaphore(MAX_CONCURRENT_TASKS)

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
    import threading
    
    def task_thread():
        """Run the task in a separate thread to avoid blocking"""
        # Acquire semaphore to limit concurrent tasks
        # This prevents "can't start new thread" errors
        if not task_semaphore.acquire(blocking=True, timeout=300):
            logger.error(f"Could not acquire task semaphore for {lottery_type} after waiting 5 minutes")
            return False
        
        try:
            # Import here to avoid circular imports
            from flask import current_app
            from app import app
            from datetime import datetime
            
            logger.info(f"Starting lottery task for {lottery_type}")
            
            # Ensure we have an application context for all database operations
            with app.app_context():
                # Step 1: Create screenshot manager and take screenshot
                logger.info(f"Taking screenshot of {url} for {lottery_type}")
                screenshot_dir = os.path.join(os.getcwd(), 'screenshots')
                
                # Use the lightweight manager by default (much smaller footprint)
                # Only use Playwright if specifically configured to do so
                use_playwright = os.environ.get('USE_PLAYWRIGHT', '').lower() == 'true'
                screenshot_manager = get_screenshot_manager(use_playwright=use_playwright, 
                                                           screenshot_dir=screenshot_dir)
                
                # Take the screenshot
                result = screenshot_manager.take_screenshot(url, lottery_type)
                
                # Check if screenshot was successful
                if result['status'] != 'success':
                    logger.error(f"Failed to capture screenshot for {lottery_type}: {result['message']}")
                    return False
                
                # Get the screenshot path
                filepath = result.get('path')
                html_path = result.get('html_path')
                
                if not filepath:
                    logger.error(f"No screenshot path returned for {lottery_type}")
                    return False
                
                logger.info(f"Screenshot captured successfully for {lottery_type} at {filepath}")
                
                # Step 2: Process the screenshot with OCR
                logger.info(f"Processing screenshot with OCR for {lottery_type}")
                extracted_data = process_screenshot(filepath, lottery_type)
                
                if not extracted_data:
                    logger.error(f"OCR processing failed for {lottery_type}")
                    return False
                    
                # Step 3: Aggregate and store the data
                logger.info(f"Aggregating data for {lottery_type}")
                saved_results = aggregate_data(extracted_data, lottery_type, url)
                
                if saved_results:
                    logger.info(f"Successfully saved {len(saved_results)} result(s) for {lottery_type}")
                else:
                    logger.warning(f"No new lottery results saved for {lottery_type}")
                
                # Update last run time
                config = ScheduleConfig.query.filter_by(url=url).first()
                if config:
                    config.last_run = datetime.now()
                    db.session.commit()
                    logger.info(f"Updated last run time for {lottery_type}")
                
                # Step 4: Clean up old screenshots to save space
                try:
                    # Simple cleanup - remove files older than 7 days
                    logger.info("Cleaning up old screenshots")
                    now = time.time()
                    for root, dirs, files in os.walk(screenshot_dir):
                        for file in files:
                            file_path = os.path.join(root, file)
                            # If file is older than 7 days, delete it
                            if os.stat(file_path).st_mtime < now - 7 * 86400:
                                os.remove(file_path)
                                logger.debug(f"Removed old file: {file_path}")
                except Exception as e:
                    logger.error(f"Error during cleanup: {str(e)}")
                    # Continue even if cleanup fails
                
                return True
                
        except Exception as e:
            logger.error(f"Error in lottery task for {lottery_type}: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
            return False
        finally:
            # Always release the semaphore in the finally block
            # to ensure it's released even if an exception occurs
            task_semaphore.release()
            logger.debug(f"Released task semaphore for {lottery_type}")
    
    # Start the task in a separate thread to avoid blocking the scheduler
    try:
        thread = threading.Thread(target=task_thread)
        thread.daemon = True
        thread.start()
        return True
    except RuntimeError as e:
        # Handle "can't start new thread" error gracefully
        logger.error(f"Failed to start thread for {lottery_type}: {str(e)}")
        return False
