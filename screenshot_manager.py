import os
import logging
import time
import asyncio
from datetime import datetime
from playwright.async_api import async_playwright
from models import Screenshot, db
from app import app

logger = logging.getLogger(__name__)

# Create directory for screenshots if it doesn't exist
SCREENSHOT_DIR = os.path.join(os.getcwd(), 'screenshots')
os.makedirs(SCREENSHOT_DIR, exist_ok=True)

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
        
        logger.info(f"Capturing high-definition screenshot from {url}")
        
        async with async_playwright() as p:
            # Use Chromium for better compatibility
            browser = await p.chromium.launch(headless=True)
            
            # Create context with realistic viewport and user agent
            context = await browser.new_context(
                viewport={'width': 1920, 'height': 1080},
                user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/96.0.4664.110 Safari/537.36'
            )
            
            # Create new page and navigate to URL
            page = await context.new_page()
            await page.goto(url, wait_until='networkidle', timeout=60000)
            
            # Wait for content to load (lottery numbers should be visible)
            await page.wait_for_timeout(5000)  # 5 seconds to ensure all JS is loaded
            
            # Take screenshot
            await page.screenshot(path=filepath, full_page=True)
            
            # Also save the HTML for backup parsing
            html_filename = f"{timestamp}_{url.split('/')[-1]}.html"
            html_filepath = os.path.join(SCREENSHOT_DIR, html_filename)
            html_content = await page.content()
            with open(html_filepath, 'w', encoding='utf-8') as f:
                f.write(html_content)
            
            # Close browser
            await browser.close()
            
            logger.info(f"High-definition screenshot saved to {filepath}")
            logger.info(f"HTML content also saved to {html_filepath}")
            return filepath
            
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
    Capture content from the specified URL and save metadata to database.
    
    Args:
        url (str): The URL to capture
        lottery_type (str, optional): The type of lottery. If None, extracted from URL.
        
    Returns:
        str: Path to the saved file, or None if failed
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
