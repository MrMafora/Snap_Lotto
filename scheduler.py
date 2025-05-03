"""
Scheduler for automating lottery data scraping
"""
import atexit
import threading
import time
import logging
import os

# Set up module-specific logger
logger = logging.getLogger(__name__)
if not logger.handlers:
    # Create logs directory if it doesn't exist
    logs_dir = os.path.join(os.getcwd(), 'logs')
    if not os.path.exists(logs_dir):
        os.makedirs(logs_dir)
    
    # Set up file handler
    file_handler = logging.FileHandler(os.path.join(logs_dir, 'scheduler.log'))
    file_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
    logger.addHandler(file_handler)
    
    # Set up console handler
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
    logger.addHandler(console_handler)
    
    # Set logging level
    logger.setLevel(logging.INFO)

# Flag to indicate if we're in Replit environment
# Used to optimize startup for Replit workflows
IS_REPLIT_ENV = True

# Thread semaphore to limit concurrent lottery tasks
# This prevents "can't start new thread" errors
MAX_CONCURRENT_TASKS = 2
task_semaphore = threading.Semaphore(MAX_CONCURRENT_TASKS)

# Scheduler instance (initialized later)
scheduler = None

def init_scheduler(app):
    """
    Initialize the APScheduler for scheduled tasks.
    
    Args:
        app (Flask): Flask application instance
        
    Returns:
        BackgroundScheduler: Initialized scheduler
    """
    global scheduler
    
    # Import heavy modules only when needed
    from apscheduler.schedulers.background import BackgroundScheduler
    
    # Initialize scheduler but don't start it yet
    scheduler = BackgroundScheduler()
    
    # In Replit environment, delay scheduler startup to allow port detection
    if IS_REPLIT_ENV:
        # Start scheduler in a separate thread after a delay
        # to ensure app is ready on port 5000 first
        def delayed_start():
            logger.info("Delaying scheduler startup for faster application initialization")
            time.sleep(5)  # Longer wait to ensure port 5000 is detected first
            scheduler.start()
            logger.info("Scheduler started after delay")
            
        # Start the delayed initialization in a background thread
        threading.Thread(target=delayed_start, daemon=True).start()
    else:
        # In non-Replit environments, start immediately
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
        # Import here to avoid early loading
        from apscheduler.triggers.cron import CronTrigger
        
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
            import screenshot_manager as sm  # Import as module to avoid name conflicts
            from ocr_processor import process_screenshot
            from data_aggregator import aggregate_data
            from datetime import datetime
            
            logger.info(f"Starting lottery task for {lottery_type}")
            
            # Ensure we have an application context for all database operations
            with app.app_context():
                # Step 1: Capture screenshot directly using the sm module
                capture_result = sm.capture_screenshot(url, lottery_type)
                
                # Check if the capture was successful
                # Zoom functionality has been removed - capture_result is now just a filepath
                if not capture_result:
                    logger.error(f"Failed to capture screenshot for {lottery_type}")
                    return False
                    
                # Assign the filepath
                filepath = capture_result
                
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
                # Import models here to avoid circular imports
                from models import ScheduleConfig, db
                
                config = ScheduleConfig.query.filter_by(url=url).first()
                if config:
                    config.last_run = datetime.now()
                    db.session.commit()
                    logger.info(f"Updated last run time for {lottery_type}")
                
                # Step 4: Clean up old screenshots to save space
                try:
                    # Use our local implementation
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

