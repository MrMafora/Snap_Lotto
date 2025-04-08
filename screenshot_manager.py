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

def take_direct_screenshot(url):
    """
    Use curl to fetch HTML content directly as a fallback to Playwright.
    
    Note: This does not create an actual PNG screenshot,
    but saves the HTML content which contains the lottery data.
    The HTML files are sufficient for data extraction.
    
    Args:
        url (str): The URL to capture
        
    Returns:
        str: Path to the saved HTML file, or None if failed
    """
    try:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        html_filename = f"{timestamp}_{url.split('/')[-1]}.html"
        html_filepath = os.path.join(SCREENSHOT_DIR, html_filename)
        
        logger.info(f"Fetching HTML content directly from {url}")
        
        # Use curl to fetch the HTML with a realistic user agent
        curl_command = [
            'curl', 
            '-A', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/96.0.4664.110 Safari/537.36',
            '-L',  # Follow redirects
            '--max-time', '30',  # Timeout after 30 seconds
            url
        ]
        
        result = subprocess.run(curl_command, capture_output=True, text=True)
        
        if result.returncode == 0 and result.stdout:
            # Save the HTML content
            with open(html_filepath, 'w', encoding='utf-8') as f:
                f.write(result.stdout)
            
            logger.info(f"HTML content saved to {html_filepath}")
            return html_filepath
        else:
            logger.error(f"Error fetching HTML: {result.stderr}")
            return None
            
    except Exception as e:
        logger.error(f"Error in direct screenshot: {str(e)}")
        return None

async def take_screenshot_async(url):
    """
    Capture a high-definition screenshot of the specified URL using Playwright.
    This uses a full browser instance to properly render JavaScript and bypass anti-scraping measures.
    If Playwright fails, falls back to direct HTML fetching.
    
    Args:
        url (str): The URL to capture
        
    Returns:
        str: Path to the saved screenshot file or HTML file, or None if failed
    """
    # Try direct HTML fetching first as a more reliable method
    html_path = take_direct_screenshot(url)
    if html_path:
        return html_path
        
    # If direct fetching fails, we'll try Playwright (though this will likely fail due to dependencies)
    try:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{timestamp}_{url.split('/')[-1]}.png"
        filepath = os.path.join(SCREENSHOT_DIR, filename)
        
        logger.info(f"Attempting Playwright screenshot from {url}")
        
        # If Playwright is available, try using it (though this will likely fail in Replit)
        try:
            async with async_playwright() as p:
                browser = await p.chromium.launch(headless=True)
                context = await browser.new_context(
                    viewport={'width': 1920, 'height': 1080},
                    user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/96.0.4664.110 Safari/537.36'
                )
                page = await context.new_page()
                await page.goto(url, wait_until='networkidle', timeout=60000)
                await page.wait_for_timeout(5000)
                await page.screenshot(path=filepath, full_page=True)
                html_content = await page.content()
                await browser.close()
                
                # Save the HTML
                html_filename = f"{timestamp}_{url.split('/')[-1]}.html"
                html_filepath = os.path.join(SCREENSHOT_DIR, html_filename)
                with open(html_filepath, 'w', encoding='utf-8') as f:
                    f.write(html_content)
                
                logger.info(f"Screenshot saved to {filepath}")
                logger.info(f"HTML content also saved to {html_filepath}")
                return filepath
        except Exception as e:
            logger.error(f"Playwright screenshot failed: {str(e)}")
            return html_path  # Return the HTML path we got earlier
            
    except Exception as e:
        logger.error(f"Error capturing screenshot: {str(e)}")
        return html_path  # Return the HTML path we got earlier, or None if that also failed

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
    
    In the current Replit environment, this primarily saves HTML content 
    rather than actual PNG screenshots, due to system dependency limitations.
    The HTML content contains all necessary data for lottery extraction.
    
    Args:
        url (str): The URL to capture
        lottery_type (str, optional): The type of lottery. If None, extracted from URL.
        
    Returns:
        str: Path to the saved HTML file, or None if failed
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
