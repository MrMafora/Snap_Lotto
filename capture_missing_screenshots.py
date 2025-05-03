#!/usr/bin/env python3
"""
Script to capture screenshots for all missing lottery types.
"""
import os
import sys
import time
import logging
from sqlalchemy import func
from models import db, Screenshot
from screenshot_manager import capture_screenshot
from config import Config

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger("capture_missing_screenshots")

def get_captured_lottery_types():
    """Get all normalized lottery types that already have screenshots."""
    from data_aggregator import normalize_lottery_type
    
    # Create a context
    from main import app
    with app.app_context():
        # Query for distinct lottery types in the database
        existing_types = db.session.query(Screenshot.lottery_type).distinct().all()
        # Extract the values and normalize them
        return [normalize_lottery_type(lt[0]) for lt in existing_types]

def get_missing_lottery_types():
    """Determine which lottery types are missing screenshots."""
    # All required normalized lottery types - match the normalization in data_aggregator.py
    all_types = ["Lottery", "Lottery Plus 1", "Lottery Plus 2", "Powerball", "Powerball Plus", "Daily Lottery"]
    
    # Get types we already have
    existing_types = get_captured_lottery_types()
    logger.info(f"Existing normalized lottery types: {existing_types}")
    
    # Find missing types
    missing_types = [lt for lt in all_types if lt not in existing_types]
    logger.info(f"Missing normalized lottery types: {missing_types}")
    
    return missing_types

def get_url_for_lottery_type(lottery_type):
    """
    Get the appropriate URL for a normalized lottery type from the config.
    Maps between normalized names (Lottery) and config names (Lotto).
    """
    # Create a mapping between normalized types and config types
    mapping = {
        "Lottery": "Lotto",
        "Lottery Plus 1": "Lotto Plus 1",
        "Lottery Plus 2": "Lotto Plus 2",
        "Powerball": "Powerball",
        "Powerball Plus": "Powerball Plus",
        "Daily Lottery": "Daily Lotto"
    }
    
    # Convert from normalized type to config type
    config_type = mapping.get(lottery_type)
    if not config_type:
        logger.error(f"No mapping found for normalized lottery type: {lottery_type}")
        return None
    
    # Look up URL in config
    for url_info in Config.RESULTS_URLS:
        if url_info['lottery_type'] == config_type:
            return url_info['url']
    
    logger.error(f"No URL found for lottery type: {config_type}")
    return None

def capture_missing_screenshots():
    """Capture screenshots for all missing lottery types."""
    missing_types = get_missing_lottery_types()
    
    if not missing_types:
        logger.info("No missing lottery types! All 6 required types already have screenshots.")
        return True
    
    logger.info(f"Will attempt to capture {len(missing_types)} missing lottery types")
    
    success_count = 0
    for lottery_type in missing_types:
        url = get_url_for_lottery_type(lottery_type)
        if not url:
            logger.error(f"Could not find URL for lottery type: {lottery_type}")
            continue
        
        logger.info(f"Capturing screenshot for {lottery_type} from {url}")
        
        try:
            # Add a delay between captures to reduce detection
            time.sleep(5)
            
            # Capture the screenshot
            result = capture_screenshot(url, lottery_type)
            
            if result and all(result):
                logger.info(f"Successfully captured screenshot for {lottery_type}")
                success_count += 1
            else:
                logger.error(f"Failed to capture screenshot for {lottery_type}")
        except Exception as e:
            logger.error(f"Error capturing screenshot for {lottery_type}: {str(e)}")
    
    logger.info(f"Capture process completed. Captured {success_count} out of {len(missing_types)} missing lottery types.")
    return success_count == len(missing_types)

if __name__ == "__main__":
    logger.info("Starting capture of missing lottery screenshots")
    capture_missing_screenshots()
    logger.info("Capture process finished")