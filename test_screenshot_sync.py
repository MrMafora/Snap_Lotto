import os
import sys
from main import app
import screenshot_manager
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("test_screenshot_sync")

def test_retake_all_screenshots():
    """
    Test the updated retake_all_screenshots function to ensure all URLs are processed
    """
    logger.info("Testing retake_all_screenshots function")
    
    try:
        with app.app_context():
            # Check how many configs we have
            from models import ScheduleConfig
            configs = ScheduleConfig.query.filter_by(active=True).all()
            logger.info(f"Found {len(configs)} active screenshot configurations")
            
            # Call the screenshot retake function with our improved logic
            logger.info("Starting screenshot capture process")
            count = screenshot_manager.retake_all_screenshots(app)
            
            # Check success count
            logger.info(f"Successfully captured {count} screenshots out of {len(configs)} configs")
            
            # Check database to see if all configs were updated
            from models import Screenshot
            screenshots = Screenshot.query.all()
            logger.info(f"Total screenshots in database: {len(screenshots)}")
            
            # Show details of each screenshot
            for s in screenshots:
                logger.info(f"Screenshot ID: {s.id}, Type: {s.lottery_type}, Timestamp: {s.timestamp}")
            
            # Success ratio
            success_ratio = count / len(configs) if len(configs) > 0 else 0
            logger.info(f"Success ratio: {success_ratio:.2%}")
            
            return count, len(configs), success_ratio
    except Exception as e:
        logger.error(f"Error testing screenshot capture: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return 0, 0, 0

if __name__ == "__main__":
    count, total, ratio = test_retake_all_screenshots()
    print(f"\nSUMMARY: Captured {count} screenshots out of {total} configs ({ratio:.2%} success rate)")
    
    # Update last_run timestamps in schedule_config table
    with app.app_context():
        from models import ScheduleConfig, db
        from datetime import datetime
        
        try:
            for config in ScheduleConfig.query.filter_by(active=True).all():
                config.last_run = datetime.now()
            
            db.session.commit()
            print("Updated last_run timestamps for all configs")
        except Exception as e:
            print(f"Error updating timestamps: {str(e)}")