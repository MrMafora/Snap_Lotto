"""
Simplified scheduler functions for lottery screenshot capture

This module provides functions to capture screenshots of lottery websites
using Puppeteer for reliable full-page screenshots without any data extraction
or complex browser interactions.
"""
import logging
import traceback
from datetime import datetime
from models import db, Screenshot, ScheduleConfig
from puppeteer_service import capture_single_screenshot, capture_multiple_screenshots
from logger import setup_logger

# Set up module-specific logger
logger = setup_logger(__name__)

def retake_all_screenshots(app=None, use_threading=False):
    """
    Function to retake all screenshots using Puppeteer.
    Collects URLs from the database and captures all screenshots.
    
    Args:
        app: Flask app context (optional)
        use_threading: Whether to use threading (passed to capture_multiple_screenshots)
    
    Returns:
        int: Number of screenshots captured
    """
    try:
        # Function to execute within app context if needed
        def execute():
            # Get all screenshot configurations from database
            screenshots = Screenshot.query.all()
            # Create URL and type pairs
            urls_with_types = [(s.url, s.lottery_type) for s in screenshots]
            
            if not urls_with_types:
                logger.warning("No screenshot configurations found in database")
                return 0
                
            # Use puppeteer service to capture all screenshots
            results = capture_multiple_screenshots(urls_with_types)
            
            # Count successful captures
            success_count = 0
            
            # Update database with results
            for screenshot, result in zip(screenshots, results):
                if result and result.get('success'):
                    screenshot.path = result['image_path']
                    screenshot.html_path = result.get('html_path')
                    screenshot.timestamp = datetime.now()
                    success_count += 1
            
            # Commit all updates at once
            db.session.commit()
            return success_count
            
        # Ensure we have an app context if provided
        if app:
            with app.app_context():
                return execute()
        else:
            return execute()
    except Exception as e:
        logger.error(f"Error in retake_all_screenshots: {str(e)}")
        traceback.print_exc()
        return 0

def sync_single_screenshot(screenshot_id, app=None):
    """
    Sync a single screenshot using the simplified approach.
    
    Args:
        screenshot_id: ID of the screenshot to sync
        app: Flask app context (optional)
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        # Handle app context if provided
        if app:
            with app.app_context():
                return _sync_single_screenshot_impl(screenshot_id)
        else:
            return _sync_single_screenshot_impl(screenshot_id)
    except Exception as e:
        logger.error(f"Error in simplified sync_single_screenshot: {str(e)}")
        traceback.print_exc()
        return False

def _sync_single_screenshot_impl(screenshot_id):
    """Internal implementation for syncing a single screenshot using Puppeteer"""
    try:
        # Find the screenshot by ID
        screenshot = Screenshot.query.get(screenshot_id)
        if not screenshot:
            logger.error(f"Screenshot with ID {screenshot_id} not found")
            return False
            
        logger.info(f"Syncing screenshot for {screenshot.lottery_type} from {screenshot.url}")
        
        # Capture the screenshot using Puppeteer
        result = capture_single_screenshot(screenshot.lottery_type, screenshot.url)
        
        if result and 'success' in result and result['success']:
            # Update the database record
            screenshot.path = result['image_path']
            screenshot.html_path = result.get('html_path')
            screenshot.timestamp = datetime.now()
            db.session.commit()
            
            logger.info(f"Successfully synced screenshot for {screenshot.lottery_type}")
            return True
        else:
            error_msg = result.get('error', 'Unknown error') if result else 'Unknown error'
            logger.warning(f"Failed to capture screenshot for {screenshot.lottery_type}: {error_msg}")
            return False
    except Exception as e:
        logger.error(f"Error in _sync_single_screenshot_impl: {str(e)}")
        traceback.print_exc()
        return False