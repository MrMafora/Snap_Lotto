#!/usr/bin/env python3
"""
Script to capture the next missing URL from our schedule.

This script captures just one missing URL at a time, making it suitable
for scheduled tasks with time limitations. It will pick the next URL
based on alphabetical order of lottery types.
"""
import os
import sys
import logging
import argparse
from datetime import datetime

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('logs/next_missing.log')
    ]
)
logger = logging.getLogger(__name__)

# Make sure we can find our module
sys.path.append(os.getcwd())

def create_app_context():
    """Create and return Flask app context."""
    from main import app
    return app.app_context()

def get_next_missing_url():
    """
    Get the next missing URL to capture.
    
    Returns:
        tuple: (url, lottery_type) or (None, None) if none missing
    """
    from models import db, Screenshot, ScheduleConfig
    
    with create_app_context():
        # Query for all configured URLs
        all_configs = db.session.query(ScheduleConfig).order_by(ScheduleConfig.lottery_type).all()
        
        # Check which ones don't have screenshots
        for config in all_configs:
            # See if there's a screenshot for this URL
            screenshot = db.session.query(Screenshot).filter(
                Screenshot.url == config.url
            ).first()
            
            if not screenshot:
                logger.info(f"Found missing URL: {config.url} ({config.lottery_type})")
                return config.url, config.lottery_type
        
        logger.info("No missing URLs found")
        return None, None

def main():
    """Main function to capture the next missing URL."""
    parser = argparse.ArgumentParser(description="Capture the next missing URL")
    parser.add_argument('--use-undetected', action='store_true', 
                      help='Use undetected_chromedriver instead of Playwright')
    
    args = parser.parse_args()
    
    # Create required directories
    os.makedirs('logs', exist_ok=True)
    os.makedirs('screenshots', exist_ok=True)
    os.makedirs('cookies', exist_ok=True)
    
    # Get the next URL to capture
    url, lottery_type = get_next_missing_url()
    
    if not url or not lottery_type:
        logger.info("All URLs have been captured. Nothing to do.")
        return 0
    
    logger.info(f"Will capture: {lottery_type} from {url}")
    
    try:
        # Choose the capture method based on the argument - default to Playwright now
        if args.use_undetected:
            # Use undetected_chromedriver
            from capture_with_undetected import capture_with_undetected_chromedriver
            logger.info("Using undetected_chromedriver for capture")
            result = capture_with_undetected_chromedriver(url, lottery_type)
            success = result and all(result)
        else:
            # Use Playwright
            from screenshot_manager import capture_screenshot
            logger.info("Using Playwright for capture")
            result = capture_screenshot(url, lottery_type)
            success = result and bool(result)  # Changed to bool() since result is just a filepath
        
        if success:
            logger.info(f"Successfully captured {lottery_type} from {url}")
            return 0
        else:
            logger.error(f"Failed to capture {lottery_type} from {url}")
            
            # If Playwright failed, try undetected_chromedriver as fallback
            if not args.use_undetected:
                logger.info("Trying with undetected_chromedriver as fallback")
                try:
                    from capture_with_undetected import capture_with_undetected_chromedriver
                    result = capture_with_undetected_chromedriver(url, lottery_type)
                    success = result and all(result)
                    
                    if success:
                        logger.info(f"Successfully captured {lottery_type} using fallback method")
                        return 0
                    else:
                        logger.error(f"Fallback method also failed for {lottery_type}")
                except Exception as e:
                    logger.error(f"Error during fallback capture: {str(e)}")
            
            return 1
    except Exception as e:
        logger.error(f"Error during capture: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return 1

if __name__ == "__main__":
    sys.exit(main())