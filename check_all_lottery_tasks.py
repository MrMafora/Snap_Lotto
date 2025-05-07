from main import app
from models import ScheduleConfig, Screenshot, db
from datetime import datetime, timedelta
import logging

# Set up logging for this script
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def check_all_tasks():
    logger.info("Checking all lottery tasks and screenshots")
    
    with app.app_context():
        # Check ScheduleConfig table
        tasks = ScheduleConfig.query.all()
        logger.info(f"Found {len(tasks)} scheduled tasks")
        
        # Check for any tasks that haven't been run in the last 24 hours
        yesterday = datetime.now() - timedelta(days=1)
        outdated_tasks = []
        
        for task in tasks:
            logger.info(f"Task: {task.id}")
            logger.info(f"  Lottery Type: {task.lottery_type}")
            logger.info(f"  URL: {task.url}")
            logger.info(f"  Last Run: {task.last_run}")
            
            if task.last_run and task.last_run < yesterday:
                outdated_tasks.append(task.lottery_type)
            
            logger.info("---")
        
        if outdated_tasks:
            logger.warning(f"The following tasks haven't been run in the last 24 hours: {', '.join(outdated_tasks)}")
        else:
            logger.info("All tasks are up-to-date")
        
        # Check Screenshot table
        screenshots = Screenshot.query.all()
        logger.info(f"Found {len(screenshots)} screenshot records")
        
        for screenshot in screenshots:
            logger.info(f"Screenshot: {screenshot.id}")
            logger.info(f"  Lottery Type: {screenshot.lottery_type}")
            logger.info(f"  URL: {screenshot.url}")
            logger.info(f"  Timestamp: {screenshot.timestamp}")
            logger.info(f"  Path: {screenshot.path}")
            logger.info("---")
    
    logger.info("Check completed")
    
if __name__ == "__main__":
    check_all_tasks()