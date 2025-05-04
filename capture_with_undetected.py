#!/usr/bin/env python3
"""
Script to capture lottery screenshots using undetected_chromedriver.

This script uses undetected_chromedriver which is specifically designed to
bypass bot detection systems like Cloudflare, Imperva, etc.
"""
import os
import sys
import time
import random
import logging
import uuid
import json
import traceback
from datetime import datetime
from urllib.parse import urlparse
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('logs/undetected_capture.log')
    ]
)
logger = logging.getLogger(__name__)

# Ensure necessary directories exist
SCREENSHOT_DIR = os.path.join(os.getcwd(), 'screenshots')
COOKIES_DIR = os.path.join(os.getcwd(), 'cookies')
os.makedirs(SCREENSHOT_DIR, exist_ok=True)
os.makedirs(COOKIES_DIR, exist_ok=True)
os.makedirs('logs', exist_ok=True)

# Add current directory to path (for importing models)
sys.path.append(os.getcwd())

# Import application modules
from models import db, Screenshot, ScheduleConfig

# South African browser language preferences
ZA_LANGUAGES = ['en-ZA', 'en', 'af']

def create_app_context():
    """Create and return a Flask app context."""
    from main import app
    return app.app_context()

def save_screenshot_to_database(url, lottery_type, filepath, img_filepath=None):
    """Save screenshot information to the database."""
    try:
        with create_app_context():
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
            return screenshot.id
    except Exception as e:
        logger.error(f"Database error when saving screenshot: {str(e)}")
        logger.error(traceback.format_exc())
        try:
            db.session.rollback()
        except:
            pass
        raise

