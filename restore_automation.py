#!/usr/bin/env python3
"""
Comprehensive Automation Restoration Script
Fixes the automation system and restores fresh lottery data from authentic sources
"""

import logging
import time
import os
from datetime import datetime
from main import app
from daily_automation import DailyLotteryAutomation
from automated_data_extractor import LotteryDataExtractor

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def verify_system_configuration():
    """Verify all system components are properly configured"""
    logger.info("=== VERIFYING SYSTEM CONFIGURATION ===")
    
    # Check Anthropic API key
    from config import Config
    config = Config()
    api_key = config.ANTHROPIC_API_KEY
    
    if not api_key:
        logger.error("Anthropic API key not configured")
        return False
    
    logger.info(f"✓ Anthropic API key configured (length: {len(api_key)})")
    
    # Check database connection
    try:
        with app.app_context():
            from main import db
            result = db.session.execute(db.text("SELECT 1")).fetchone()
            logger.info("✓ Database connection working")
    except Exception as e:
        logger.error(f"Database connection failed: {e}")
        return False
    
    # Check screenshot directory
    if not os.path.exists(config.SCREENSHOT_DIR):
        os.makedirs(config.SCREENSHOT_DIR)
        logger.info("✓ Screenshot directory created")
    else:
        logger.info("✓ Screenshot directory exists")
    
    return True

def run_comprehensive_automation():
    """Run the complete automation workflow to restore fresh data"""
    logger.info("=== STARTING COMPREHENSIVE AUTOMATION ===")
    
    try:
        with app.app_context():
            automation = DailyLotteryAutomation(app)
            
            # Step 1: Clean old screenshots
            logger.info("Step 1: Cleaning old screenshots...")
            cleanup_success = automation.cleanup_old_screenshots()
            logger.info(f"Cleanup result: {cleanup_success}")
            
            # Step 2: Capture fresh screenshots from authentic lottery websites
            logger.info("Step 2: Capturing fresh screenshots from authentic sources...")
            capture_success, capture_count = automation.capture_fresh_screenshots(['all'])
            logger.info(f"Screenshot capture: Success={capture_success}, Count={capture_count}")
            
            if not capture_success:
                logger.warning("Screenshot capture failed, will continue with available images")
            
            # Step 3: Process with AI (both captured screenshots and provided images)
            logger.info("Step 3: Processing images with Anthropic AI...")
            
            # Process any captured screenshots
            ai_success, ai_count = automation.process_screenshots_with_ai()
            logger.info(f"AI processing of screenshots: Success={ai_success}, Count={ai_count}")
            
            # Also process provided lottery images as backup
            extractor = LotteryDataExtractor()
            provided_images = [
                'attached_assets/20250531_045717_lotto.png',
                'attached_assets/20250531_045728_lotto_plus_1_results.png', 
                'attached_assets/20250531_045742_lotto_plus_2_results.png',
                'attached_assets/20250531_045759_powerball.png',
                'attached_assets/20250531_045812_powerball_plus.png',
                'attached_assets/20250531_045824_daily_lotto.png'
            ]
            
            processed_count = 0
            for image_path in provided_images:
                if os.path.exists(image_path):
                    try:
                        logger.info(f"Processing provided image: {image_path}")
                        result = extractor.process_single_image_safe(image_path)
                        if result:
                            saved = extractor.save_to_database(result)
                            if saved:
                                processed_count += 1
                                logger.info(f"✓ Successfully processed and saved: {image_path}")
                            else:
                                logger.warning(f"Failed to save data from: {image_path}")
                        else:
                            logger.warning(f"No data extracted from: {image_path}")
                    except Exception as e:
                        logger.error(f"Error processing {image_path}: {str(e)}")
            
            logger.info(f"Processed {processed_count} provided lottery images")
            
            # Step 4: Verify database has fresh data
            logger.info("Step 4: Verifying database updates...")
            db_success, db_count = automation.update_database_with_results()
            logger.info(f"Database verification: Success={db_success}, Count={db_count}")
            
            # Final status report
            total_processed = ai_count + processed_count
            overall_success = (capture_success or processed_count > 0) and (ai_success or processed_count > 0)
            
            logger.info("=== AUTOMATION RESTORATION COMPLETE ===")
            logger.info(f"Overall Success: {overall_success}")
            logger.info(f"Screenshots Captured: {capture_count}")
            logger.info(f"Images Processed: {total_processed}")
            logger.info(f"Database Records: {db_count}")
            
            return overall_success, {
                'cleanup': cleanup_success,
                'capture_count': capture_count,
                'ai_processed': total_processed,
                'db_records': db_count
            }
            
    except Exception as e:
        logger.error(f"Automation failed: {str(e)}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        return False, None

def check_latest_data():
    """Check what's the latest data in the database"""
    logger.info("=== CHECKING LATEST DATABASE DATA ===")
    
    try:
        with app.app_context():
            from main import db
            
            query = """
            SELECT lottery_type, draw_date, draw_number, main_numbers
            FROM lottery_results 
            ORDER BY draw_date DESC, lottery_type 
            LIMIT 10
            """
            
            results = db.session.execute(db.text(query)).fetchall()
            
            if results:
                logger.info("Latest lottery results in database:")
                for row in results:
                    logger.info(f"  {row.lottery_type}: Draw {row.draw_number}, Date {row.draw_date}, Numbers: {row.numbers}")
            else:
                logger.warning("No lottery results found in database")
                
            return len(results)
            
    except Exception as e:
        logger.error(f"Failed to check database: {e}")
        return 0

def main():
    """Main restoration function"""
    start_time = datetime.now()
    logger.info(f"Starting automation restoration at {start_time}")
    
    # Step 1: Verify system configuration
    if not verify_system_configuration():
        logger.error("System configuration verification failed")
        return False
    
    # Step 2: Check current database state
    initial_count = check_latest_data()
    
    # Step 3: Run comprehensive automation
    success, results = run_comprehensive_automation()
    
    # Step 4: Check final database state
    final_count = check_latest_data()
    
    # Step 5: Report results
    end_time = datetime.now()
    duration = end_time - start_time
    
    logger.info("=== FINAL RESTORATION REPORT ===")
    logger.info(f"Duration: {duration}")
    logger.info(f"Initial DB Records: {initial_count}")
    logger.info(f"Final DB Records: {final_count}")
    logger.info(f"Records Added: {final_count - initial_count}")
    logger.info(f"Overall Success: {success}")
    
    if results:
        logger.info(f"Details: {results}")
    
    return success

if __name__ == "__main__":
    main()