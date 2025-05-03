"""
Fix screenshot synchronization issues.

This is a simple script that ensures all screenshots in the database
get updated with the same timestamp when running 'Sync All Screenshots'
to fix the issue where only some records were being updated.
"""
import logging
import sys
from datetime import datetime
from main import app
from models import Screenshot, ScheduleConfig, db

# Set up logging
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    stream=sys.stdout)
logger = logging.getLogger("fix_screenshots")

def sync_all_timestamps():
    """
    Update all screenshot records with the same timestamp
    to fix synchronization issues.
    
    Returns:
        int: Number of successfully updated screenshots
    """
    logger.info("Starting update of all screenshot timestamps")
    
    with app.app_context():
        # Get all active configs
        configs = ScheduleConfig.query.filter_by(active=True).all()
        logger.info(f"Found {len(configs)} active configurations")
        
        # Get current time - all screenshots will have the same timestamp
        now = datetime.now()
        
        # Update all screenshots
        count = 0
        for config in configs:
            try:
                # Find existing screenshot record
                screenshot = Screenshot.query.filter_by(url=config.url).first()
                
                if screenshot:
                    logger.info(f"Updating timestamp for {config.lottery_type}")
                    screenshot.timestamp = now
                    count += 1
                else:
                    logger.warning(f"No screenshot record found for {config.lottery_type}")
            except Exception as e:
                logger.error(f"Error updating {config.lottery_type}: {str(e)}")
        
        # Commit all changes at once
        if count > 0:
            db.session.commit()
            logger.info(f"Successfully updated {count} out of {len(configs)} screenshot records")
        
        return count

def check_synchronization():
    """Check current screenshot synchronization status"""
    with app.app_context():
        screenshots = Screenshot.query.order_by(Screenshot.timestamp.desc()).all()
        
        logger.info("Current screenshot timestamps:")
        for s in screenshots:
            logger.info(f"{s.id}: {s.lottery_type} - {s.timestamp}")
        
        # Group by timestamp to see how many different timestamps exist
        timestamps = {}
        for s in screenshots:
            ts = s.timestamp.strftime('%Y-%m-%d %H:%M:%S')
            if ts not in timestamps:
                timestamps[ts] = []
            timestamps[ts].append(s.lottery_type)
        
        logger.info(f"Found {len(timestamps)} different timestamps:")
        for ts, types in timestamps.items():
            logger.info(f"  {ts}: {len(types)} screenshots")

if __name__ == "__main__":
    if '--check' in sys.argv:
        check_synchronization()
    else:
        count = sync_all_timestamps()
        print(f"\nUPDATE COMPLETE: Synchronized {count} screenshot records\n")