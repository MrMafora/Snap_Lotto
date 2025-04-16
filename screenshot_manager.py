"""
Screenshot manager for capturing lottery website screenshots
"""
import os
import logging
import asyncio
import random
import time
from datetime import datetime
import traceback
from pathlib import Path
import threading
import shutil
import json
from urllib.parse import urlparse
from playwright.async_api import async_playwright
from playwright.sync_api import sync_playwright
from sqlalchemy import func
from models import db, Screenshot, ScheduleConfig
from logger import setup_logger

# Set up module-specific logger
logger = setup_logger(__name__, level=logging.INFO)

# Create directory for screenshots if it doesn't exist
SCREENSHOT_DIR = os.path.join(os.getcwd(), 'screenshots')
os.makedirs(SCREENSHOT_DIR, exist_ok=True)

# Create directory for cookies if it doesn't exist
COOKIES_DIR = os.path.join(os.getcwd(), 'cookies')
os.makedirs(COOKIES_DIR, exist_ok=True)

# Thread semaphore to limit concurrent screenshots
# This prevents "can't start new thread" errors by limiting resource usage
MAX_CONCURRENT_THREADS = 3
screenshot_semaphore = threading.Semaphore(MAX_CONCURRENT_THREADS)

# List of user agents to rotate through randomly
USER_AGENTS = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/115.0',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.5 Safari/605.1.15',
    'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 Edg/120.0.0.0'
]

# Human-like scroll behavior parameters
SCROLL_BEHAVIOR = [
    {'distance': 0.2, 'delay': 0.5},  # Scroll 20% with 0.5s delay
    {'distance': 0.3, 'delay': 0.7},  # Scroll 30% with 0.7s delay
    {'distance': 0.5, 'delay': 0.3},  # Scroll 50% with 0.3s delay
    {'distance': 0.7, 'delay': 0.6},  # Scroll 70% with 0.6s delay
    {'distance': 1.0, 'delay': 0.8}   # Scroll 100% with 0.8s delay
]

# Maximum number of retry attempts
MAX_RETRIES = 3

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

