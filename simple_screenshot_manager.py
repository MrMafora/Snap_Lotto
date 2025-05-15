"""
Simple Screenshot Manager for Lottery Websites

This module provides a simplified approach to capturing lottery website screenshots.
It focuses solely on capturing full-page screenshots without any data extraction or
complex page interactions, designed to work with websites that have strong anti-scraping
protections.
"""
import os
import logging
import time
from datetime import datetime
import traceback
import threading
from playwright.sync_api import sync_playwright
from models import db, Screenshot
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
NAVIGATION_TIMEOUT = 60000  # 60 seconds timeout for page navigation
WAIT_AFTER_LOAD = 5000  # Wait 5 seconds after page load before taking screenshot

def ensure_playwright_browsers():
    """
    Ensure that Playwright browsers are installed.
    This should be run once at the start of the application.
    """
    try:
        import subprocess
        subprocess.check_call(['playwright', 'install', 'chromium'])
        logger.info("Playwright browsers installed successfully")
    except Exception as e:
        logger.error(f"Error installing Playwright browsers: {str(e)}")

def capture_screenshot(url, retry_count=0):
    """
    Simplified function to capture a full-page screenshot using Playwright.
    Focuses only on basic screenshot capture with no page interactions or data extraction.
    
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
        filename = f"{timestamp}_{url.split('/')[-1]}.png"
        filepath = os.path.join(SCREENSHOT_DIR, filename)
        
        logger.info(f"Capturing screenshot from {url} - Attempt {retry_count + 1}/{MAX_RETRIES}")
        
        # Use Playwright to capture screenshot with standard settings
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            
            try:
                # Create page with standard viewport size that fits most content
                page = browser.new_page(
                    viewport={'width': 1280, 'height': 1024},
                    user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
                )
                
                # Navigate with generous timeout
                logger.info(f"Navigating to {url} with {NAVIGATION_TIMEOUT/1000}s timeout")
                page.goto(url, timeout=NAVIGATION_TIMEOUT, wait_until='load')
                
                # Wait for additional time for any lazy-loaded content
                page.wait_for_timeout(WAIT_AFTER_LOAD)
                
                # Take a screenshot of the full page
                page.screenshot(path=filepath, full_page=True)
                logger.info(f"Screenshot successfully saved to {filepath}")
                
                # Read the saved screenshot file to return its content
                with open(filepath, 'rb') as f:
                    screenshot_data = f.read()
                
                browser.close()
                return filepath, screenshot_data, None
                
            except Exception as e:
                logger.error(f"Error during screenshot capture: {str(e)}")
                browser.close()
                
                # Retry on timeout or network errors
                if retry_count < MAX_RETRIES - 1:
                    # Wait before retry to avoid rate limiting
                    wait_time = (retry_count + 1) * 5  # 5, 10, 15 seconds
                    logger.info(f"Waiting {wait_time} seconds before retry...")
                    time.sleep(wait_time)
                    return capture_screenshot(url, retry_count + 1)
                
                return None, None, None
                
    except Exception as e:
        logger.error(f"Critical error capturing screenshot: {str(e)}")
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
                    # Update the database record
                    screenshot.path = filepath
                    screenshot.timestamp = datetime.now()
                    db.session.commit()
                    success_count += 1
                    logger.info(f"Successfully captured and updated screenshot for {screenshot.lottery_type}")
                else:
                    failed_urls.append((screenshot.lottery_type, screenshot.url))
                    logger.warning(f"Failed to capture screenshot for {screenshot.lottery_type}: {screenshot.url}")
                    
            except Exception as e:
                failed_urls.append((screenshot.lottery_type, screenshot.url))
                logger.error(f"Error processing screenshot for {screenshot.lottery_type}: {str(e)}")
                
        # Log summary of results
        logger.info(f"Screenshot capture complete: {success_count} successful, {len(failed_urls)} failed")
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
            
        logger.info(f"Syncing screenshot for {screenshot.lottery_type} from {screenshot.url}")
        
        with screenshot_semaphore:
            filepath, _, _ = capture_screenshot(screenshot.url)
            
        if filepath:
            # Update the database record
            screenshot.path = filepath
            screenshot.timestamp = datetime.now()
            db.session.commit()
            logger.info(f"Successfully synced screenshot for {screenshot.lottery_type}")
            return True
        else:
            logger.warning(f"Failed to sync screenshot for {screenshot.lottery_type}")
            return False
            
    except Exception as e:
        logger.error(f"Error syncing screenshot {screenshot_id}: {str(e)}")
        traceback.print_exc()
        return False