def capture_with_undetected_chromedriver(url, lottery_type, retry_count=0, headless=True):
    """
    Capture screenshot using undetected_chromedriver.
    
    Args:
        url (str): URL to capture
        lottery_type (str): Type of lottery
        retry_count (int): Current retry attempt
        headless (bool): Whether to run in headless mode
        
    Returns:
        tuple: (html_path, screenshot_path, success)
    """
    # Import here to avoid slow startup time
    import undetected_chromedriver as uc
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    from selenium.common.exceptions import TimeoutException, WebDriverException
    import selenium.common.exceptions as exceptions
    
    # Maximum retries
    MAX_RETRIES = 3
    if retry_count >= MAX_RETRIES:
        logger.error(f"Maximum retries ({MAX_RETRIES}) exceeded for {url}")
        return None, None, False
    
    # Generate unique filenames
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    unique_id = str(uuid.uuid4())[:8]
    html_filename = f"{lottery_type.replace(' ', '_')}_{timestamp}_{unique_id}.html"
    img_filename = f"{lottery_type.replace(' ', '_')}_{timestamp}_{unique_id}.png"
    html_path = os.path.join(SCREENSHOT_DIR, html_filename)
    img_path = os.path.join(SCREENSHOT_DIR, img_filename)
    
    # Get domain for cookies
    domain = urlparse(url).netloc
    cookie_file = os.path.join(COOKIES_DIR, f"ud_{domain.replace('.', '_')}.json")
    
    logger.info(f"Capturing {url} with undetected-chromedriver (try {retry_count+1}/{MAX_RETRIES})")
    
    driver = None
    try:
        # Configure Chrome options
        options = uc.ChromeOptions()
        if headless:
            options.add_argument('--headless')
        
        # South African browser configuration
        options.add_argument('--lang=en-ZA,en;q=0.9,af;q=0.8')
        options.add_argument('--disable-blink-features=AutomationControlled')
        options.add_argument('--disable-extensions')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-infobars')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--disable-browser-side-navigation')
        options.add_argument('--disable-features=IsolateOrigins,site-per-process')
        options.add_argument('--disable-gpu')
        
        # Set timezone to South Africa
        options.add_argument('--timezone=Africa/Johannesburg')
        
        # Random screen size (popular South African resolutions)
        screen_sizes = [
            (1366, 768),  # Common laptop (40% of ZA users)
            (1920, 1080), # FHD desktop (30%)
            (1536, 864),  # Common laptop variant (10%)
            (1440, 900)   # MacBook Pro (8%)
        ]
        screen = random.choice(screen_sizes)
        options.add_argument(f'--window-size={screen[0]},{screen[1]}')
        
        # Find Chrome binary
        chrome_paths = [
            # Replit-specific paths
            "/nix/store/zi4f80l169xlmivz8vja8wlphq74qqk0-chromium-125.0.6422.141/bin/chromium",
            "/nix/store/chromium/bin/chromium",
            # Common Linux paths
            "/usr/bin/chromium",
            "/usr/bin/chromium-browser",
            "/usr/bin/google-chrome",
            "/usr/bin/google-chrome-stable"
        ]
        
        chrome_binary = None
        for path in chrome_paths:
            if os.path.exists(path):
                chrome_binary = path
                logger.info(f"Found Chrome binary at {path}")
                break
        
        if chrome_binary:
            options.binary_location = chrome_binary
        
        # Initialize driver with specific driver configuration
        try:
            driver = uc.Chrome(options=options)
        except TypeError as e:
            if "Binary Location Must be a String" in str(e):
                # Try again with a simplified approach 
                logger.info("Falling back to simplified driver initialization")
                driver = uc.Chrome(use_subprocess=True, headless=headless)
        driver.set_page_load_timeout(60)  # 60 second timeout
        
        # Load cookies if they exist
        if os.path.exists(cookie_file):
            try:
                # Need to visit the domain first before setting cookies
                driver.get(f"https://{domain}")
                time.sleep(2)  # Wait for page to load
                
                with open(cookie_file, 'r') as f:
                    cookies = json.load(f)
                
                for cookie in cookies:
                    # Skip if missing required fields
                    if not all(k in cookie for k in ["name", "value"]):
                        continue
                    
                    # Fix cookie expiry format
                    if 'expiry' in cookie and isinstance(cookie['expiry'], float):
                        cookie['expiry'] = int(cookie['expiry'])
                    
                    try:
                        driver.add_cookie(cookie)
                    except exceptions.InvalidCookieDomainException:
                        # Skip cookies that don't match the current domain
                        pass
                
                logger.info(f"Loaded {len(cookies)} cookies for {domain}")
            except Exception as e:
                logger.warning(f"Error loading cookies: {str(e)}")
        
        # Navigate to URL with added jitter
        logger.info(f"Navigating to {url}")
        driver.get(url)
        
        # Wait for initial page load with random delay
        time.sleep(random.uniform(3, 6))
        
        # Handle cookie consent popups
        cookie_consent_xpaths = [
            "//button[contains(text(), 'Accept')]",
            "//button[contains(text(), 'Accept all')]",
            "//button[contains(text(), 'I agree')]",
            "//button[contains(text(), 'Allow all')]",
            "//button[contains(text(), 'Got it')]",
            "//button[contains(text(), 'OK')]",
            "//button[contains(text(), 'Allow')]",
            "//button[contains(text(), 'Agree')]",
            "//button[contains(text(), 'Aanvaar')]",  # Afrikaans
            "//a[contains(text(), 'Accept')]",
            "//a[contains(text(), 'Accept all')]",
            "//*[@id='onetrust-accept-btn-handler']",
            "//*[@id='accept-all-cookies-button']",
            "//div[contains(@class, 'cookie-consent')]//button",
            "//div[contains(@class, 'cookie-banner')]//button"
        ]
        
        # Try each consent button selector
        cookie_handled = False
        for xpath in cookie_consent_xpaths:
            try:
                buttons = driver.find_elements(By.XPATH, xpath)
                if buttons and len(buttons) > 0:
                    # Try to find an "accept" button in the collection
                    accept_button = None
                    for btn in buttons:
                        if btn.is_displayed() and any(term in btn.text.lower() for term in ['accept', 'agree', 'allow', 'ok', 'got it']):
                            accept_button = btn
                            break
                    
                    # If found, click it
                    if accept_button:
                        logger.info(f"Clicking cookie consent button: {accept_button.text}")
                        accept_button.click()
                        cookie_handled = True
                        time.sleep(random.uniform(1, 3))
                        break
                    # If no accept button found, click the first visible button
                    elif buttons[0].is_displayed():
                        logger.info("Clicking first visible button in cookie dialog")
                        buttons[0].click()
                        cookie_handled = True
                        time.sleep(random.uniform(1, 3))
                        break
            except Exception as e:
                logger.debug(f"Error handling cookie consent with {xpath}: {str(e)}")
        
        # Log if we handled cookies
        if cookie_handled:
            logger.info("Successfully handled cookie consent")
        else:
            logger.info("No cookie consent popup detected or unable to interact with it")
        
        # Simulate human-like scrolling
        total_height = driver.execute_script("return document.body.scrollHeight")
        viewport_height = driver.execute_script("return window.innerHeight")
        
        # Scroll down slowly in steps with random pauses
        current_position = 0
        scroll_steps = random.randint(5, 12)  # Random number of scroll steps
        for i in range(scroll_steps):
            # Calculate scroll percentage with randomization
            scroll_pct = (i + 1) / scroll_steps
            target_position = int(total_height * scroll_pct * random.uniform(0.9, 1.1))
            
            # Smooth scroll by breaking it into micro-steps
            micro_steps = random.randint(3, 8)
            step_size = (target_position - current_position) / micro_steps
            
            for j in range(micro_steps):
                next_pos = current_position + step_size
                driver.execute_script(f"window.scrollTo(0, {int(next_pos)})")
                time.sleep(random.uniform(0.1, 0.3))  # Short pause between micro-scrolls
                current_position = next_pos
            
            # Longer pause at each major scroll position (as if reading content)
            pause_time = random.uniform(1, 3)
            logger.debug(f"Scrolled to {int(current_position)}px ({int(scroll_pct*100)}%), pausing for {pause_time:.1f}s")
            time.sleep(pause_time)
            
            # Occasionally scroll back up a bit (very human-like behavior)
            if random.random() < 0.3:  # 30% chance
                scroll_back = random.uniform(0.1, 0.3)  # Scroll back 10-30%
                back_position = int(current_position * (1 - scroll_back))
                driver.execute_script(f"window.scrollTo(0, {back_position})")
                logger.debug(f"Scrolled back to {back_position}px")
                time.sleep(random.uniform(0.5, 1.5))
                
                # Then continue from where we left off
                driver.execute_script(f"window.scrollTo(0, {int(current_position)})")
                time.sleep(random.uniform(0.5, 1))
        
        # Final scroll to bottom and wait
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight)")
        time.sleep(random.uniform(2, 4))
        
        # Get page content
        page_content = driver.page_source
        
        # Save HTML to file
        with open(html_path, 'w', encoding='utf-8') as f:
            f.write(page_content)
        logger.info(f"Saved HTML to {html_path}")
        
        # Take a screenshot
        driver.save_screenshot(img_path)
        logger.info(f"Saved screenshot to {img_path}")
        
        # Save cookies for future sessions
        try:
            cookies = driver.get_cookies()
            with open(cookie_file, 'w') as f:
                json.dump(cookies, f)
            logger.info(f"Saved {len(cookies)} cookies to {cookie_file}")
        except Exception as e:
            logger.warning(f"Error saving cookies: {str(e)}")
        
        # Save to database
        try:
            save_screenshot_to_database(url, lottery_type, html_path, img_path)
        except Exception as db_error:
            logger.error(f"Database error: {str(db_error)}")
            # Continue anyway as we have the files
        
        return html_path, img_path, True
    
    except (TimeoutException, WebDriverException) as e:
        logger.error(f"Chrome driver error: {str(e)}")
        
        # Use exponential backoff for retries
        wait_time = 5 * (2 ** retry_count) + random.random() * 10
        logger.info(f"Retrying in {wait_time:.1f} seconds (attempt {retry_count+1})")
        time.sleep(wait_time)
        
        # Retry with new session
        return capture_with_undetected_chromedriver(url, lottery_type, retry_count+1, headless)
        
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        logger.error(traceback.format_exc())
        return None, None, False
        
    finally:
        # Always close the driver
        if driver:
            try:
                driver.quit()
            except:
                pass

