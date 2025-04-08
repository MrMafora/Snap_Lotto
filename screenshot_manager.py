"""
Screenshot manager for capturing lottery website screenshots
"""
import os
import logging
import asyncio
from datetime import datetime
import traceback
from pathlib import Path
from playwright.async_api import async_playwright
from playwright.sync_api import sync_playwright
from models import db, Screenshot

logger = logging.getLogger(__name__)

# Create directory for screenshots if it doesn't exist
SCREENSHOT_DIR = os.path.join(os.getcwd(), 'screenshots')
os.makedirs(SCREENSHOT_DIR, exist_ok=True)

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
    try:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{timestamp}_{url.split('/')[-1]}.png"
        filepath = os.path.join(SCREENSHOT_DIR, filename)
        
        logger.info(f"Capturing screenshot from {url} using Playwright (sync)")
        
        chromium_path = "/nix/store/zi4f80l169xlmivz8vja8wlphq74qqk0-chromium-125.0.6422.141/bin/chromium"
        if os.path.exists(chromium_path):
            logger.info(f"Using Chromium from: {chromium_path}")
        
        # Use Playwright to capture screenshot
        with sync_playwright() as p:
            browser_type = p.chromium
            
            try:
                browser = browser_type.launch(
                    headless=True,
                    executable_path=chromium_path if os.path.exists(chromium_path) else None
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
                
                # Navigate and wait for the page to fully load
                page.goto(url, wait_until='networkidle')
                
                # Scroll down to ensure all content is loaded
                page.evaluate('window.scrollTo(0, document.body.scrollHeight)')
                page.wait_for_timeout(1000)  # Wait a second for any animations
                
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
    
    try:
        # Try async method first
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        
        filepath, screenshot_data = loop.run_until_complete(capture_screenshot_async(url))
        
        # If async failed, try sync method
        if not filepath:
            filepath, screenshot_data = capture_screenshot_sync(url)
        
        if filepath and screenshot_data:
            # Save screenshot metadata to database
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
            
            return filepath, None  # Return None for extracted data to use OCR
    except Exception as e:
        logger.error(f"Error in capture_screenshot: {str(e)}")
    
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
