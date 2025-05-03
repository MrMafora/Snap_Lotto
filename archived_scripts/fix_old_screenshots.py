"""
Fix old screenshots by updating their timestamps
"""
from main import app
from models import Screenshot, db
from datetime import datetime, timedelta
import logging

# Set up logging
logging.basicConfig(level=logging.INFO,
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("fix_old")

def fix_old_screenshots():
    """
    Update timestamps for old screenshots
    """
    logger.info("Updating timestamps for old screenshots")
    
    with app.app_context():
        # Get cutoff time (5 minutes ago)
        cutoff_time = datetime.now() - timedelta(minutes=5)
        
        # Find old screenshots
        old_screenshots = Screenshot.query.filter(
            Screenshot.timestamp < cutoff_time
        ).all()
        
        if not old_screenshots:
            logger.info("No old screenshots found")
            return
            
        logger.info(f"Found {len(old_screenshots)} old screenshots")
        
        # Update each screenshot timestamp
        for screenshot in old_screenshots:
            logger.info(f"Updating {screenshot.lottery_type} from {screenshot.timestamp}")
            screenshot.timestamp = datetime.now()
            
        # Commit the changes
        db.session.commit()
        
        logger.info(f"Updated {len(old_screenshots)} screenshots")

if __name__ == "__main__":
    fix_old_screenshots()