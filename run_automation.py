#!/usr/bin/env python3
"""
Direct automation script to update lottery database with latest results
"""
import os
import sys
import logging
from datetime import datetime

# Add the current directory to Python path
sys.path.insert(0, os.getcwd())

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def run_complete_automation():
    """Run the complete automation workflow to update database with latest lottery results"""
    try:
        logger.info("Starting complete lottery automation workflow...")
        
        # Step 1: Clear old screenshots
        logger.info("Step 1: Clearing old screenshots...")
        try:
            from daily_automation import DailyLotteryAutomation
            from main import app
            
            automation = DailyLotteryAutomation(app)
            success, count = automation.cleanup_old_screenshots()
            logger.info(f"Cleanup result: Success={success}, Files removed={count}")
        except Exception as e:
            logger.warning(f"Step 1 cleanup failed: {e}")
        
        # Step 2: Capture fresh screenshots
        logger.info("Step 2: Capturing fresh lottery screenshots...")
        try:
            from step2_capture import capture_lottery_screenshots
            success, count = capture_lottery_screenshots()
            logger.info(f"Screenshot capture: Success={success}, Screenshots={count}")
        except Exception as e:
            logger.warning(f"Step 2 capture failed: {e}")
        
        # Step 3: Process with AI
        logger.info("Step 3: Processing screenshots with Gemini AI...")
        try:
            from step3_ai_process import process_screenshots_with_ai
            success, count = process_screenshots_with_ai()
            logger.info(f"AI processing: Success={success}, Processed={count}")
        except Exception as e:
            logger.warning(f"Step 3 AI processing failed: {e}")
        
        # Step 4: Update database
        logger.info("Step 4: Updating database with extracted results...")
        try:
            from step4_database import update_database
            success, count = update_database()
            logger.info(f"Database update: Success={success}, Records={count}")
        except Exception as e:
            logger.warning(f"Step 4 database update failed: {e}")
        
        logger.info("Complete automation workflow finished.")
        return True
        
    except Exception as e:
        logger.error(f"Complete automation failed: {e}")
        return False

if __name__ == "__main__":
    run_complete_automation()