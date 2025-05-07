from main import app
from models import ScheduleConfig, db
import logging

# Set up logging for this script
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def check_daily_lottery():
    logger.info("Checking Daily Lottery task")
    
    with app.app_context():
        daily_lotto = ScheduleConfig.query.filter_by(lottery_type='Daily Lotto').first()
        
        if daily_lotto:
            logger.info(f"Daily Lottery task found:")
            logger.info(f"  ID: {daily_lotto.id}")
            logger.info(f"  URL: {daily_lotto.url}")
            logger.info(f"  Last Run: {daily_lotto.last_run}")
        else:
            logger.warning("No Daily Lottery task found")
    
    logger.info("Check completed")
    
if __name__ == "__main__":
    check_daily_lottery()