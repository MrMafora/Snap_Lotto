"""
Integrate screenshot validation into the main application scheduler.

This script:
1. Loads the scheduled_screenshot_validation module
2. Connects it to the main application's scheduler
3. Configures it to run after screenshot capture
"""
import logging
import sys
from datetime import datetime, timedelta
from apscheduler.triggers.cron import CronTrigger
from scheduled_screenshot_validation import validate_all_screenshots
from main import app, scheduler

# Set up logging
logging.basicConfig(level=logging.INFO,
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                   stream=sys.stdout)
logger = logging.getLogger("integrate_validation")

def integrate_validation():
    """Integrate screenshot validation into main scheduler"""
    logger.info("Integrating screenshot validation into main scheduler")
    
    with app.app_context():
        # Add validation job to run 1 hour after screenshots are captured
        scheduler.add_job(
            validate_all_screenshots,
            CronTrigger(hour=3, minute=0),  # 3 AM SAST
            id='screenshot_validation',
            replace_existing=True
        )
        
        # Also run validation once at startup (with a small delay)
        scheduler.add_job(
            validate_all_screenshots,
            'date',
            run_date=datetime.now() + timedelta(seconds=30),
            id='immediate_validation'
        )
        
        logger.info("Screenshot validation scheduled to run daily at 3:00 AM SAST")
        logger.info("Initial validation will run in 30 seconds")
    
    return True

if __name__ == "__main__":
    integrate_validation()