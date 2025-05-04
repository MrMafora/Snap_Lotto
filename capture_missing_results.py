#!/usr/bin/env python3
"""
Script to capture the remaining results URLs for lottery types.

This script specifically focuses on capturing the current results URLs of lottery types
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
        logging.FileHandler('logs/capture_missing_results.log')
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

def get_missing_results_urls():
    """
    Determine which results URLs are missing screenshots.
    
    Returns:
        list: List of dictionaries with URL and lottery type information
    """
    with create_app_context():
        # Get all schedule configs for results URLs
        results_configs = db.session.query(ScheduleConfig).filter(
            or_(
                ScheduleConfig.url.contains('/results/'),
                and_(
                    ScheduleConfig.url.contains('results'),
                    ~ScheduleConfig.url.contains('-history')
                )
            )
        ).all()
        
        # Check which ones don't have screenshots
        missing_urls = []
        for config in results_configs:
            # See if there's a screenshot for this URL
            screenshot = db.session.query(Screenshot).filter(
                Screenshot.url == config.url
            ).first()
            
            if not screenshot:
                missing_urls.append({
                    'url': config.url,
                    'lottery_type': config.lottery_type
                })
                logger.info(f"Missing screenshot for results URL: {config.url} ({config.lottery_type})")
            
        logger.info(f"Found {len(missing_urls)} missing results URLs out of {len(results_configs)} total")
        return missing_urls

def capture_missing_results():
    """
    Capture screenshots for all missing results URLs.
    
    Returns:
        bool: Success status
    """
    missing_urls = get_missing_results_urls()
    
    if not missing_urls:
        logger.info("No missing results URLs! All results URLs already have screenshots.")
        return True
    
    success_count = 0
    
    # Sort by lottery type for better organization
    missing_urls = sorted(missing_urls, key=lambda x: x['lottery_type'])
    
    for url_info in missing_urls:
        url = url_info['url']
        lottery_type = url_info['lottery_type']
        
        logger.info(f"Capturing screenshot for {lottery_type} from {url}")
        
        try:
            # Add a delay between captures to reduce detection
            # Use a long random delay (30-60 seconds) to avoid getting blocked
            delay = random.uniform(30, 60)
            logger.info(f"Waiting {delay:.1f} seconds before capture to avoid detection")
            time.sleep(delay)
            
            # Capture the screenshot
            result = capture_screenshot(url, lottery_type)
            
            if result and all(result):
                logger.info(f"Successfully captured screenshot for {lottery_type}")
                success_count += 1
            else:
                logger.error(f"Failed to capture screenshot for {lottery_type}")
        except Exception as e:
            logger.error(f"Error capturing screenshot for {lottery_type}: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
    
    logger.info(f"Capture process completed. Captured {success_count} out of {len(missing_urls)} missing results URLs.")
    return success_count == len(missing_urls)

def force_recapture_results(lottery_type=None):
    """
    Force recapture of results URL(s) even if they already exist.
    
    Args:
        lottery_type (str, optional): Specific lottery type to recapture, or None for all
        
    Returns:
        bool: Success status
    """
    with create_app_context():
        # Query for results URLs
        query = db.session.query(ScheduleConfig).filter(
            or_(
                ScheduleConfig.url.contains('/results/'),
                and_(
                    ScheduleConfig.url.contains('results'),
                    ~ScheduleConfig.url.contains('-history')
                )
            )
        )
        
        # Filter by lottery type if specified
        if lottery_type:
            normalized_type = normalize_lottery_type(lottery_type)
            query = query.filter(
                ScheduleConfig.lottery_type.ilike(f"%{normalized_type}%")
            )
            
        results_configs = query.all()
        
        if not results_configs:
            logger.info(f"No results URLs found for {'specified lottery type' if lottery_type else 'any type'}")
            return False
        
        success_count = 0
        for config in results_configs:
            url = config.url
            lt = config.lottery_type
            
            logger.info(f"Force recapturing {lt} from {url}")
            
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
                    logger.info(f"Successfully recaptured screenshot for {lt}")
                    success_count += 1
                else:
                    logger.error(f"Failed to recapture screenshot for {lt}")
            except Exception as e:
                logger.error(f"Error recapturing {lt}: {str(e)}")
                import traceback
                logger.error(traceback.format_exc())
                
        logger.info(f"Recapture process completed. Successfully recaptured {success_count} out of {len(results_configs)} results URLs.")
        return success_count > 0

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Capture missing lottery results URLs")
    parser.add_argument('--force', action='store_true', 
                        help='Force recapture of results URLs even if they already exist')
    parser.add_argument('--type', type=str, 
                        help='Specific lottery type to force recapture (only used with --force)')
    
    args = parser.parse_args()
    
    if args.force:
        logger.info(f"Starting forced recapture of results URLs for {args.type if args.type else 'all lottery types'}")
        success = force_recapture_results(args.type)
    else:
        logger.info("Starting capture of missing results URLs")
        success = capture_missing_results()
    
    if success:
        logger.info("Screenshot capture completed successfully")
        sys.exit(0)
    else:
        logger.error("Screenshot capture completed with errors")
        sys.exit(1)