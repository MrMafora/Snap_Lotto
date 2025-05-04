#!/usr/bin/env python3
"""
Script to capture the remaining history URLs for lottery types.

This script specifically focuses on capturing the history URLs of lottery types
that are missing from our database.
"""
import os
import logging
import time
import sys
import random
from datetime import datetime, timedelta
from sqlalchemy import and_, or_

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('logs/capture_missing_history.log')
    ]
)
logger = logging.getLogger(__name__)

# Make sure we can find our module
sys.path.append(os.getcwd())

# Import app-specific modules
from models import db, Screenshot, ScheduleConfig
from screenshot_manager import capture_screenshot
from data_aggregator import normalize_lottery_type

def create_app_context():
    """Create and return Flask app context."""
    from main import app
    return app.app_context()

def get_missing_history_urls():
    """
    Determine which history URLs are missing screenshots.
    
    Returns:
        list: List of dictionaries with URL and lottery type information
    """
    with create_app_context():
        # Get all schedule configs for history URLs
        history_configs = db.session.query(ScheduleConfig).filter(
            ScheduleConfig.url.contains('-history')
        ).all()
        
        # Check which ones don't have screenshots
        missing_urls = []
        for config in history_configs:
            # See if there's a screenshot for this URL
            screenshot = db.session.query(Screenshot).filter(
                Screenshot.url == config.url
            ).first()
            
            if not screenshot:
                missing_urls.append({
                    'url': config.url,
                    'lottery_type': config.lottery_type
                })
                logger.info(f"Missing screenshot for history URL: {config.url} ({config.lottery_type})")
            
        logger.info(f"Found {len(missing_urls)} missing history URLs out of {len(history_configs)} total")
        return missing_urls

def capture_missing_history():
    """
    Capture screenshots for all missing history URLs.
    
    Returns:
        bool: Success status
    """
    missing_urls = get_missing_history_urls()
    
    if not missing_urls:
        logger.info("No missing history URLs! All history URLs already have screenshots.")
        return True
    
    success_count = 0
    
    # Sort by lottery type for better organization
    missing_urls = sorted(missing_urls, key=lambda x: x['lottery_type'])
    
    for url_info in missing_urls:
        url = url_info['url']
        lottery_type = url_info['lottery_type']
        
        logger.info(f"Capturing screenshot for {lottery_type} history from {url}")
        
        try:
            # Add a delay between captures to reduce detection
            # Use a long random delay (30-60 seconds) to avoid getting blocked
            delay = random.uniform(30, 60)
            logger.info(f"Waiting {delay:.1f} seconds before capture to avoid detection")
            time.sleep(delay)
            
            # Capture the screenshot
            result = capture_screenshot(url, lottery_type)
            
            if result and all(result):
                logger.info(f"Successfully captured screenshot for {lottery_type} history")
                success_count += 1
            else:
                logger.error(f"Failed to capture screenshot for {lottery_type} history")
        except Exception as e:
            logger.error(f"Error capturing screenshot for {lottery_type} history: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
    
    logger.info(f"Capture process completed. Captured {success_count} out of {len(missing_urls)} missing history URLs.")
    return success_count == len(missing_urls)

def force_recapture_history(lottery_type=None):
    """
    Force recapture of history URL(s) even if they already exist.
    
    Args:
        lottery_type (str, optional): Specific lottery type to recapture, or None for all
        
    Returns:
        bool: Success status
    """
    with create_app_context():
        # Query for history URLs
        query = db.session.query(ScheduleConfig).filter(
            ScheduleConfig.url.contains('-history')
        )
        
        # Filter by lottery type if specified
        if lottery_type:
            normalized_type = normalize_lottery_type(lottery_type)
            query = query.filter(
                ScheduleConfig.lottery_type.ilike(f"%{normalized_type}%")
            )
            
        history_configs = query.all()
        
        if not history_configs:
            logger.info(f"No history URLs found for {'specified lottery type' if lottery_type else 'any type'}")
            return False
        
        success_count = 0
        for config in history_configs:
            url = config.url
            lt = config.lottery_type
            
            logger.info(f"Force recapturing {lt} history from {url}")
            
            try:
                # Remove existing screenshot if any
                existing = db.session.query(Screenshot).filter(
                    Screenshot.url == url
                ).first()
                
                if existing:
                    logger.info(f"Removing existing screenshot record with ID {existing.id}")
                    # Actually delete the record
                    db.session.delete(existing)
                    db.session.commit()
                
                # Add a long delay between captures
                delay = random.uniform(40, 90)  # Even longer delay for forced recaptures
                logger.info(f"Waiting {delay:.1f} seconds before capture")
                time.sleep(delay)
                
                # Capture new screenshot
                result = capture_screenshot(url, lt)
                
                if result and all(result):
                    logger.info(f"Successfully recaptured screenshot for {lt} history")
                    success_count += 1
                else:
                    logger.error(f"Failed to recapture screenshot for {lt} history")
            except Exception as e:
                logger.error(f"Error recapturing {lt} history: {str(e)}")
                import traceback
                logger.error(traceback.format_exc())
                
        logger.info(f"Recapture process completed. Successfully recaptured {success_count} out of {len(history_configs)} history URLs.")
        return success_count > 0

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Capture missing lottery history URLs")
    parser.add_argument('--force', action='store_true', 
                        help='Force recapture of history URLs even if they already exist')
    parser.add_argument('--type', type=str, 
                        help='Specific lottery type to force recapture (only used with --force)')
    
    args = parser.parse_args()
    
    if args.force:
        logger.info(f"Starting forced recapture of history URLs for {args.type if args.type else 'all lottery types'}")
        success = force_recapture_history(args.type)
    else:
        logger.info("Starting capture of missing history URLs")
        success = capture_missing_history()
    
    if success:
        logger.info("Screenshot capture completed successfully")
        sys.exit(0)
    else:
        logger.error("Screenshot capture completed with errors")
        sys.exit(1)