def get_missing_urls():
    """Get all URLs that don't have screenshots."""
    with create_app_context():
        # Get all URLs from schedule config
        all_configs = db.session.query(ScheduleConfig).all()
        
        # Check which ones don't have screenshots
        missing_urls = []
        for config in all_configs:
            # See if there's a screenshot for this URL
            screenshot = db.session.query(Screenshot).filter(
                Screenshot.url == config.url
            ).first()
            
            if not screenshot:
                missing_urls.append({
                    'url': config.url,
                    'lottery_type': config.lottery_type
                })
                
        return missing_urls

def capture_url(url, lottery_type):
    """Capture a single URL."""
    logger.info(f"Capturing {lottery_type} from {url}")
    result = capture_with_undetected_chromedriver(url, lottery_type, headless=True)
    if result and all(result):
        logger.info(f"Successfully captured {lottery_type}")
        return True
    else:
        logger.error(f"Failed to capture {lottery_type}")
        return False

def capture_missing():
    """Capture all missing URLs."""
    missing = get_missing_urls()
    
    if not missing:
        logger.info("No missing URLs! All URLs have screenshots.")
        return True
    
    logger.info(f"Found {len(missing)} missing URLs. Starting capture...")
    
    # Sort by lottery type
    missing = sorted(missing, key=lambda x: x['lottery_type'])
    
    success_count = 0
    for url_info in missing:
        # Add a significant delay between captures to avoid detection
        delay = random.uniform(30, 60)
        logger.info(f"Waiting {delay:.1f} seconds before next capture")
        time.sleep(delay)
        
        # Capture URL
        if capture_url(url_info['url'], url_info['lottery_type']):
            success_count += 1
    
    logger.info(f"Captured {success_count} out of {len(missing)} missing URLs")
    return success_count == len(missing)

