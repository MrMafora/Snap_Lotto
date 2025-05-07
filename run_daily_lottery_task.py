from main import app
from scheduler import run_lottery_task
import logging

# Set up logging for this script
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def run_daily_lottery_update():
    logger.info("Running Daily Lottery update task")
    
    with app.app_context():
        # Daily Lotto history URL
        url = "https://www.nationallottery.co.za/daily-lotto-history"
        lottery_type = "Daily Lotto"
        
        logger.info(f"Running lottery task for {lottery_type} from {url}")
        success = run_lottery_task(url, lottery_type)
        
        if success:
            logger.info(f"Successfully updated {lottery_type} data")
        else:
            logger.error(f"Failed to update {lottery_type} data")
    
    logger.info("Task completed")
    
if __name__ == "__main__":
    run_daily_lottery_update()