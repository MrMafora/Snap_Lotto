from main import app
from models import ScheduleConfig, db
from datetime import datetime
import logging

# Set up logging for this script
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def update_last_run():
    logger.info("Updating last run time for Daily Lottery task")
    
    with app.app_context():
        config = ScheduleConfig.query.filter_by(lottery_type='Daily Lotto').first()
        
        if config:
            logger.info(f"Found Daily Lottery task with ID {config.id}")
            logger.info(f"Current last run: {config.last_run}")
            
            # Update last run time
            config.last_run = datetime.now()
            db.session.commit()
            
            # Verify the update
            config_check = ScheduleConfig.query.filter_by(lottery_type='Daily Lotto').first()
            logger.info(f"Updated last run: {config_check.last_run}")
            logger.info("Last run time updated successfully")
        else:
            logger.warning("No Daily Lottery task found")
    
    logger.info("Update completed")
    
if __name__ == "__main__":
    update_last_run()