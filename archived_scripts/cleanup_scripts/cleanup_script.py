"""
Standalone script to run the screenshot cleanup functionality with proper application context.
This script will clean up old screenshots, keeping only the most recent one for each URL.
"""

import os
import sys
from main import app
import screenshot_manager
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def run_cleanup():
    """Run the screenshot cleanup with proper Flask application context"""
    logger.info("Starting cleanup script")
    
    with app.app_context():
        try:
            # Run the cleanup function
            logger.info("Running screenshot cleanup...")
            screenshot_manager.cleanup_old_screenshots()
            logger.info("Cleanup completed successfully")
            return True
        except Exception as e:
            logger.error(f"Error during cleanup: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
            return False

if __name__ == "__main__":
    success = run_cleanup()
    sys.exit(0 if success else 1)