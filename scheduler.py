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

def capture_next_missing_url_job():
    """
    Scheduled job to capture the next missing URL.
    This is run hourly to gradually build up our collection without timing out.
    Uses specialized National Lottery capture with advanced anti-bot measures.
    Uses the enhanced capture_single_url.py script with proper timeout handling.
    """
    try:
        import subprocess
        import random
        import sys
        
        # Add a small random delay to avoid predictable patterns
        delay = random.randint(1, 300)  # 1-300 seconds (up to 5 minutes)
        logger.info(f"Delaying next URL capture by {delay} seconds")
        time.sleep(delay)
        
        # Get the next missing URL
        logger.info("Getting next missing URL")
        
        # First get the next missing URL
        app_context = None
        try:
            from flask import current_app
            if not current_app:
                from main import app
                app_context = app.app_context()
                app_context.push()
        except:
            pass
        
        # Import here to avoid circular dependencies
        from capture_next_missing import get_next_missing_url
        url, lottery_type = get_next_missing_url()
        
        if app_context:
            app_context.pop()
        
        if not url or not lottery_type:
            logger.info("No missing URLs to capture at this time")
            return
        
        logger.info(f"Capturing {lottery_type} from {url}")
        
        # Use the enhanced capture_single_url.py script with timeout
        # Command to run the capture script with a 5-minute timeout
        cmd = [
            sys.executable,
            "capture_single_url.py",
            "--url", url,
            "--timeout", "300"  # 5 minutes
        ]
        
        if lottery_type:
            cmd.extend(["--lottery-type", lottery_type])
        
        # Run the capture script
        try:
            logger.info(f"Running command: {' '.join(cmd)}")
            result = subprocess.run(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                timeout=360  # 6 minute overall timeout
            )
            
            if result.returncode == 0:
                logger.info(f"Successfully captured {lottery_type} from {url}")
                logger.debug(f"Output: {result.stdout}")
                return
            else:
                logger.error(f"Failed to capture {lottery_type} from {url}")
                logger.error(f"Error: {result.stderr}")
        except subprocess.TimeoutExpired:
            logger.error(f"Capture process timed out for {lottery_type} from {url}")
        
        # Try with legacy Playwright mode as first fallback
        logger.info("Trying again with legacy Playwright mode")
        result = subprocess.run(
            ["python", "capture_next_missing.py", "--use-legacy"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=600  # 10 minute timeout
        )
        
        if result.returncode == 0:
            logger.info("Successfully captured next missing URL with legacy Playwright")
        else:
            logger.error(f"Failed to capture next missing URL with legacy Playwright. Exit code: {result.returncode}")
            logger.error(f"Error: {result.stderr}")
            
            # Try with simple requests method as final fallback
            logger.info("Trying simple requests-based capture as final fallback")
            try:
                # Import the specialized capture function
                from national_lottery_capture import capture_national_lottery_url
                
                success, html_path, _ = capture_national_lottery_url(url, lottery_type)
                
                if success:
                    logger.info(f"Successfully captured {lottery_type} from {url} with simple requests method")
                else:
                    logger.error(f"Failed to capture {lottery_type} from {url} with all methods")
            except Exception as e:
                logger.error(f"Error in requests fallback: {str(e)}")
                logger.error(f"Failed to capture {lottery_type} from {url} with all available methods")
    except subprocess.TimeoutExpired:
        logger.error("Timeout expired when capturing next missing URL")
    except Exception as e:
        logger.error(f"Error in capture_next_missing_url_job: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())

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
    from apscheduler.triggers.cron import CronTrigger
    from apscheduler.triggers.interval import IntervalTrigger
    
    # Initialize scheduler but don't start it yet
    scheduler = BackgroundScheduler()
    
    # Add daily screenshot cleanup job (runs at 4:00 AM SAST)
    # This ensures we keep our storage clean and organized
    scheduler.add_job(
        func=run_screenshot_cleanup,
        trigger=CronTrigger(hour=4, minute=0),  # 4:00 AM
        args=[app],
        id="daily_screenshot_cleanup",
        replace_existing=True
    )
    logger.info("Added daily screenshot cleanup job (runs at 4:00 AM SAST)")
    
    # Add hourly job to capture the next missing URL
    # This will gradually build up our collection over time
    scheduler.add_job(
        func=capture_next_missing_url_job,
        trigger=IntervalTrigger(hours=1),  # Run every hour
        id="hourly_url_capture",
        replace_existing=True
    )
    logger.info("Added hourly URL capture job (runs every hour)")
    
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
                # Step 1: Try to capture screenshot using specialized National Lottery capture
                try:
                    from national_lottery_capture import capture_national_lottery_url, normalize_lottery_type
                    
                    # Normalize the lottery type from the URL
                    normalized_type = normalize_lottery_type(url)
                    
                    # Log the normalization for debugging
                    if normalized_type != lottery_type:
                        logger.info(f"Normalized lottery type from '{lottery_type}' to '{normalized_type}'")
                        lottery_type = normalized_type
                    
                    logger.info(f"Attempting specialized National Lottery capture for {lottery_type}")
                    success, html_path, img_path = capture_national_lottery_url(url, lottery_type, save_to_db=True)
                    
                    if success and html_path:
                        logger.info(f"Specialized National Lottery capture successful for {lottery_type}")
                        filepath = html_path
                    else:
                        # Fall back to standard capture if specialized capture fails
                        logger.warning(f"Specialized National Lottery capture failed for {lottery_type}, falling back to standard capture")
                        capture_result = sm.capture_screenshot(url, lottery_type)
                        if not capture_result:
                            logger.error(f"Standard capture also failed for {lottery_type}")
                            return False
                        filepath = capture_result
                except Exception as e:
                    # If specialized capture throws an exception, fall back to standard capture
                    logger.error(f"Error in specialized capture for {lottery_type}: {str(e)}")
                    logger.warning(f"Falling back to standard capture for {lottery_type}")
                    capture_result = sm.capture_screenshot(url, lottery_type)
                    if not capture_result:
                        logger.error(f"Standard capture also failed for {lottery_type}")
                        return False
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
            
            # Try to use specialized National Lottery capture first
            try:
                from national_lottery_capture import capture_national_lottery_url, normalize_lottery_type
                
                # Normalize the lottery type from the URL
                normalized_type = normalize_lottery_type(screenshot.url)
                
                # Log the normalization for debugging
                if normalized_type != screenshot.lottery_type:
                    logger.info(f"Normalized lottery type from '{screenshot.lottery_type}' to '{normalized_type}'")
                    screenshot.lottery_type = normalized_type
                
                logger.info(f"Attempting specialized National Lottery capture for retake of {screenshot.lottery_type}")
                success, html_path, img_path = capture_national_lottery_url(
                    screenshot.url, screenshot.lottery_type, save_to_db=False)
                
                if success and html_path:
                    logger.info(f"Specialized National Lottery capture successful for retake of {screenshot.lottery_type}")
                    filepath = html_path
                else:
                    # Fall back to standard capture
                    logger.warning(f"Specialized capture failed for retake, falling back to standard capture")
                    # Import screenshot manager inside the thread to avoid circular imports
                    import screenshot_manager as sm
                    filepath = sm.capture_screenshot(screenshot.url, screenshot.lottery_type)
            except Exception as e:
                # Fall back to standard capture
                logger.error(f"Error in specialized capture for retake: {str(e)}")
                # Import screenshot manager inside the thread to avoid circular imports
                import screenshot_manager as sm
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

def retake_all_screenshots(app=None, use_threading=True, use_specialized_capture=True):
    """
    Retake screenshots for all configured URLs.
    By default, uses the specialized National Lottery capture function.
    
    Args:
        app (Flask): Flask application instance (optional)
        use_threading (bool): Whether to use threading for parallel processing
        use_specialized_capture (bool): Whether to use specialized National Lottery capture
        
    Returns:
        int: Number of successfully captured screenshots
    """
    try:
        # Create application context if not provided
        if app is None:
            from main import app
            
        with app.app_context():
            # Import models
            from models import db, ScheduleConfig
            
            # Get all active schedule configs
            configs = ScheduleConfig.query.filter_by(active=True).all()
            logger.info(f"Found {len(configs)} active schedule configurations to retake")
            
            success_count = 0
            
            # Process configs sequentially or with threading
            if use_threading:
                import threading
                import queue
                
                # Define a task queue
                task_queue = queue.Queue()
                for config in configs:
                    task_queue.put((config.url, config.lottery_type))
                
                # Define the worker function
                def worker():
                    nonlocal success_count
                    while not task_queue.empty():
                        try:
                            url, lottery_type = task_queue.get(block=False)
                            logger.info(f"Worker processing {lottery_type} from {url}")
                            
                            # Use the appropriate capture method
                            if use_specialized_capture:
                                try:
                                    from national_lottery_capture import capture_national_lottery_url
                                    success, _, _ = capture_national_lottery_url(url, lottery_type)
                                    if success:
                                        success_count += 1
                                except Exception as e:
                                    logger.error(f"Error in specialized capture for {lottery_type}: {str(e)}")
                                    # Fall back to standard capture on failure
                                    import screenshot_manager as sm
                                    if sm.capture_screenshot(url, lottery_type):
                                        success_count += 1
                            else:
                                # Use standard capture
                                import screenshot_manager as sm
                                if sm.capture_screenshot(url, lottery_type):
                                    success_count += 1
                            
                            task_queue.task_done()
                        except queue.Empty:
                            break
                        except Exception as e:
                            logger.error(f"Error in worker thread: {str(e)}")
                            task_queue.task_done()
                
                # Create and start worker threads (limit to a reasonable number)
                thread_count = min(4, len(configs))
                threads = []
                for _ in range(thread_count):
                    thread = threading.Thread(target=worker)
                    thread.daemon = True
                    thread.start()
                    threads.append(thread)
                
                # Wait for all tasks to complete
                for thread in threads:
                    thread.join()
                
            else:
                # Process configs sequentially
                for config in configs:
                    url = config.url
                    lottery_type = config.lottery_type
                    logger.info(f"Processing {lottery_type} from {url}")
                    
                    # Use the appropriate capture method
                    if use_specialized_capture:
                        try:
                            from national_lottery_capture import capture_national_lottery_url
                            success, _, _ = capture_national_lottery_url(url, lottery_type)
                            if success:
                                success_count += 1
                            else:
                                # Fall back to standard capture on failure
                                import screenshot_manager as sm
                                if sm.capture_screenshot(url, lottery_type):
                                    success_count += 1
                        except Exception as e:
                            logger.error(f"Error in specialized capture for {lottery_type}: {str(e)}")
                            # Fall back to standard capture on failure
                            import screenshot_manager as sm
                            if sm.capture_screenshot(url, lottery_type):
                                success_count += 1
                    else:
                        # Use standard capture
                        import screenshot_manager as sm
                        if sm.capture_screenshot(url, lottery_type):
                            success_count += 1
            
            logger.info(f"Successfully retook {success_count} out of {len(configs)} screenshots")
            return success_count
    except Exception as e:
        logger.error(f"Error in scheduler.retake_all_screenshots: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return 0

def run_screenshot_cleanup(app=None):
    """
    Run the screenshot cleanup process to remove old screenshots.
    This helps maintain disk space by keeping only the latest screenshots.
    
    Args:
        app (Flask): Flask application instance (optional)
        
    Returns:
        bool: True if cleanup was successful, False otherwise
    """
    try:
        # Import screenshot manager here to avoid circular imports
        import screenshot_manager as sm
        
        logger.info("Starting scheduled screenshot cleanup from scheduler")
        
        # If no app context is provided but we need one
        if app is None:
            # Import Flask app (handle circular imports)
            from flask import current_app
            
            if not current_app:
                from main import app
                app_context = app.app_context()
                app_context.push()
                created_context = True
            else:
                created_context = False
        else:
            app_context = app.app_context()
            app_context.push()
            created_context = True
            
        try:
            # Execute the cleanup function
            sm.cleanup_old_screenshots()
            logger.info("Scheduled screenshot cleanup completed successfully")
            return True
        finally:
            # Only pop the context if we created it
            if app is not None and created_context:
                app_context.pop()
                
    except Exception as e:
        logger.error(f"Error in scheduler.run_screenshot_cleanup: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return False