def capture_screenshot_sync(url, retry_count=0):
    """
    Enhanced synchronous version of screenshot capture using Playwright sync API.
    Includes anti-detection techniques and human-like behavior.
    
    Args:
        url (str): The URL to capture
        retry_count (int): Current retry attempt, used for recursive retries
        
    Returns:
        tuple: (filepath, screenshot_data, zoom_filepath) or (None, None, None) if failed
    """
    import time

    # If we've exceeded max retries, give up
    if retry_count >= MAX_RETRIES:
        logger.error(f"Maximum retry attempts ({MAX_RETRIES}) exceeded for {url}")
        return None, None, None

    try:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{timestamp}_{url.split('/')[-1]}.png"
        filepath = os.path.join(SCREENSHOT_DIR, filename)
        
        logger.info(f"Capturing screenshot from {url} using Playwright (sync) - Attempt {retry_count + 1}/{MAX_RETRIES}")
        
        # Get domain for cookie storage
        domain = urlparse(url).netloc
        cookie_file = os.path.join(COOKIES_DIR, f"{domain.replace('.', '_')}.json")
        
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
        
        # Choose a random user agent
        user_agent = random.choice(USER_AGENTS)
        logger.debug(f"Using user agent: {user_agent}")
        
        # Random screen size to prevent fingerprinting
        screen_width = random.choice([1280, 1366, 1440, 1920])
        screen_height = random.choice([800, 900, 1024, 1080])
        
        # Use Playwright to capture screenshot with built-in timeouts
        with sync_playwright() as p:
            browser_type = p.chromium
            
            try:
                # Launch with specific arguments to prevent detection
                browser = browser_type.launch(
                    headless=True,
                    executable_path=chromium_path,
                    args=[
                        "--disable-blink-features=AutomationControlled",
                        "--disable-features=IsolateOrigins,site-per-process",
                        "--disable-site-isolation-trials",
                        f"--window-size={screen_width},{screen_height}",
                        "--no-sandbox",
                        "--disable-setuid-sandbox"
                    ]
                )
                
                # Create a new context with specific settings to appear more human-like
                context = browser.new_context(
                    viewport={'width': screen_width, 'height': screen_height},
                    user_agent=user_agent,
                    locale=random.choice(['en-US', 'en-GB', 'en-CA', 'en-ZA']),
                    timezone_id=random.choice(['America/New_York', 'Europe/London', 'Africa/Johannesburg']),
                    geolocation={"latitude": -26.2041, "longitude": 28.0473},  # Johannesburg coordinates
                    permissions=['geolocation']
                )
                
                # Load cookies from previous sessions if available
                if os.path.exists(cookie_file):
                    try:
                        with open(cookie_file, 'r') as f:
                            cookies = json.load(f)
                            context.add_cookies(cookies)
                            logger.info(f"Loaded {len(cookies)} cookies for {domain}")
                    except Exception as e:
                        logger.warning(f"Error loading cookies: {str(e)}")
                
                # Create a new page
                page = context.new_page()
                
                # Execute stealth script to prevent detection
                # This script modifies navigator properties to appear as a real browser
                page.evaluate("""() => {
                    // Overwrite the 'webdriver' property
                    Object.defineProperty(navigator, 'webdriver', {
                        get: () => false,
                        configurable: true
                    });
                    
                    // Overwrite plugins to add some fake ones
                    Object.defineProperty(navigator, 'plugins', {
                        get: () => {
                            return [
                                {
                                    name: 'Chrome PDF Plugin',
                                    description: 'Portable Document Format',
                                    filename: 'internal-pdf-viewer'
                                },
                                {
                                    name: 'Chrome PDF Viewer',
                                    description: '',
                                    filename: 'mhjfbmdgcfjbbpaeojofohoefgiehjai'
                                },
                                {
                                    name: 'Native Client',
                                    description: '',
                                    filename: 'internal-nacl-plugin'
                                }
                            ];
                        },
                        configurable: true
                    });
                    
                    // Add language plugins
                    Object.defineProperty(navigator, 'languages', {
                        get: () => ['en-US', 'en'],
                        configurable: true
                    });
                }""")
                
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
                    "DNT": "1",
                    "Cache-Control": "max-age=0",
                    "Referer": "https://www.google.com/"
                })
                
                # Add randomized delays to appear more human-like
                # Random initial wait before accessing the site (250-750ms)
                page.wait_for_timeout(random.randint(250, 750))
                
                # Navigate and wait for the page to fully load with a timeout
                start_time = time.time()
                max_time = 30  # Maximum time in seconds
                
                try:
                    # Try to navigate with a 20-second timeout
                    page.goto(url, wait_until='domcontentloaded', timeout=20000)
                    
                    # Wait a randomized amount of time for additional resources to load
                    # This makes it appear more human-like, instead of immediately interacting with the page
                    page.wait_for_timeout(random.randint(1000, 2000))
                    
                except Exception as e:
                    # If timeout occurs, log but continue - we might still get a partial page
                    logger.warning(f"Page navigation timeout for {url}: {str(e)}")
                    
                    # Since we caught the timeout, let's try to continue with whatever page was loaded
                    if time.time() - start_time > max_time:
                        logger.error("Exceeded maximum time, aborting")
                        
                        # Close browser to clean up resources
                        browser.close()
                        
                        # If this was a timeout, retry with a different approach
                        if "timeout" in str(e).lower():
                            logger.info(f"Retrying with different wait strategy (attempt {retry_count + 1})")
                            return capture_screenshot_sync(url, retry_count + 1)
                        
                        raise TimeoutError("Screenshot capture exceeded maximum time")
                
                # Check if we were blocked or got a CAPTCHA
                if page.query_selector('div:has-text("captcha")') or page.query_selector('div:has-text("CAPTCHA")'):
                    logger.warning(f"CAPTCHA detected on {url}")
                    
                    # Close browser
                    browser.close()
                    
                    # Retry with different user agent and longer wait
                    logger.info(f"Retrying with different user agent (attempt {retry_count + 1})")
                    return capture_screenshot_sync(url, retry_count + 1)
                    
                # Perform human-like scrolling with random behavior
                try:
                    # Get page height
                    page_height = page.evaluate('document.body.scrollHeight')
                    current_position = 0
                    
                    # Apply each scroll step with varied timing and distance
                    for scroll_step in random.sample(SCROLL_BEHAVIOR, len(SCROLL_BEHAVIOR)):
                        # Calculate scroll distance for this step
                        target_position = int(page_height * scroll_step['distance'])
                        
                        # Scroll to the new position
                        page.evaluate(f'window.scrollTo(0, {target_position})')
                        
                        # Wait for the specified delay
                        page.wait_for_timeout(int(scroll_step['delay'] * 1000))
                        
                        # Update current position
                        current_position = target_position
                    
                    # Randomly scroll back up a bit to simulate looking at something
                    if random.random() < 0.7:  # 70% chance to scroll back up
                        scroll_back = random.uniform(0.2, 0.6)  # Scroll back 20-60%
                        scroll_up_pos = int(current_position * (1 - scroll_back))
                        page.evaluate(f'window.scrollTo(0, {scroll_up_pos})')
                        page.wait_for_timeout(random.randint(800, 1500))
                        
                        # Then scroll back to bottom
                        page.evaluate(f'window.scrollTo(0, {current_position})')
                        page.wait_for_timeout(random.randint(500, 1000))
                except Exception as e:
                    logger.warning(f"Error during human-like scrolling: {str(e)}")
                
                # Save the full page screenshot
                page.screenshot(path=filepath, full_page=True)
                logger.info(f"Full screenshot saved to {filepath}")
                
                # Create a separate zoomed-in screenshot of the main data
                try:
                    # For results pages, try to capture the specific lottery results box
                    if 'results' in url.lower():
                        # Look for the main results container with lottery numbers and divisions
                        main_content = None
                        
                        # Try several potential selectors for the main content
                        selectors = [
                            '.results-section', 
                            '.lottery-results', 
                            '.main-content',
                            '.results-container',
                            '#results-container',
                            'table.results-table',
                            'div.container'
                        ]
                        
                        for selector in selectors:
                            try:
                                main_content = page.query_selector(selector)
                                if main_content:
                                    logger.info(f"Found main content with selector: {selector}")
                                    break
                            except:
                                continue
                        
                        # If we couldn't find a specific selector, try to find the red-bordered section
                        # by looking for typical content like lottery numbers or division tables
                        if not main_content:
                            # Look for lottery number balls (they usually have specific classes)
                            ball_selectors = [
                                '.lottery-ball', 
                                '.ball',
                                '.number-ball',
                                '.winning-number',
                                'span[class*="ball"]',
                                'div[class*="ball"]'
                            ]
                            
                            for selector in ball_selectors:
                                try:
                                    balls = page.query_selector_all(selector)
                                    if balls and len(balls) > 5:  # Typical lottery has at least 6 numbers
                                        # Get the parent element that contains all balls
                                        parent = page.evaluate('el => el.parentElement.parentElement', balls[0])
                                        if parent:
                                            main_content = parent
                                            logger.info(f"Found lottery balls with selector: {selector}")
                                            break
                                except:
                                    continue
                        
                        # As a fallback, try using a more generic approach by looking for content
                        # with lottery keywords like "winning numbers" or "division"
                        if not main_content:
                            try:
                                # Look for text content that indicates lottery results
                                main_content = page.query_selector('div:has-text("WINNING NUMBERS"), div:has-text("Divisions"), div:has-text("DIVISION"), table:has-text("WINNERS")')
                                logger.info("Found main content using text content search")
                            except:
                                pass
                        
                        # If we found content to zoom in on
                        if main_content:
                            # Use a custom filename for the zoomed screenshot
                            zoom_filename = f"{timestamp}_{url.split('/')[-1]}_zoomed.png"
                            zoom_filepath = os.path.join(SCREENSHOT_DIR, zoom_filename)
                            
                            # Take a screenshot of just this element with a bit of padding
                            bounding_box = main_content.bounding_box()
                            if bounding_box:
                                # Add 20px padding around the element
                                clip = {
                                    'x': max(0, bounding_box['x'] - 20),
                                    'y': max(0, bounding_box['y'] - 20),
                                    'width': bounding_box['width'] + 40,
                                    'height': bounding_box['height'] + 40
                                }
                                
                                # Take the zoomed screenshot
                                page.screenshot(path=zoom_filepath, clip=clip)
                                logger.info(f"Zoomed screenshot saved to {zoom_filepath}")
                                
                                # Save cookies from this session for future use
                                try:
                                    cookies = context.cookies()
                                    with open(cookie_file, 'w') as f:
                                        json.dump(cookies, f)
                                    logger.info(f"Saved {len(cookies)} cookies for {domain}")
                                except Exception as e:
                                    logger.warning(f"Error saving cookies: {str(e)}")
                                
                                # Read the screenshot data
                                with open(filepath, 'rb') as f:
                                    screenshot_bytes = f.read()
                                
                                browser.close()
                                # Return both filepaths so they can be saved to the database
                                return filepath, screenshot_bytes, zoom_filepath
                        else:
                            logger.warning("Could not find a specific content area to zoom in on")
                
                except Exception as e:
                    logger.error(f"Error creating zoomed screenshot: {str(e)}")
                    # Continue with the regular screenshot even if zoomed fails
                
                logger.info(f"Screenshot process completed for {url}")
                
                # Save cookies from this session for future use
                try:
                    cookies = context.cookies()
                    with open(cookie_file, 'w') as f:
                        json.dump(cookies, f)
                    logger.info(f"Saved {len(cookies)} cookies for {domain}")
                except Exception as e:
                    logger.warning(f"Error saving cookies: {str(e)}")
                
                # If we got this far, we didn't capture a zoomed screenshot yet
                # Read the full screenshot data
                with open(filepath, 'rb') as f:
                    screenshot_data = f.read()
                
                browser.close()
                # Return without zoomed path
                return filepath, screenshot_data, None
                
            except Exception as e:
                logger.error(f"Playwright screenshot capture failed: {str(e)}")
                traceback.print_exc()
                
                # Clean up any browser instances
                try:
                    browser.close()
                except:
                    pass
                
                return None, None, None
            
    except Exception as e:
        logger.error(f"Error capturing screenshot: {str(e)}")
        traceback.print_exc()
        return None, None, None

