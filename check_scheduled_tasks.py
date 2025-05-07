from main import app
from models import ScheduleConfig, db
import logging

# Set up logging for this script
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def check_tasks():
    logger.info("Checking scheduled tasks")
    
    with app.app_context():
        tasks = ScheduleConfig.query.all()
        
        if tasks:
            logger.info(f"Found {len(tasks)} scheduled tasks")
            
            for task in tasks:
                logger.info(f"Task: {task.id}")
                logger.info(f"  Lottery Type: {task.lottery_type}")
                logger.info(f"  URL: {task.url}")
                # Schedule may be stored in a different field
                logger.info(f"  Schedule: {task.schedule if hasattr(task, 'schedule') else 'Not set'}")
                logger.info(f"  Last Run: {task.last_run}")
                logger.info("---")
        else:
            logger.warning("No scheduled tasks found")
    
    logger.info("Check completed")
    
if __name__ == "__main__":
    check_tasks()