def cleanup_old_screenshots():
    """
    Cleanup old screenshots, keeping only the latest screenshot for each URL.
    
    Returns:
        int: Number of deleted screenshots
    """
    from models import Screenshot, db
    from datetime import datetime
    import os
    import logging
    
    logger.info("Starting cleanup of old screenshots")
    
    try:
        # Get all screenshots grouped by lottery type
        lottery_types = db.session.query(Screenshot.lottery_type).distinct().all()
        deleted_count = 0
        
        for lottery_type_row in lottery_types:
            lottery_type = lottery_type_row[0]
            logger.info(f"Cleaning up screenshots for {lottery_type}")
            
            # Get all screenshots for this lottery type, ordered by timestamp descending
            screenshots = Screenshot.query.filter_by(lottery_type=lottery_type).order_by(Screenshot.timestamp.desc()).all()
            
            # Keep the most recent one, delete the rest
            if len(screenshots) > 1:
                for screenshot in screenshots[1:]:
                    logger.info(f"Deleting old screenshot {screenshot.id} from {screenshot.timestamp}")
                    
                    # Delete the file
                    if screenshot.path and os.path.exists(screenshot.path):
                        try:
                            os.remove(screenshot.path)
                            logger.info(f"Deleted file: {screenshot.path}")
                        except Exception as e:
                            logger.error(f"Error deleting file {screenshot.path}: {str(e)}")
                    
                    # Zoom functionality has been removed
                    
                    # Delete the database record
                    db.session.delete(screenshot)
                    deleted_count += 1
                
                # Commit after processing each lottery type
                db.session.commit()
        
        logger.info(f"Cleanup completed. Deleted {deleted_count} old screenshots.")
        return deleted_count
    except Exception as e:
        logger.error(f"Error cleaning up screenshots: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        db.session.rollback()
        return 0

def retake_screenshot_by_id(screenshot_id, app=None):
    """
    Retake a specific screenshot by its ID.
    
    Args:
        screenshot_id (int): Database ID of the screenshot
        app (Flask): Flask application instance (optional)
        
    Returns:
        bool: Success status
    """
    from models import Screenshot, db
    from flask import current_app
    import traceback
    
    try:
        # Import here to avoid circular imports
        if app is None:
            from main import app
            
        with app.app_context():
            # Get the screenshot from the database
            screenshot = Screenshot.query.get(screenshot_id)
            
            if not screenshot:
                logger.error(f"Screenshot with ID {screenshot_id} not found")
                return False
                
            logger.info(f"Retaking screenshot for {screenshot.lottery_type} from {screenshot.url}")
            
            # Import screenshot manager inside the thread to avoid circular imports
            import screenshot_manager as sm
            
            # Capture new screenshot with the same URL and lottery type
            # Capture screenshot (with zoom functionality removed, returns only filepath)
            filepath = sm.capture_screenshot(screenshot.url, screenshot.lottery_type)
            
            if not filepath:
                logger.error(f"Failed to retake screenshot for {screenshot.lottery_type}")
                return False
            
            # Update the existing screenshot record with new path
            screenshot.path = filepath
            # No longer using zoomed_path since zoom functionality has been removed
            screenshot.timestamp = db.func.now()  # Update timestamp
            db.session.commit()
            
            logger.info(f"Successfully retook screenshot for {screenshot.lottery_type}")
            return True
                
    except Exception as e:
        logger.error(f"Error retaking screenshot: {str(e)}")
        logger.error(traceback.format_exc())
        if 'db' in locals():
            db.session.rollback()
        return False

def retake_all_screenshots(app=None, use_threading=True):
    """
    Retake screenshots for all configured URLs.
    This function will call screenshot_manager.retake_all_screenshots to handle the screenshot process.
    
    Args:
        app (Flask): Flask application instance (optional)
        use_threading (bool): Whether to use threading for parallel processing
        
    Returns:
        int: Number of successfully captured screenshots
    """
    try:
        # Import screenshot manager here to avoid circular imports
        import screenshot_manager as sm
        
        # Call the screenshot manager's implementation
        logger.info("Delegating screenshot capture to screenshot_manager.retake_all_screenshots")
        result = sm.retake_all_screenshots(app, use_threading=use_threading)
        
        # Return the count of screenshots taken
        return result
    except Exception as e:
        logger.error(f"Error in scheduler.retake_all_screenshots: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return 0
