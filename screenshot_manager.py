"""
Screenshot manager for capturing lottery website screenshots
"""
import os
import logging
import asyncio
from datetime import datetime
import traceback
from pathlib import Path
import threading
from playwright.async_api import async_playwright
from playwright.sync_api import sync_playwright
from models import db, Screenshot

logger = logging.getLogger(__name__)

# Create directory for screenshots if it doesn't exist
SCREENSHOT_DIR = os.path.join(os.getcwd(), 'screenshots')
os.makedirs(SCREENSHOT_DIR, exist_ok=True)

# Thread semaphore to limit concurrent screenshots
# This prevents "can't start new thread" errors by limiting resource usage
MAX_CONCURRENT_THREADS = 3
screenshot_semaphore = threading.Semaphore(MAX_CONCURRENT_THREADS)

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

async def capture_screenshot_async(url):
    """
    Capture a screenshot of the specified URL using Playwright.
    This uses a full browser instance to properly render JavaScript and bypass anti-scraping measures.
    
    Args:
        url (str): The URL to capture
        
    Returns:
        tuple: (filepath, screenshot_data) or (None, None) if failed
    """
    try:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{timestamp}_{url.split('/')[-1]}.png"
        filepath = os.path.join(SCREENSHOT_DIR, filename)
        
        logger.info(f"Capturing screenshot from {url} using Playwright")
        
        chromium_path = "/nix/store/zi4f80l169xlmivz8vja8wlphq74qqk0-chromium-125.0.6422.141/bin/chromium"
        if os.path.exists(chromium_path):
            logger.info(f"Using Chromium from: {chromium_path}")
        
        # Use Playwright to capture screenshot
        async with async_playwright() as p:
            browser_type = p.chromium
            
            try:
                browser = await browser_type.launch(
                    headless=True,
                    executable_path=chromium_path if os.path.exists(chromium_path) else None
                )
                
                context = await browser.new_context(
                    viewport={'width': 1280, 'height': 1600},
                    user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
                )
                
                page = await context.new_page()
                
                # Set extra HTTP headers to appear more like a real browser
                await page.set_extra_http_headers({
                    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
                    "Accept-Language": "en-US,en;q=0.9",
                    "Accept-Encoding": "gzip, deflate, br",
                    "Connection": "keep-alive",
                    "Upgrade-Insecure-Requests": "1",
                    "Sec-Fetch-Dest": "document",
                    "Sec-Fetch-Mode": "navigate",
                    "Sec-Fetch-Site": "none",
                    "Sec-Fetch-User": "?1",
                    "DNT": "1"
                })
                
                # Navigate and wait for the page to fully load
                await page.goto(url, wait_until='networkidle')
                
                # Scroll down to ensure all content is loaded
                await page.evaluate('window.scrollTo(0, document.body.scrollHeight)')
                await page.wait_for_timeout(1000)  # Wait a second for any animations
                
                # Take a screenshot of the full page
                await page.screenshot(path=filepath, full_page=True)
                
                logger.info(f"Screenshot successfully saved to {filepath}")
                
                # Read the saved screenshot file to return its content
                with open(filepath, 'rb') as f:
                    screenshot_data = f.read()
                
                await browser.close()
                return filepath, screenshot_data
                
            except Exception as e:
                logger.error(f"Playwright screenshot capture failed: {str(e)}")
                traceback.print_exc()
                return None, None
            
    except Exception as e:
        logger.error(f"Error capturing screenshot: {str(e)}")
        traceback.print_exc()
        return None, None