def capture_all(force=False):
    """Capture all URLs, optionally forcing recapture of existing ones."""
    with create_app_context():
        # Get all URLs from schedule config
        all_configs = db.session.query(ScheduleConfig).all()
        
        if force:
            # Delete existing screenshots
            for config in all_configs:
                existing = db.session.query(Screenshot).filter(
                    Screenshot.url == config.url
                ).all()
                
                for screenshot in existing:
                    logger.info(f"Deleting existing screenshot {screenshot.id} for {config.lottery_type}")
                    db.session.delete(screenshot)
                
            db.session.commit()
        
        # Capture all URLs
        logger.info(f"Capturing all {len(all_configs)} URLs")
        
        # Sort by lottery type
        all_configs = sorted(all_configs, key=lambda x: x.lottery_type)
        
        success_count = 0
        for config in all_configs:
            # Add a significant delay between captures to avoid detection
            delay = random.uniform(30, 60)
            logger.info(f"Waiting {delay:.1f} seconds before capturing {config.lottery_type}")
            time.sleep(delay)
            
            # Capture URL
            if capture_url(config.url, config.lottery_type):
                success_count += 1
        
        logger.info(f"Captured {success_count} out of {len(all_configs)} URLs")
        return success_count == len(all_configs)

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Capture lottery screenshots using undetected-chromedriver")
    parser.add_argument('--url', type=str, help='Specific URL to capture')
    parser.add_argument('--type', type=str, help='Lottery type for the URL')
    parser.add_argument('--missing', action='store_true', help='Capture all missing URLs')
    parser.add_argument('--all', action='store_true', help='Capture all URLs')
    parser.add_argument('--force', action='store_true', help='Force recapture of all URLs')
    parser.add_argument('--no-headless', action='store_true', help='Disable headless mode')
    
    args = parser.parse_args()
    
    if args.url and args.type:
        # Capture specific URL
        success = capture_url(args.url, args.type)
    elif args.missing:
        # Capture all missing URLs
        success = capture_missing()
    elif args.all or args.force:
        # Capture all URLs
        success = capture_all(force=args.force)
    else:
        parser.print_help()
        sys.exit(1)
    
    if success:
        logger.info("Capture completed successfully")
        sys.exit(0)
    else:
        logger.error("Capture completed with errors")
        sys.exit(1)