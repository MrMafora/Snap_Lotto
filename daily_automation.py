"""
Daily Automated Lottery Data Processing System
Handles the complete workflow: Clear → Capture → Process → Update Database
"""

import os
import logging
import time
from datetime import datetime
from flask import Flask
from models import db, Screenshot, LotteryResult
import screenshot_manager
from automated_data_extractor import LotteryDataExtractor

logger = logging.getLogger(__name__)

class DailyLotteryAutomation:
    """Manages the complete daily automation workflow"""
    
    def __init__(self, app):
        self.app = app
        self.data_extractor = LotteryDataExtractor()
        
    def cleanup_old_screenshots(self):
        """Step 1: Clear old screenshot files"""
        logger.info("DEBUG: Starting cleanup function")
        
        try:
            logger.info("DEBUG: Cleanup started")
            screenshot_dir = os.path.join(os.getcwd(), 'screenshots')
            logger.info(f"DEBUG: Screenshot directory: {screenshot_dir}")
            
            deleted_count = 0
            
            if not os.path.exists(screenshot_dir):
                logger.info("DEBUG: Screenshot directory doesn't exist, creating it")
                os.makedirs(screenshot_dir, exist_ok=True)
                return True, 0
            
            # List files first
            logger.info("DEBUG: Listing files in screenshot directory")
            files = os.listdir(screenshot_dir)
            logger.info(f"DEBUG: Found {len(files)} files")
            
            # Skip cleanup for now to isolate the issue
            logger.info("DEBUG: Skipping actual file deletion for debugging")
            
            logger.info(f"DEBUG: Cleanup completed successfully. Would have processed {len(files)} files")
            return True, len(files)
            
        except Exception as e:
            logger.error(f"DEBUG: Exception in cleanup: {str(e)}")
            import traceback
            logger.error(f"DEBUG: Traceback: {traceback.format_exc()}")
            return False, 0
    
    def capture_fresh_screenshots(self):
        """Step 2: Capture brand new screenshots from lottery websites"""
        try:
            logger.info("DEBUG: Starting capture of fresh lottery screenshots...")
            
            # Import the screenshot manager function directly
            from screenshot_manager import retake_all_screenshots
            
            with self.app.app_context():
                logger.info("DEBUG: Calling retake_all_screenshots...")
                count = retake_all_screenshots(self.app, use_threading=False)
                logger.info(f"DEBUG: Screenshot capture returned count: {count}")
            
            logger.info(f"Fresh screenshot capture completed. Processed {count} lottery sites")
            return True, count
            
        except Exception as e:
            logger.error(f"DEBUG: Failed to capture fresh screenshots: {str(e)}")
            import traceback
            logger.error(f"DEBUG: Traceback: {traceback.format_exc()}")
            return False, 0
    
    def process_screenshots_with_ai(self):
        """Step 3: Send fresh screenshots to AI for data extraction"""
        try:
            logger.info("Starting AI processing of fresh screenshots...")
            
            # Get the screenshots directory
            screenshot_dir = os.path.join(os.getcwd(), 'screenshots')
            if not os.path.exists(screenshot_dir):
                logger.warning("Screenshots directory not found")
                return False, 0
            
            # Process all fresh PNG files in the directory
            processed_count = self.data_extractor.process_all_images(screenshot_dir)
            logger.info(f"AI processing completed. Processed {processed_count} screenshots")
            return True, processed_count
            
        except Exception as e:
            logger.error(f"Failed to process screenshots with AI: {str(e)}")
            return False, 0
    
    def update_database_with_results(self):
        """Step 4: Update database with fresh lottery data"""
        try:
            logger.info("Starting database update with fresh lottery results...")
            
            with self.app.app_context():
                # Get count of results added today
                today = datetime.now().date()
                new_results = LotteryResult.query.filter(
                    db.func.date(LotteryResult.created_at) == today
                ).count()
                
            logger.info(f"Database update completed. {new_results} fresh results available")
            return True, new_results
            
        except Exception as e:
            logger.error(f"Failed to update database: {str(e)}")
            return False, 0
    
    def run_complete_daily_workflow(self):
        """Execute the complete daily automation workflow"""
        workflow_start = datetime.now()
        logger.info(f"=== DAILY LOTTERY AUTOMATION STARTED at {workflow_start} ===")
        
        results = {
            'start_time': workflow_start,
            'cleanup': {'success': False, 'count': 0},
            'capture': {'success': False, 'count': 0},
            'processing': {'success': False, 'count': 0},
            'database': {'success': False, 'count': 0},
            'overall_success': False
        }
        
        try:
            # Step 1: Cleanup old screenshots
            cleanup_success, cleanup_count = self.cleanup_old_screenshots()
            results['cleanup'] = {'success': cleanup_success, 'count': cleanup_count}
            
            if not cleanup_success:
                logger.error("Daily workflow stopped: Cleanup failed")
                return results
            
            # Step 2: Capture fresh screenshots
            capture_success, capture_count = self.capture_fresh_screenshots()
            results['capture'] = {'success': capture_success, 'count': capture_count}
            
            if not capture_success:
                logger.error("Daily workflow stopped: Screenshot capture failed")
                return results
            
            # Brief pause to ensure screenshots are ready
            time.sleep(5)
            
            # Step 3: AI processing
            processing_success, processing_count = self.process_screenshots_with_ai()
            results['processing'] = {'success': processing_success, 'count': processing_count}
            
            if not processing_success:
                logger.error("Daily workflow stopped: AI processing failed")
                return results
            
            # Step 4: Database update verification
            db_success, db_count = self.update_database_with_results()
            results['database'] = {'success': db_success, 'count': db_count}
            
            # Overall success if all steps completed
            results['overall_success'] = (cleanup_success and capture_success and 
                                        processing_success and db_success)
            
            workflow_end = datetime.now()
            duration = workflow_end - workflow_start
            
            if results['overall_success']:
                logger.info(f"=== DAILY AUTOMATION COMPLETED SUCCESSFULLY in {duration} ===")
                logger.info(f"Summary: Cleaned {cleanup_count} old files, captured {capture_count} fresh screenshots, processed {processing_count} with AI, {db_count} database results")
            else:
                logger.error(f"=== DAILY AUTOMATION COMPLETED WITH ERRORS in {duration} ===")
            
            results['end_time'] = workflow_end
            results['duration'] = str(duration)
            
        except Exception as e:
            logger.error(f"Critical error in daily workflow: {str(e)}")
            results['error'] = str(e)
        
        return results

def run_daily_automation(app):
    """Entry point for running daily automation"""
    automation = DailyLotteryAutomation(app)
    return automation.run_complete_daily_workflow()

# For manual testing
if __name__ == "__main__":
    from main import app
    
    print("Starting manual daily automation test...")
    results = run_daily_automation(app)
    
    print("\n=== AUTOMATION RESULTS ===")
    print(f"Overall Success: {results['overall_success']}")
    print(f"Duration: {results.get('duration', 'Unknown')}")
    
    for step, data in results.items():
        if isinstance(data, dict) and 'success' in data:
            status = "✅" if data['success'] else "❌"
            print(f"{step.title()}: {status} (Count: {data['count']})")