def capture_screenshot_sync(url):
    """
    Synchronous version of screenshot capture using Playwright sync API.
    
    Args:
        url (str): The URL to capture
        
    Returns:
        tuple: (filepath, screenshot_data) or (None, None) if failed
    """
    import time

    try:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{timestamp}_{url.split('/')[-1]}.png"
        filepath = os.path.join(SCREENSHOT_DIR, filename)
        
        logger.info(f"Capturing screenshot from {url} using Playwright (sync)")
        
        # Try to find chromium in common locations
        chromium_paths = [
            "/nix/store/zi4f80l169xlmivz8vja8wlphq74qqk0-chromium-125.0.6422.141/bin/chromium",
            "/usr/bin/chromium-browser",
            "/usr/bin/chromium",
            "/nix/store/chromium/bin/chromium"
        ]
        
        chromium_path = None
        for path in chromium_paths:
            if os.path.exists(path):
                logger.info(f"Using Chromium from: {path}")
                chromium_path = path
                break
                
        # Use Playwright to capture screenshot with built-in timeouts
        with sync_playwright() as p:
            browser_type = p.chromium
            
            try:
                browser = browser_type.launch(
                    headless=True,
                    executable_path=chromium_path
                )
                
                context = browser.new_context(
                    viewport={'width': 1280, 'height': 1600},
                    user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
                )
                
                page = context.new_page()
                
                # Set extra HTTP headers to appear more like a real browser
                page.set_extra_http_headers({
                    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
                    "Accept-Language": "en-US,en;q=0.9",
                    "Accept-Encoding": "gzip, deflate, br",
                    "Connection": "keep-alive",
                    "Upgrade-Insecure-Requests": "1",
                    "Sec-Fetch-Dest": "document",
                    "Sec-Fetch-Mode": "navigate",
                    "Sec-Fetch-Site": "none",
                    "Sec-Fetch-User": "?1",
                    "DNT": "1"
                })
                
                # Navigate and wait for the page to fully load with a timeout
                start_time = time.time()
                max_time = 30  # Maximum time in seconds
                
                try:
                    # Try to navigate with a 20-second timeout
                    page.goto(url, wait_until='networkidle', timeout=20000)
                except Exception as e:
                    # If timeout occurs, log but continue - we might still get a partial page
                    logger.warning(f"Page navigation timeout for {url}: {str(e)}")
                    
                    # Since we caught the timeout, let's try to continue with whatever page was loaded
                    if time.time() - start_time > max_time:
                        logger.error("Exceeded maximum time, aborting")
                        raise TimeoutError("Screenshot capture exceeded maximum time")
                
                # Scroll down to ensure all content is loaded
                try:
                    page.evaluate('window.scrollTo(0, document.body.scrollHeight)')
                    page.wait_for_timeout(1000)  # Wait a second for any animations
                except Exception as e:
                    logger.warning(f"Error during page scrolling: {str(e)}")
                
                # Take a screenshot of the full page
                page.screenshot(path=filepath, full_page=True)
                
                logger.info(f"Screenshot successfully saved to {filepath}")
                
                # Read the saved screenshot file to return its content
                with open(filepath, 'rb') as f:
                    screenshot_data = f.read()
                
                browser.close()
                return filepath, screenshot_data
                
            except Exception as e:
                logger.error(f"Playwright screenshot capture failed: {str(e)}")
                traceback.print_exc()
                
                # Clean up any browser instances
                try:
                    browser.close()
                except:
                    pass
                
                return None, None
            
    except Exception as e:
        logger.error(f"Error capturing screenshot: {str(e)}")
        traceback.print_exc()
        return None, None

def capture_screenshot(url, lottery_type=None):
    """
    Capture screenshot of the specified URL and save metadata to database.
    
    This function captures a screenshot using Playwright with Chromium to bypass 
    anti-scraping measures on lottery websites.
    
    Args:
        url (str): The URL to capture
        lottery_type (str, optional): The type of lottery. If None, extracted from URL.
        
    Returns:
        tuple: (filepath, screenshot_data) or (None, None) if failed
    """
    if not lottery_type:
        lottery_type = extract_lottery_type_from_url(url)
    
    # Use semaphore to limit concurrent screenshot captures
    # This prevents "can't start new thread" errors
    if not screenshot_semaphore.acquire(blocking=True, timeout=300):
        logger.error(f"Could not acquire screenshot semaphore for {lottery_type} after waiting 5 minutes")
        return None, None
    
    try:
        # Use the sync method instead of async to avoid event loop issues
        filepath, screenshot_data = capture_screenshot_sync(url)
        
        if filepath and screenshot_data:
            try:
                # Check if we need to create an app context
                from flask import current_app, has_app_context
                if not has_app_context():
                    # Import app here to avoid circular imports
                    from app import app
                    with app.app_context():
                        # Save screenshot metadata to database within app context
                        screenshot = Screenshot(
                            url=url,
                            lottery_type=lottery_type,
                            timestamp=datetime.now(),
                            path=filepath,
                            processed=False
                        )
                        
                        db.session.add(screenshot)
                        db.session.commit()
                        
                        logger.info(f"Screenshot record saved to database with ID {screenshot.id}")
                else:
                    # We already have an app context, proceed normally
                    screenshot = Screenshot(
                        url=url,
                        lottery_type=lottery_type,
                        timestamp=datetime.now(),
                        path=filepath,
                        processed=False
                    )
                    
                    db.session.add(screenshot)
                    db.session.commit()
                    
                    logger.info(f"Screenshot record saved to database with ID {screenshot.id}")
            except Exception as e:
                logger.error(f"Error saving screenshot to database: {str(e)}")
                traceback.print_exc()
                # Still return the filepath so OCR can be attempted
            
            return filepath, None  # Return None for extracted data to use OCR
    except Exception as e:
        logger.error(f"Error in capture_screenshot: {str(e)}")
        traceback.print_exc()
        return None, None
    finally:
        # Always release the semaphore in the finally block
        # to ensure it's released even if an exception occurs
        screenshot_semaphore.release()
        logger.debug(f"Released screenshot semaphore for {lottery_type}")
    
    return None, None

