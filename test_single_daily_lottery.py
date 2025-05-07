from main import app
from selenium_screenshot_manager import capture_screenshot
from models import Screenshot, db
import logging

# Set up logging for this script
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def run_test():
    logger.info("Starting test for Daily Lottery screenshot capture")
    
    with app.app_context():
        # Get the Daily Lotto URL from the database
        daily_lotto = Screenshot.query.filter_by(lottery_type='Daily Lotto').first()
        
        if daily_lotto:
            logger.info(f"Found Daily Lotto record with URL: {daily_lotto.url}")
            
            # Capture the screenshot
            filepath, screenshot_data, _ = capture_screenshot(daily_lotto.url)
            
            if filepath:
                logger.info(f"Successfully captured Daily Lotto screenshot to {filepath}")
                
                # Update the database record
                daily_lotto.path = filepath
                db.session.commit()
                logger.info("Updated Daily Lotto record in database")
            else:
                logger.error("Failed to capture Daily Lotto screenshot")
        else:
            logger.error("No Daily Lotto record found in database")
    
    logger.info("Test completed")
    
if __name__ == "__main__":
    run_test()