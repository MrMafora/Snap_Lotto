"""
Selenium Screenshot Manager

A pure Python solution for capturing screenshots using Selenium, which is more
reliable in the Replit environment without requiring separate browser installations.
"""
import os
import logging
import time
import traceback
import threading
from datetime import datetime
import urllib.request
from models import db, Screenshot, ScheduleConfig
from logger import setup_logger

# Set up module-specific logger
logger = setup_logger(__name__, level=logging.INFO)

# Create directory for screenshots if it doesn't exist
SCREENSHOT_DIR = os.path.join(os.getcwd(), 'screenshots')
os.makedirs(SCREENSHOT_DIR, exist_ok=True)

# Thread semaphore to limit concurrent screenshots
# This prevents "can't start new thread" errors by limiting resource usage
MAX_CONCURRENT_THREADS = 2
screenshot_semaphore = threading.Semaphore(MAX_CONCURRENT_THREADS)

# Screenshot capture settings
MAX_RETRIES = 3  # Number of retry attempts for failed screenshots
NAVIGATION_TIMEOUT = 60  # 60 seconds timeout for page navigation

def capture_screenshot(url, retry_count=0):
    """
    Simplified function to capture a screenshot using urllib.
    This is a fallback approach that doesn't provide full-page screenshots
    but is more reliable when Playwright is not available.
    
    Args:
        url (str): The URL to capture
        retry_count (int): Current retry attempt
        
    Returns:
        tuple: (filepath, screenshot_data, None) or (None, None, None) if failed
    """
    # If we've exceeded max retries, give up
    if retry_count >= MAX_RETRIES:
        logger.error(f"Maximum retry attempts ({MAX_RETRIES}) exceeded for {url}")
        return None, None, None
        
    try:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        url_filename = url.split('/')[-1] or 'index'
        filename = f"{timestamp}_{url_filename}.txt"
        filepath = os.path.join(SCREENSHOT_DIR, filename)
        
        logger.info(f"Capturing data from {url} - Attempt {retry_count + 1}/{MAX_RETRIES}")
        
        # Use urllib to get the HTML content
        try:
            # Use a custom User-Agent to avoid being blocked
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
            }
            req = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(req, timeout=NAVIGATION_TIMEOUT) as response:
                html_content = response.read()
                
                # Save the HTML content to a file
                with open(filepath, 'wb') as f:
                    f.write(html_content)
                
                logger.info(f"HTML content successfully saved to {filepath}")
                
                # Return the filepath and data
                return filepath, html_content, None
                
        except Exception as e:
            logger.error(f"Error during URL fetch: {str(e)}")
            
            # Retry on timeout or network errors
            if retry_count < MAX_RETRIES - 1:
                # Wait before retry to avoid rate limiting
                wait_time = (retry_count + 1) * 5  # 5, 10, 15 seconds
                logger.info(f"Waiting {wait_time} seconds before retry...")
                time.sleep(wait_time)
                return capture_screenshot(url, retry_count + 1)
            
            return None, None, None
            
    except Exception as e:
        logger.error(f"Critical error capturing data: {str(e)}")
        traceback.print_exc()
        return None, None, None

def capture_all_screenshots():
    """
    Capture screenshots for all lottery URLs in the database.
    Returns the number of successful captures.
    """
    success_count = 0
    failed_urls = []
    
    try:
        # Get all screenshot records from database
        screenshots = Screenshot.query.all()
        logger.info(f"Found {len(screenshots)} screenshot records to capture")
        
        for screenshot in screenshots:
            try:
                with screenshot_semaphore:
                    filepath, _, _ = capture_screenshot(screenshot.url)
                    
                if filepath:
                    # Update the Screenshot record
                    screenshot.path = filepath
                    screenshot.timestamp = datetime.now()
                    
                    # Also update the corresponding ScheduleConfig record if it exists
                    config = ScheduleConfig.query.filter_by(url=screenshot.url).first()
                    if config:
                        config.last_run = datetime.now()
                        logger.info(f"Updated ScheduleConfig record for {screenshot.lottery_type}")
                    else:
                        logger.warning(f"No ScheduleConfig record found for {screenshot.lottery_type}")
                    
                    # Commit all updates
                    db.session.commit()
                    success_count += 1
                    logger.info(f"Successfully captured and updated data for {screenshot.lottery_type}")
                else:
                    failed_urls.append((screenshot.lottery_type, screenshot.url))
                    logger.warning(f"Failed to capture data for {screenshot.lottery_type}: {screenshot.url}")
                    
            except Exception as e:
                failed_urls.append((screenshot.lottery_type, screenshot.url))
                logger.error(f"Error processing data for {screenshot.lottery_type}: {str(e)}")
                
        # Log summary of results
        logger.info(f"Data capture complete: {success_count} successful, {len(failed_urls)} failed")
        for lottery_type, url in failed_urls:
            logger.warning(f"Failed: {lottery_type} - {url}")
            
        return success_count
        
    except Exception as e:
        logger.error(f"Error in capture_all_screenshots: {str(e)}")
        traceback.print_exc()
        return 0

def sync_single_screenshot(screenshot_id):
    """
    Sync a single screenshot by ID.
    Returns True if successful, False otherwise.
    """
    try:
        # Find the screenshot by ID
        screenshot = Screenshot.query.get(screenshot_id)
        if not screenshot:
            logger.error(f"Screenshot with ID {screenshot_id} not found")
            return False
            
        logger.info(f"Syncing data for {screenshot.lottery_type} from {screenshot.url}")
        
        with screenshot_semaphore:
            filepath, _, _ = capture_screenshot(screenshot.url)
            
        if filepath:
            # Update the Screenshot record
            screenshot.path = filepath
            screenshot.timestamp = datetime.now()
            
            # Also update the corresponding ScheduleConfig record if it exists
            config = ScheduleConfig.query.filter_by(url=screenshot.url).first()
            if config:
                config.last_run = datetime.now()
                logger.info(f"Updated ScheduleConfig record for {screenshot.lottery_type}")
            else:
                logger.warning(f"No ScheduleConfig record found for {screenshot.lottery_type}")
            
            db.session.commit()
            logger.info(f"Successfully synced data for {screenshot.lottery_type}")
            return True
        else:
            logger.warning(f"Failed to sync data for {screenshot.lottery_type}")
            return False
            
    except Exception as e:
        logger.error(f"Error syncing data {screenshot_id}: {str(e)}")
        traceback.print_exc()
        return False