def extract_lottery_type_from_url(url):
    """Extract lottery type from the URL"""
    lower_url = url.lower()
    
    if "lotto-plus-1" in lower_url:
        return "Lotto Plus 1"
    elif "lotto-plus-2" in lower_url:
        return "Lotto Plus 2"
    elif "powerball-plus" in lower_url:
        return "Powerball Plus"
    elif "powerball" in lower_url:
        return "Powerball"
    elif "daily-lotto" in lower_url:
        return "Daily Lotto"
    elif "lotto" in lower_url:
        return "Lotto"
    
    # For results pages
    if "results" in lower_url:
        if "lotto-plus-1-results" in lower_url:
            return "Lotto Plus 1 Results"
        elif "lotto-plus-2-results" in lower_url:
            return "Lotto Plus 2 Results"
        elif "powerball-plus" in lower_url:
            return "Powerball Plus Results"
        elif "powerball" in lower_url:
            return "Powerball Results"
        elif "daily-lotto" in lower_url:
            return "Daily Lotto Results"
        elif "lotto" in lower_url:
            return "Lotto Results"
    
    return "Unknown"

def get_unprocessed_screenshots():
    """Get all unprocessed screenshots from the database"""
    return Screenshot.query.filter_by(processed=False).all()

def mark_screenshot_as_processed(screenshot_id):
    """Mark a screenshot as processed in the database"""
    screenshot = Screenshot.query.get(screenshot_id)
    if screenshot:
        screenshot.processed = True
        db.session.commit()

def cleanup_old_screenshots():
    """
    Clean up old screenshots to save disk space.
    Keep only the most recent screenshot for each URL.
    
    This ensures we only have 12 screenshots at any given time (one per URL).
    """
    logger.info("Starting screenshot cleanup process")
    
    try:
        # Get all unique URLs
        unique_urls = db.session.query(Screenshot.url).distinct().all()
        urls = [url[0] for url in unique_urls]
        
        deleted_count = 0
        
        from models import LotteryResult
        
        # For each URL, keep only the most recent screenshot
        for url in urls:
            # Get all screenshots for this URL ordered by timestamp (newest first)
            screenshots = Screenshot.query.filter_by(url=url).order_by(Screenshot.timestamp.desc()).all()
            
            # Keep the most recent one, delete the rest
            if len(screenshots) > 1:
                for screenshot in screenshots[1:]:
                    try:
                        # First check if screenshot is referenced by lottery results
                        # We need to handle the foreign key constraint
                        referenced_results = LotteryResult.query.filter_by(screenshot_id=screenshot.id).all()
                        
                        if referenced_results:
                            # Screenshot is referenced, update these references to NULL
                            for result in referenced_results:
                                logger.info(f"Clearing screenshot_id reference for LotteryResult {result.id}")
                                result.screenshot_id = None
                            db.session.commit()
                                
                        # Delete the file from disk
                        if os.path.exists(screenshot.path):
                            os.remove(screenshot.path)
                            logger.info(f"Deleted old screenshot file: {screenshot.path}")
                        
                        # Delete the database record
                        db.session.delete(screenshot)
                        deleted_count += 1
                        db.session.commit()  # Commit after each deletion to avoid large transactions
                        
                    except Exception as e:
                        logger.error(f"Error deleting screenshot {screenshot.id}: {str(e)}")
                        logger.error(traceback.format_exc())
                        # Continue with next screenshot
                        db.session.rollback()
        
        logger.info(f"Cleaned up {deleted_count} old screenshots" if deleted_count > 0 else "No old screenshots to clean up")
            
    except Exception as e:
        logger.error(f"Error during screenshot cleanup: {str(e)}")
        logger.error(traceback.format_exc())
        db.session.rollback()
