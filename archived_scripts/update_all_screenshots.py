"""
Script to update all screenshots
"""
from main import app
import screenshot_manager
import logging
from datetime import datetime

# Set up logging
logging.basicConfig(level=logging.INFO,
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("update_screenshots")

def update_all_screenshots():
    """
    Update all screenshot records with requests-based approach
    """
    logger.info("Starting manual update of all screenshots")
    
    start_time = datetime.now()
    
    with app.app_context():
        # Call the actual screenshot update function
        updated_count = screenshot_manager.retake_all_screenshots(app)
        
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        
        logger.info(f"Screenshot update completed in {duration:.1f} seconds")
        logger.info(f"Updated {updated_count} screenshots")
        
        return updated_count

if __name__ == "__main__":
    update_all_screenshots()