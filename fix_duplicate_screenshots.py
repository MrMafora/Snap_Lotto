from main import app
from models import Screenshot, db
import logging

# Set up logging
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("fix_duplicates")

def fix_duplicate_screenshots():
    """
    Fix duplicate screenshots in the database by keeping only the latest entry for each lottery type
    """
    with app.app_context():
        # Find duplicates
        from sqlalchemy import func
        duplicates = db.session.query(
            Screenshot.lottery_type,
            func.count(Screenshot.id).label('count')
        ).group_by(Screenshot.lottery_type).having(func.count(Screenshot.id) > 1).all()
        
        if not duplicates:
            logger.info("No duplicate screenshots found")
            return
        
        logger.info(f"Found {len(duplicates)} duplicate lottery types")
        
        # For each duplicate type, keep only the latest record
        for lottery_type, count in duplicates:
            logger.info(f"Fixing {count} duplicates for {lottery_type}")
            
            # Get all duplicates ordered by timestamp (newest first)
            screenshots = Screenshot.query.filter_by(lottery_type=lottery_type).order_by(
                Screenshot.timestamp.desc()).all()
            
            # Keep the first one (newest), delete the rest
            for screenshot in screenshots[1:]:
                logger.info(f"Deleting duplicate record: ID={screenshot.id}, Type={screenshot.lottery_type}")
                db.session.delete(screenshot)
            
            db.session.commit()
        
        logger.info("Finished fixing duplicate screenshots")

if __name__ == "__main__":
    fix_duplicate_screenshots()