def capture_screenshot(url, lottery_type=None):
    """
    Capture screenshot of the specified URL and save metadata to database.
    
    This function captures a screenshot using Playwright with Chromium to bypass 
    anti-scraping measures on lottery websites.
    
    Args:
        url (str): The URL to capture
        lottery_type (str, optional): The type of lottery. If None, extracted from URL.
        
    Returns:
        tuple: (filepath, screenshot_data, zoom_filepath) or (None, None, None) if failed
    """
    if not lottery_type:
        lottery_type = extract_lottery_type_from_url(url)
    
    # Use semaphore to limit concurrent screenshot captures
    # This prevents "can't start new thread" errors
    if not screenshot_semaphore.acquire(blocking=True, timeout=300):
        logger.error(f"Could not acquire screenshot semaphore for {lottery_type} after waiting 5 minutes")
        return None, None, None
    
    try:
        # Use the sync method instead of async to avoid event loop issues
        filepath, screenshot_data, zoom_filepath = capture_screenshot_sync(url)
        
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
                            zoomed_path=zoom_filepath,
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
                        zoomed_path=zoom_filepath,
                        processed=False
                    )
                    
                    db.session.add(screenshot)
                    db.session.commit()
                    
                    logger.info(f"Screenshot record saved to database with ID {screenshot.id}")
            except Exception as e:
                logger.error(f"Error saving screenshot to database: {str(e)}")
                traceback.print_exc()
                # Still return the filepath so OCR can be attempted
            
            return filepath, None, zoom_filepath  # Return None for extracted data to use OCR
    except Exception as e:
        logger.error(f"Error in capture_screenshot: {str(e)}")
        traceback.print_exc()
        return None, None, None
    finally:
        # Always release the semaphore in the finally block
        # to ensure it's released even if an exception occurs
        screenshot_semaphore.release()
        logger.debug(f"Released screenshot semaphore for {lottery_type}")
    
    return None, None, None

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
        
