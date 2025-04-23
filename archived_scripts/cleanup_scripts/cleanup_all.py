"""
Script to clean up all duplicate screenshots and ensure only one screenshot per URL is kept.
"""

from main import app
from models import Screenshot, db
import os
import logging
import traceback

# Configure logging
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

with app.app_context():
    try:
        # Get all unique URLs
        unique_urls = db.session.query(Screenshot.url).distinct().all()
        urls = [url[0] for url in unique_urls]
        
        print(f"Found {len(urls)} unique URLs")
        
        total_deleted = 0
        
        # For each URL, keep only the most recent screenshot
        for url in urls:
            logger.info(f"Processing URL: {url}")
            
            # Get all screenshots for this URL ordered by timestamp (newest first)
            screenshots = Screenshot.query.filter_by(url=url).order_by(Screenshot.timestamp.desc()).all()
            
            print(f"  - URL: {url} has {len(screenshots)} screenshots")
            
            # Keep the most recent one, delete the rest
            if len(screenshots) > 1:
                print(f"  - Keeping screenshot {screenshots[0].id} from {screenshots[0].timestamp}")
                
                for screenshot in screenshots[1:]:
                    try:
                        print(f"  - Deleting screenshot {screenshot.id} from {screenshot.timestamp}")
                        
                        # Update any lottery results that reference this screenshot
                        from models import LotteryResult
                        referenced_results = LotteryResult.query.filter_by(screenshot_id=screenshot.id).all()
                        
                        if referenced_results:
                            for result in referenced_results:
                                logger.info(f"    - Updating reference for LotteryResult {result.id}")
                                result.screenshot_id = None
                            db.session.commit()
                        
                        # Delete the files from disk
                        if screenshot.path and os.path.exists(screenshot.path):
                            os.remove(screenshot.path)
                            logger.info(f"    - Deleted file: {screenshot.path}")
                        
                        # Delete the zoomed screenshot if it exists
                        if screenshot.zoomed_path and os.path.exists(screenshot.zoomed_path):
                            os.remove(screenshot.zoomed_path)
                            logger.info(f"    - Deleted zoomed file: {screenshot.zoomed_path}")
                        
                        # Delete the database record
                        db.session.delete(screenshot)
                        total_deleted += 1
                        db.session.commit()
                        
                    except Exception as e:
                        logger.error(f"Error deleting screenshot {screenshot.id}: {str(e)}")
                        logger.error(traceback.format_exc())
                        db.session.rollback()
        
        print(f"Cleaned up {total_deleted} screenshots")
        
        # Verify final count
        final_count = Screenshot.query.count()
        print(f"Final screenshot count: {final_count}")
        
    except Exception as e:
        logger.error(f"Error during cleanup: {str(e)}")
        logger.error(traceback.format_exc())
        db.session.rollback()