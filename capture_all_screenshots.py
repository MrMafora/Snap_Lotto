#!/usr/bin/env python3
"""
Script to manually capture screenshots for all lottery types.
This will ensure we have one screenshot for each of the 6 normalized lottery types.
"""
import os
import sys
import logging
import argparse
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def capture_single_screenshot(lottery_type=None, url=None, index=None):
    """
    Capture a single screenshot for the specified lottery type and URL,
    or for the URL at the specified index in the config.
    
    Args:
        lottery_type (str, optional): The lottery type to capture
        url (str, optional): The URL to capture 
        index (int, optional): Index of URL in Config.RESULTS_URLS to capture
    
    Returns:
        bool: Success or failure
    """
    from main import app
    from screenshot_manager import capture_screenshot
    from config import Config
    
    # If index is provided, use the URL at that index
    if index is not None:
        try:
            index = int(index)
            if index < 0 or index >= len(Config.RESULTS_URLS):
                logger.error(f"Invalid index: {index}. Valid range: 0-{len(Config.RESULTS_URLS)-1}")
                return False
                
            url = Config.RESULTS_URLS[index]['url']
            lottery_type = Config.RESULTS_URLS[index]['lottery_type']
        except (ValueError, IndexError) as e:
            logger.error(f"Error with index: {str(e)}")
            return False
    
    # Validate inputs
    if not url or not lottery_type:
        logger.error("Must provide either index, or both url and lottery_type")
        return False
        
    logger.info(f"Capturing screenshot for {lottery_type} from {url}")
    
    try:
        # Capture screenshot within app context
        with app.app_context():
            filepath = capture_screenshot(url, lottery_type)
            
            if filepath:
                logger.info(f"Successfully captured screenshot for {lottery_type}")
                return True
            else:
                logger.error(f"Failed to capture screenshot for {lottery_type}")
                return False
    except Exception as e:
        logger.error(f"Error capturing screenshot for {lottery_type}: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return False

def run_cleanup():
    """Run screenshot cleanup to ensure we have one screenshot per normalized type"""
    from main import app
    from screenshot_manager import cleanup_old_screenshots
    from models import Screenshot
    from data_aggregator import normalize_lottery_type
    
    try:
        with app.app_context():
            # Run cleanup
            logger.info("Running screenshot cleanup")
            cleanup_old_screenshots()
            
            # Display current state
            screenshots = Screenshot.query.all()
            logger.info(f"Database contains {len(screenshots)} screenshots")
            
            # Count by normalized type
            norm_types = {}
            for screenshot in screenshots:
                norm_type = normalize_lottery_type(screenshot.lottery_type)
                if norm_type not in norm_types:
                    norm_types[norm_type] = []
                norm_types[norm_type].append(screenshot.lottery_type)
            
            logger.info(f"Coverage: {len(norm_types)}/6 normalized types captured")
            for norm_type, types in norm_types.items():
                logger.info(f"  {norm_type}: {', '.join(types)}")
            
            # List any missing normalized types
            expected = [
                'Daily Lottery', 'Lottery', 'Lottery Plus 1', 
                'Lottery Plus 2', 'Powerball', 'Powerball Plus'
            ]
            missing = [t for t in expected if t not in norm_types]
            if missing:
                logger.warning(f"Missing {len(missing)} normalized types: {', '.join(missing)}")
            else:
                logger.info("All expected normalized types captured successfully!")
                
            return True
    except Exception as e:
        logger.error(f"Error running cleanup: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return False

def list_urls():
    """List all available URLs and their indices"""
    from config import Config
    
    logger.info("Available lottery URLs:")
    for i, url_info in enumerate(Config.RESULTS_URLS):
        logger.info(f"  [{i}] {url_info['lottery_type']}: {url_info['url']}")
    
    return True

if __name__ == "__main__":
    # Parse command line arguments
    parser = argparse.ArgumentParser(description="Capture lottery screenshots")
    parser.add_argument("--list", action="store_true", help="List available URLs")
    parser.add_argument("--cleanup", action="store_true", help="Run screenshot cleanup")
    parser.add_argument("--index", type=int, help="Index of URL to capture (0-5)")
    parser.add_argument("--url", help="URL to capture")
    parser.add_argument("--type", dest="lottery_type", help="Lottery type")
    
    args = parser.parse_args()
    
    # Handle different actions
    if args.list:
        list_urls()
    elif args.cleanup:
        run_cleanup()
    elif args.index is not None:
        capture_single_screenshot(index=args.index)
    elif args.url and args.lottery_type:
        capture_single_screenshot(lottery_type=args.lottery_type, url=args.url)
    else:
        # If no arguments, show help and list URLs
        parser.print_help()
        print("\n")
        list_urls()
        print("\nExample usage:")
        print("  python capture_all_screenshots.py --index 0  # Capture Lotto")
        print("  python capture_all_screenshots.py --cleanup  # Run cleanup")