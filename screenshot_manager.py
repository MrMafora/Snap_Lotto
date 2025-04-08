import os
import logging
import time
import asyncio
import subprocess
import sys
from datetime import datetime
from playwright.async_api import async_playwright
from models import Screenshot, db
from app import app

logger = logging.getLogger(__name__)

# Create directory for screenshots if it doesn't exist
SCREENSHOT_DIR = os.path.join(os.getcwd(), 'screenshots')
os.makedirs(SCREENSHOT_DIR, exist_ok=True)

# Ensure Playwright browsers are installed
def ensure_playwright_browsers():
    try:
        logger.info("Checking Playwright browsers installation...")
        from playwright.sync_api import sync_playwright
        
        # Test if browsers are installed by creating a temporary browser instance
        with sync_playwright() as p:
            try:
                browser = p.chromium.launch()
                browser.close()
                logger.info("Playwright browsers are already installed")
                return True
            except Exception:
                logger.warning("Playwright browsers not installed, installing now...")
                result = subprocess.run(
                    [sys.executable, "-m", "playwright", "install", "chromium"],
                    capture_output=True,
                    text=True
                )
                if result.returncode == 0:
                    logger.info("Successfully installed Playwright browsers")
                    return True
                else:
                    logger.error(f"Failed to install Playwright browsers: {result.stderr}")
                    return False
    except Exception as e:
        logger.error(f"Error ensuring Playwright browsers: {str(e)}")
        return False

# Run the browser installation check
ensure_playwright_browsers()

# Direct HTML fetching is removed because it doesn't work with anti-scraping websites
# We'll use only Playwright with proper browser rendering

async def take_screenshot_async(url):
    """
    Capture a high-definition screenshot of the specified URL using Playwright.
    This uses a full browser instance to properly render JavaScript and bypass anti-scraping measures.
    
    Args:
        url (str): The URL to capture
        
    Returns:
        str: Path to the saved screenshot file, or None if failed
    """
    try:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{timestamp}_{url.split('/')[-1]}.png"
        filepath = os.path.join(SCREENSHOT_DIR, filename)
        
        logger.info(f"Capturing screenshot from {url} using Playwright")
        
        # Use Playwright to capture a screenshot
        try:
            # Set browser executable path to use the system installed Chromium
            chromium_path = subprocess.run(
                ["which", "chromium"], 
                capture_output=True, 
                text=True
            ).stdout.strip()
            
            logger.info(f"Using Chromium from: {chromium_path}")
            
            async with async_playwright() as p:
                # Launch browser with executable path
                browser = await p.chromium.launch(
                    headless=True,
                    executable_path=chromium_path if chromium_path else None
                )
                
                # Set up context with desktop viewport and realistic user agent
                context = await browser.new_context(
                    viewport={'width': 1920, 'height': 1080},
                    user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
                )
                
                # Create page and navigate to URL
                page = await context.new_page()
                
                # Set extra headers to appear more like a real browser
                await page.set_extra_http_headers({
                    "Accept-Language": "en-US,en;q=0.9",
                    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
                    "sec-ch-ua": '"Chromium";v="120", "Google Chrome";v="120"',
                    "sec-ch-ua-mobile": "?0",
                    "sec-ch-ua-platform": '"Windows"',
                })
                
                # Navigate to the target URL and wait until network is idle
                await page.goto(url, wait_until='networkidle', timeout=90000)
                
                # Wait for the page to fully render (important for JavaScript-heavy sites)
                await page.wait_for_timeout(8000)
                
                # Take the screenshot
                await page.screenshot(path=filepath, full_page=True)
                
                # Close the browser
                await browser.close()
                
                logger.info(f"Screenshot successfully saved to {filepath}")
                return filepath
                
        except Exception as e:
            logger.error(f"Playwright screenshot failed: {str(e)}")
            return None
            
    except Exception as e:
        logger.error(f"Error capturing screenshot: {str(e)}")
        return None

def take_screenshot(url):
    """
    Synchronous wrapper for take_screenshot_async.
    
    Args:
        url (str): The URL to capture
        
    Returns:
        str: Path to the saved screenshot file, or None if failed
    """
    try:
        return asyncio.run(take_screenshot_async(url))
    except Exception as e:
        logger.error(f"Error in synchronous screenshot wrapper: {str(e)}")
        return None

def capture_screenshot(url, lottery_type=None):
    """
    Capture a screenshot from the specified URL and save metadata to database.
    
    This function takes a proper screenshot using Playwright with Chromium to bypass 
    anti-scraping measures on lottery websites. The screenshot is then sent to 
    AI-powered OCR for data extraction.
    
    Args:
        url (str): The URL to capture
        lottery_type (str, optional): The type of lottery. If None, extracted from URL.
        
    Returns:
        str: Path to the saved screenshot file, or None if failed
    """
    # Extract lottery type from URL if not provided
    if not lottery_type:
        lottery_type = extract_lottery_type_from_url(url)
    
    # Run screenshot/content capture function
    filepath = take_screenshot(url)
    
    if filepath:
        # Save content info to database
        screenshot = Screenshot(
            url=url,
            lottery_type=lottery_type,
            timestamp=datetime.utcnow(),
            path=filepath,
            processed=False
        )
        
        db.session.add(screenshot)
        db.session.commit()
        
        logger.info(f"Content capture record saved to database with ID {screenshot.id}")
        return filepath
    
    return None

def extract_lottery_type_from_url(url):
    """Extract lottery type from the URL"""
    url_lower = url.lower()
    
    if 'lotto-plus-1' in url_lower:
        return 'Lotto Plus 1'
    elif 'lotto-plus-2' in url_lower:
        return 'Lotto Plus 2'
    elif 'powerball-plus' in url_lower:
        return 'Powerball Plus'
    elif 'powerball' in url_lower:
        return 'Powerball'
    elif 'daily-lotto' in url_lower:
        return 'Daily Lotto'
    elif 'lotto' in url_lower:
        return 'Lotto'
    else:
        return 'Unknown'

def get_unprocessed_screenshots():
    """Get all unprocessed screenshots from the database"""
    return Screenshot.query.filter_by(processed=False).all()

def mark_screenshot_as_processed(screenshot_id):
    """Mark a screenshot as processed in the database"""
    screenshot = Screenshot.query.get(screenshot_id)
    if screenshot:
        screenshot.processed = True
        db.session.commit()
        logger.info(f"Screenshot {screenshot_id} marked as processed")
