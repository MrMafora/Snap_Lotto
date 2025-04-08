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
        # Use a subprocess to avoid Playwright issues with Gunicorn
        import subprocess
        import tempfile
        import os
        import json
        import time
        
        logger.info(f"Starting lottery task for {lottery_type}")
        
        # Step 1: Capture screenshot
        # Create a temporary script to run in a separate process
        script = f"""
import os
import sys
import json
import time
import traceback

# Configure the path for imports
sys.path.insert(0, os.getcwd())

# Wait a second for any previous tasks to finish
time.sleep(1)

# Import the screenshot function
from screenshot_manager import capture_screenshot_sync

try:
    # Capture the screenshot
    print("Starting screenshot capture for {lottery_type}")
    filepath, _ = capture_screenshot_sync("{url}")
    
    # Save the result
    if filepath:
        print(f"Screenshot captured: {{filepath}}")
        print("SUCCESS:" + filepath)
        sys.exit(0)
    else:
        print("Failed to capture screenshot")
        sys.exit(1)
except Exception as e:
    print(f"Error capturing screenshot: {{str(e)}}")
    traceback.print_exc()
    sys.exit(1)
"""
        
        # Create a temporary file for the script
        with tempfile.NamedTemporaryFile(suffix='.py', delete=False) as f:
            script_path = f.name
            f.write(script.encode('utf-8'))
        
        try:
            # Run the script as a separate process
            logger.info(f"Running screenshot script for {lottery_type}")
            process = subprocess.Popen(
                ['python', script_path],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                universal_newlines=True
            )
            
            # Set a timeout (30 seconds)
            timeout = 30
            filepath = None
            
            # Wait for the process to complete or timeout
            for i in range(timeout):
                if process.poll() is not None:
                    # Process completed
                    stdout, stderr = process.communicate()
                    
                    # Check if successful
                    for line in stdout.splitlines():
                        if line.startswith("SUCCESS:"):
                            filepath = line[8:]  # Remove "SUCCESS:" prefix
                            logger.info(f"Screenshot captured: {filepath}")
                            break
                    
                    if stderr:
                        logger.error(f"Screenshot stderr: {stderr}")
                    
                    break
                
                time.sleep(1)
            
            # Kill the process if it's still running
            if process.poll() is None:
                process.kill()
                logger.error(f"Screenshot process timed out for {lottery_type}")
            
            # Clean up the temporary script
            os.unlink(script_path)
            
            # Continue with OCR if we have a screenshot
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
                    
                    logger.info(f"Task completed successfully for {lottery_type}")
                    return True
                else:
                    logger.warning(f"No data extracted for {lottery_type}")
                    return False
            else:
                logger.error(f"Failed to capture screenshot for {lottery_type}")
                return False
                
        except Exception as e:
            logger.error(f"Error in script execution: {str(e)}")
            # Clean up the temporary script
            if os.path.exists(script_path):
                os.unlink(script_path)
            return False
            
    except Exception as e:
        logger.error(f"Error running lottery task: {str(e)}")
        return False
