#!/usr/bin/env python
"""
Script to purge all data from the lottery database while preserving the schema.
This is used to start fresh with new data from the updated OCR system.
"""

import os
import sys
import logging
from datetime import datetime
from main import app
from models import db, LotteryResult, Screenshot, ScheduleConfig

# Set up logging
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def purge_data():
    """
    Purge all data from the lottery database tables while preserving the schema.
    """
    try:
        with app.app_context():
            # Count records before deletion for reporting
            screenshot_count = Screenshot.query.count()
            result_count = LotteryResult.query.count()
            schedule_count = ScheduleConfig.query.count()
            
            logger.info(f"Starting purge operation...")
            logger.info(f"Found {screenshot_count} screenshots")
            logger.info(f"Found {result_count} lottery results")
            logger.info(f"Found {schedule_count} schedule configurations")
            
            # Auto-confirm for this environment
            logger.info(f"Automatically confirming purge of {screenshot_count} screenshots and {result_count} results.")
            confirm = "CONFIRM"
            
            # Delete data from tables
            LotteryResult.query.delete()
            Screenshot.query.delete()
            
            # Do NOT delete schedule configurations - we want to keep them
            # ScheduleConfig.query.delete()
            
            # Commit the changes
            db.session.commit()
            
            # Verify deletion
            new_screenshot_count = Screenshot.query.count()
            new_result_count = LotteryResult.query.count()
            new_schedule_count = ScheduleConfig.query.count()
            
            logger.info("Purge complete!")
            logger.info(f"Screenshots: {screenshot_count} -> {new_screenshot_count}")
            logger.info(f"Lottery Results: {result_count} -> {new_result_count}")
            logger.info(f"Schedule Configs: {schedule_count} -> {new_schedule_count} (preserved)")
            
            # If any screenshots exist on disk, log the count but don't delete them
            screenshot_dir = os.environ.get('SCREENSHOT_DIR', os.path.join(os.getcwd(), 'screenshots'))
            if os.path.exists(screenshot_dir):
                screenshot_files = [f for f in os.listdir(screenshot_dir) if f.endswith('.png')]
                logger.info(f"Found {len(screenshot_files)} screenshot files on disk.")
                logger.info(f"NOTE: Screenshot files on disk were NOT deleted - the scheduler will reuse them.")
            
            return True
    except Exception as e:
        logger.error(f"Error during purge operation: {str(e)}")
        return False

if __name__ == "__main__":
    purge_data()