from main import app
from selenium_screenshot_manager import capture_all_screenshots
import logging

# Set up logging for this script
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def run_test():
    logger.info("Starting test of the screenshot capture system")
    
    with app.app_context():
        success_count = capture_all_screenshots()
        logger.info(f"Total screenshots captured successfully: {success_count}")
        
    logger.info("Test completed")
    
if __name__ == "__main__":
    run_test()