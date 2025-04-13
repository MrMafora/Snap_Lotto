"""
Scheduler for automating lottery data scraping
"""
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from flask import current_app
import atexit
import threading
import time

from screenshot_manager import capture_screenshot
from ocr_processor import process_screenshot
from data_aggregator import aggregate_data
from models import db, ScheduleConfig
from logger import setup_logger

# Set up module-specific logger
logger = setup_logger(__name__)

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
            from main import app
            
            # Get all the required functions
            from screenshot_manager import capture_screenshot, cleanup_old_screenshots
            from ocr_processor import process_screenshot
            from data_aggregator import aggregate_data
            from datetime import datetime
            
            logger.info(f"Starting lottery task for {lottery_type}")
            
            # Ensure we have an application context for all database operations
            with app.app_context():
                # Step 1: Capture screenshot directly
                capture_result = capture_screenshot(url, lottery_type)
                
                # Unpack the values - either we get (filepath, screenshot_data, zoom_filepath)
                # or we get None if the capture failed
                if not capture_result:
                    logger.error(f"Failed to capture screenshot for {lottery_type}")
                    return False
                    
                # Unpack the result
                filepath, screenshot_data, zoom_filepath = capture_result
                
                # Only proceed if we have a valid screenshot filepath
                if not filepath:
                    logger.error(f"Failed to capture screenshot for {lottery_type}")
                    return False
                
                logger.info(f"Screenshot captured successfully for {lottery_type}")
                    
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
                    cleanup_old_screenshots()
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

def retake_all_screenshots():
    """
    Retake screenshots for all configured URLs.
    This function will capture new screenshots for all URLs in the ScheduleConfig table.
    Old screenshots will be deleted through the normal cleanup process.
    
    Returns:
        dict: A dictionary containing success/failure status for each URL
    """
    import threading
    from models import ScheduleConfig
    from flask import current_app
    from main import app
    
    # Dictionary to store results
    results = {}
    processed_urls = set()
    
    def process_url(url, lottery_type):
        """Process a single URL in a separate thread"""
        # Acquire semaphore to limit concurrent tasks
        if not task_semaphore.acquire(blocking=True, timeout=300):
            results[url] = {
                'status': 'error',
                'message': f"Could not acquire task semaphore for {lottery_type} after waiting 5 minutes"
            }
            return
        
        try:
            logger.info(f"Retaking screenshot for {lottery_type} from {url}")
            
            # Import screenshot manager inside the thread to avoid circular imports
            from screenshot_manager import capture_screenshot
            
            with app.app_context():
                # Capture new screenshot
                capture_result = capture_screenshot(url, lottery_type)
                
                if not capture_result:
                    results[url] = {
                        'status': 'error',
                        'message': f"Failed to capture screenshot for {lottery_type}"
                    }
                    return
                
                filepath, _, zoom_filepath = capture_result
                
                results[url] = {
                    'status': 'success',
                    'lottery_type': lottery_type,
                    'filepath': filepath,
                    'zoom_filepath': zoom_filepath
                }
                
                logger.info(f"Successfully retook screenshot for {lottery_type}")
        except Exception as e:
            logger.error(f"Error retaking screenshot for {lottery_type}: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
            
            results[url] = {
                'status': 'error',
                'message': str(e)
            }
        finally:
            # Always release the semaphore
            task_semaphore.release()
    
    try:
        with app.app_context():
            # Get all unique URLs from ScheduleConfig
            configs = ScheduleConfig.query.all()
            threads = []
            
            for config in configs:
                # Skip duplicate URLs to avoid redundant work
                if config.url in processed_urls:
                    continue
                
                processed_urls.add(config.url)
                
                # Start a new thread for each URL
                thread = threading.Thread(target=process_url, args=(config.url, config.lottery_type))
                thread.daemon = True
                thread.start()
                threads.append(thread)
            
            # Wait for all threads to complete
            for thread in threads:
                thread.join(timeout=60)  # Wait up to 60 seconds per thread
            
            # Run cleanup to remove old screenshots
            from screenshot_manager import cleanup_old_screenshots
            cleanup_old_screenshots()
            
            return results
    except Exception as e:
        logger.error(f"Error in retake_all_screenshots: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return {'status': 'error', 'message': str(e)}
