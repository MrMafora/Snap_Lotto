"""
Simplified scheduler functions for lottery screenshot capture

This module provides functions to capture screenshots of lottery websites
using a simplified approach that focuses solely on taking full-page screenshots
without any data extraction or complex browser interactions.
"""
import logging
import traceback
from datetime import datetime
from models import db, Screenshot, ScheduleConfig
from simple_screenshot_manager import capture_screenshot, capture_all_screenshots
from logger import setup_logger

# Set up module-specific logger
logger = setup_logger(__name__)

def retake_all_screenshots(app=None, use_threading=False):
    """
    Simplified function to retake all screenshots.
    Uses the simplified screenshot manager with no data extraction.
    
    Args:
        app: Flask app context (optional)
        use_threading: Whether to use threading (ignored in simplified version)
    
    Returns:
        int: Number of screenshots captured
    """
    try:
        # Ensure we have an app context if provided
        if app:
            with app.app_context():
                return capture_all_screenshots()
        else:
            return capture_all_screenshots()
    except Exception as e:
        logger.error(f"Error in simplified retake_all_screenshots: {str(e)}")
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
    """Internal implementation for syncing a single screenshot"""
    try:
        # Find the screenshot by ID
        screenshot = Screenshot.query.get(screenshot_id)
        if not screenshot:
            logger.error(f"Screenshot with ID {screenshot_id} not found")
            return False
            
        logger.info(f"Syncing screenshot for {screenshot.lottery_type} from {screenshot.url}")
        
        # Capture the screenshot using our simplified approach
        filepath, screenshot_data, _ = capture_screenshot(screenshot.url)
        
        if filepath:
            # Update the database record
            screenshot.path = filepath
            screenshot.timestamp = datetime.now()
            screenshot.zoomed_path = None  # No zoomed version in simplified approach
            db.session.commit()
            
            logger.info(f"Successfully synced screenshot for {screenshot.lottery_type}")
            return True
        else:
            logger.warning(f"Failed to capture screenshot for {screenshot.lottery_type}")
            return False
    except Exception as e:
        logger.error(f"Error in _sync_single_screenshot_impl: {str(e)}")
        traceback.print_exc()
        return False