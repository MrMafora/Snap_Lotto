#!/usr/bin/env python3
"""
Script to synchronize screenshots for all lottery types.
Ensures there is exactly one screenshot for each normalized lottery type.

This script:
1. Checks current screenshot database state
2. Removes any duplicate/invalid records 
3. Captures missing lottery types
4. Verifies final state matches expectations (6 normalized types)

Run this script manually whenever screenshots need to be refreshed
or to troubleshoot missing lottery results.
"""
import os
import sys
import logging
import time
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

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
                return missing
            else:
                logger.info("All expected normalized types captured successfully!")
                return []
    except Exception as e:
        logger.error(f"Error running cleanup: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return None

def capture_missing_screenshots(missing_types):
    """
    Capture screenshots for missing lottery types
    
    Args:
        missing_types (list): List of missing normalized lottery types
    
    Returns:
        int: Number of successful captures
    """
    from main import app
    from config import Config
    from screenshot_manager import capture_screenshot
    
    if not missing_types:
        logger.info("No missing types to capture")
        return 0
    
    success_count = 0
    failure_count = 0
    
    # Map normalized types to URL indices
    type_to_url_map = {
        'Lottery': 0,          # Lotto
        'Lottery Plus 1': 1,   # Lotto Plus 1
        'Lottery Plus 2': 2,   # Lotto Plus 2
        'Powerball': 3,        # Powerball
        'Powerball Plus': 4,   # Powerball Plus
        'Daily Lottery': 5     # Daily Lotto
    }
    
    with app.app_context():
        for norm_type in missing_types:
            if norm_type in type_to_url_map:
                index = type_to_url_map[norm_type]
                url_info = Config.RESULTS_URLS[index]
                url = url_info['url']
                lottery_type = url_info['lottery_type']
                
                logger.info(f"Capturing screenshot for {lottery_type} from {url}")
                
                try:
                    # Capture screenshot
                    filepath = capture_screenshot(url, lottery_type)
                    
                    if filepath:
                        logger.info(f"Successfully captured screenshot for {lottery_type}")
                        success_count += 1
                    else:
                        logger.error(f"Failed to capture screenshot for {lottery_type}")
                        failure_count += 1
                        
                    # Small delay between captures to avoid overloading the server
                    time.sleep(2)
                    
                except Exception as e:
                    logger.error(f"Error capturing screenshot for {lottery_type}: {str(e)}")
                    import traceback
                    logger.error(traceback.format_exc())
                    failure_count += 1
            else:
                logger.warning(f"Unknown normalized type: {norm_type}")
    
    logger.info(f"Capture summary: {success_count} successful, {failure_count} failed")
    return success_count

def sync_all_screenshots():
    """
    Main function to synchronize all screenshots
    
    Returns:
        bool: Success status
    """
    try:
        # First run cleanup to see what we have
        logger.info("Step 1: Running initial cleanup to assess current state")
        missing_types = run_cleanup()
        
        if missing_types is None:
            logger.error("Failed to determine missing types")
            return False
        
        if missing_types:
            # Capture missing screenshots
            logger.info(f"Step 2: Capturing {len(missing_types)} missing screenshot types")
            captured = capture_missing_screenshots(missing_types)
            logger.info(f"Captured {captured} out of {len(missing_types)} missing types")
            
            # Run cleanup again to verify and clean up duplicates
            logger.info("Step 3: Running final cleanup to verify results")
            final_missing = run_cleanup()
            
            if not final_missing:
                logger.info("Success! All 6 normalized lottery types are now captured")
                return True
            else:
                logger.warning(f"Still missing {len(final_missing)} types: {', '.join(final_missing)}")
                return False
        else:
            logger.info("All 6 normalized lottery types are already captured")
            return True
    except Exception as e:
        logger.error(f"Error in sync_all_screenshots: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return False

if __name__ == "__main__":
    logger.info("Starting screenshot synchronization")
    
    if sync_all_screenshots():
        logger.info("Screenshot synchronization completed successfully")
        sys.exit(0)
    else:
        logger.error("Screenshot synchronization failed")
        sys.exit(1)