def retake_screenshot_by_id(screenshot_id, app=None):
    """
    Retake a specific screenshot by its ID.
    
    Args:
        screenshot_id (int): ID of the screenshot to retake
        app: Flask app context (optional)
    
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        # Add context manager if app is provided
        if app:
            with app.app_context():
                screenshot = Screenshot.query.get(screenshot_id)
        else:
            screenshot = Screenshot.query.get(screenshot_id)
        
        if not screenshot:
            logger.error(f"Screenshot with ID {screenshot_id} not found")
            return False
        
        logger.info(f"Retaking screenshot for {screenshot.url} ({screenshot.lottery_type})")
        
        # Take the screenshot
        success = take_screenshot_threaded(screenshot.url, screenshot.lottery_type)
        
        if success:
            logger.info(f"Successfully retook screenshot for {screenshot.url}")
            return True
        else:
            logger.error(f"Failed to retake screenshot for {screenshot.url}")
            return False
    
    except Exception as e:
        logger.error(f"Error retaking screenshot by ID {screenshot_id}: {str(e)}")
        traceback.print_exc()
        return False
        
def retake_all_screenshots(app=None):
    """
    Retake all screenshots for each configured URL.
    
    Args:
        app: Flask app context (optional)
    
    Returns:
        int: Number of screenshots captured
    """
    try:
        # Add context manager if app is provided
        if app:
            with app.app_context():
                configs = ScheduleConfig.query.filter_by(active=True).all()
        else:
            configs = ScheduleConfig.query.filter_by(active=True).all()
            
        logger.info(f"Retaking screenshots for {len(configs)} configurations")
        count = 0
        
        for config in configs:
            if take_screenshot_threaded(config.url, config.lottery_type):
                count += 1
                
        logger.info(f"Successfully retook {count} screenshots")
        return count
    except Exception as e:
        logger.error(f"Error retaking all screenshots: {str(e)}")
        traceback.print_exc()
        return 0

def take_screenshot_threaded(url, lottery_type, use_thread=True):
    """
    Take a screenshot of the specified URL in a separate thread.
    
    Args:
        url (str): The URL to capture
        lottery_type (str): Type of lottery (used for DB storage)
        use_thread (bool): Whether to use a thread or run synchronously
        
    Returns:
        bool: True if the screenshot was successfully scheduled/taken
    """
    if not url:
        logger.error("Empty URL provided for screenshot")
        return False
        
    try:
        if use_thread:
            # Use a thread to avoid blocking the main thread
            threading.Thread(
                target=_take_screenshot_worker,
                args=(url, lottery_type),
                daemon=True
            ).start()
            return True
        else:
            # Run synchronously
            return _take_screenshot_worker(url, lottery_type)
    except Exception as e:
        logger.error(f"Error scheduling screenshot for {url}: {str(e)}")
        traceback.print_exc()
        return False

def _take_screenshot_worker(url, lottery_type):
    """
    Worker function to take a screenshot of the specified URL.
    Intended to be run in a separate thread.
    
    Args:
        url (str): The URL to capture
        lottery_type (str): Type of lottery
        
    Returns:
        bool: True if successful
    """
    try:
        # Acquire the semaphore to limit concurrent screenshot operations
        with screenshot_semaphore:
            logger.info(f"Taking screenshot of {url} ({lottery_type})")
            
            # Take the screenshot
            filepath, screenshot_data, zoom_filepath = capture_screenshot(url, lottery_type)
            
            if not filepath or not screenshot_data:
                logger.error(f"Failed to capture screenshot for {url}")
                return False
                
            # Save to database
            try:
                # Check if existing screenshot exists for this URL
                existing = Screenshot.query.filter_by(url=url).first()
                
                if existing:
                    # Update existing record
                    existing.path = filepath
                    existing.zoomed_path = zoom_filepath
                    existing.timestamp = datetime.now()
                    existing.processed = False
                    db.session.commit()
                    
                    logger.info(f"Updated existing screenshot record for {url}")
                    screenshot_id = existing.id
                else:
                    # Create new record
                    screenshot = Screenshot(
                        url=url,
                        lottery_type=lottery_type,
                        path=filepath,
                        zoomed_path=zoom_filepath,
                        timestamp=datetime.now(),
                        processed=False
                    )
                    
                    db.session.add(screenshot)
                    db.session.commit()
                    
                    logger.info(f"Created new screenshot record for {url}")
                    screenshot_id = screenshot.id
                
                logger.info(f"Screenshot saved successfully (ID: {screenshot_id})")
                return True
                
            except Exception as e:
                logger.error(f"Error saving screenshot to database: {str(e)}")
                traceback.print_exc()
                return False
            
    except Exception as e:
        logger.error(f"Error in screenshot worker thread: {str(e)}")
        traceback.print_exc()
        return False

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
                                
                        # Delete the files from disk
                        if os.path.exists(screenshot.path):
                            os.remove(screenshot.path)
                            logger.info(f"Deleted old screenshot file: {screenshot.path}")
                            
                        # Delete the zoomed screenshot if it exists
                        if screenshot.zoomed_path and os.path.exists(screenshot.zoomed_path):
                            os.remove(screenshot.zoomed_path)
                            logger.info(f"Deleted old zoomed screenshot file: {screenshot.zoomed_path}")
                        
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
