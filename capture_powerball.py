#!/usr/bin/env python3
"""
Script to capture the Powerball lottery screenshot.
This version focuses specifically on the Powerball lottery with extra anti-detection measures.
"""
import logging
import os
import sys
import random
import time
from datetime import datetime
from urllib.parse import urlparse
from playwright.sync_api import sync_playwright
from config import Config

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger("capture_powerball")

# Ensure directories exist
SCREENSHOT_DIR = os.path.join(os.getcwd(), 'screenshots')
os.makedirs(SCREENSHOT_DIR, exist_ok=True)
COOKIES_DIR = os.path.join(os.getcwd(), 'cookies')
os.makedirs(COOKIES_DIR, exist_ok=True)

# Configuration
MAX_WAIT_TIME = 120000  # 120 seconds
NAVIGATION_TIMEOUT = 120000  # 120 seconds

def capture_powerball():
    """
    Capture a screenshot of the Powerball lottery results page.
    
    Returns:
        tuple: (success, html_path, img_path)
    """
    lottery_type = "Powerball"
    url = "https://www.nationallottery.co.za/results/powerball"
    
    logger.info(f"Starting Powerball screenshot capture from {url}")
    
    domain = urlparse(url).netloc
    cookie_file = os.path.join(COOKIES_DIR, f"{domain.replace('.', '_')}.json")
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    html_filename = f"{lottery_type}_{timestamp}.html"
    img_filename = f"{lottery_type}_{timestamp}.png"
    
    html_path = os.path.join(SCREENSHOT_DIR, html_filename)
    img_path = os.path.join(SCREENSHOT_DIR, img_filename)
    
    with sync_playwright() as p:
        browser_type = p.chromium
        
        # Launch browser with anti-detection options
        logger.info("Launching browser with stealth options")
        browser = browser_type.launch(
            headless=True,
            args=[
                '--no-sandbox',
                '--disable-setuid-sandbox',
                '--disable-infobars',
                '--window-position=0,0',
                '--ignore-certifcate-errors',
                '--ignore-certifcate-errors-spki-list',
                '--disable-dev-shm-usage',
                '--disable-accelerated-2d-canvas',
                '--disable-gpu',
                '--disable-notifications',
                '--disable-extensions',
                '--disable-component-extensions-with-background-pages',
                f'--window-size={random.choice([1366, 1440, 1536, 1920])},{random.choice([768, 900, 1080])}'
            ],
            chromium_sandbox=False
        )
        
        try:
            # Enhanced browser context with more realistic fingerprinting
            logger.info("Setting up browser context with human-like fingerprinting")
            context = browser.new_context(
                user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
                locale='en-ZA',
                timezone_id='Africa/Johannesburg',
                viewport={'width': 1366, 'height': 768},
                device_scale_factor=1,
                has_touch=False,
                is_mobile=False,
                color_scheme='no-preference',
                reduced_motion='no-preference',
                forced_colors='none',
                accept_downloads=False
            )
            
            # Load cookies if available
            try:
                if os.path.exists(cookie_file):
                    with open(cookie_file, 'r') as f:
                        cookies = eval(f.read())
                        if cookies:
                            context.add_cookies(cookies)
                            logger.info(f"Loaded {len(cookies)} cookies for {domain}")
            except Exception as e:
                logger.warning(f"Error loading cookies: {str(e)}")
            
            # Create a new page
            page = context.new_page()
            
            # Set common headers
            logger.info("Setting realistic browser headers")
            page.set_extra_http_headers({
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.9,en-ZA;q=0.8',
                'Accept-Encoding': 'gzip, deflate, br',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1',
                'Sec-Fetch-Dest': 'document',
                'Sec-Fetch-Mode': 'navigate',
                'Sec-Fetch-Site': 'none',
                'Sec-Fetch-User': '?1',
                'sec-ch-ua': '"Chromium";v="124", "Google Chrome";v="124"',
                'sec-ch-ua-mobile': '?0',
                'sec-ch-ua-platform': '"Windows"',
                'DNT': '1',
            })
            
            # Add subtle pre-navigation delay like a human
            pre_nav_delay = random.uniform(1.5, 3.5)
            logger.info(f"Waiting {pre_nav_delay:.2f} seconds before navigation (human-like)")
            time.sleep(pre_nav_delay)
            
            # Navigate with extended timeout
            logger.info(f"Starting navigation to {url} with timeout {NAVIGATION_TIMEOUT}ms")
            page.set_default_navigation_timeout(NAVIGATION_TIMEOUT)
            page.set_default_timeout(MAX_WAIT_TIME)
            
            # First navigate to homepage to appear more natural
            logger.info("First navigating to homepage (more natural behavior)")
            try:
                page.goto("https://www.nationallottery.co.za/", wait_until='domcontentloaded')
                # Wait like a human would
                time.sleep(random.uniform(3.0, 5.0))
                
                # Click on "Results" link if available
                logger.info("Looking for 'Results' link to click naturally")
                try:
                    if page.locator("text=Results").count() > 0:
                        logger.info("Found 'Results' link, clicking...")
                        page.locator("text=Results").first.click()
                        time.sleep(random.uniform(2.0, 4.0))
                    else:
                        logger.info("No 'Results' link found, navigating directly")
                except Exception as e:
                    logger.warning(f"Error clicking Results link: {str(e)}")
                
                # Now navigate to the actual URL
                logger.info(f"Now navigating to target URL: {url}")
                page.goto(url, wait_until='domcontentloaded', timeout=NAVIGATION_TIMEOUT)
                
            except Exception as e:
                logger.warning(f"Error with initial navigation approach: {str(e)}")
                # Direct navigation fallback
                logger.info("Falling back to direct navigation")
                page.goto(url, wait_until='domcontentloaded', timeout=NAVIGATION_TIMEOUT) 
            
            # Wait for content to stabilize and load fully
            logger.info("Waiting for page to stabilize and load fully")
            time.sleep(random.uniform(5.0, 10.0))
            
            # Take screenshot
            logger.info("Taking screenshot")
            page.screenshot(path=img_path)
            
            # Get the full HTML content
            html_content = page.content()
            with open(html_path, 'w', encoding='utf-8') as f:
                f.write(html_content)
            
            # Save the cookies for future use
            try:
                cookies = context.cookies()
                with open(cookie_file, 'w') as f:
                    f.write(str(cookies))
                    logger.info(f"Saved {len(cookies)} cookies for future use")
            except Exception as e:
                logger.warning(f"Error saving cookies: {str(e)}")
            
            logger.info(f"Successfully captured Powerball screenshot and HTML")
            
            # Save to database
            try:
                from main import app
                from screenshot_manager import save_screenshot_to_database
                
                with app.app_context():
                    screenshot_id = save_screenshot_to_database(url, lottery_type, html_path, img_path)
                    logger.info(f"Saved to database with ID {screenshot_id}")
            except Exception as e:
                logger.error(f"Error saving to database: {str(e)}")
            
            return True, html_path, img_path
        
        except Exception as e:
            logger.error(f"Error capturing screenshot: {str(e)}")
            return False, None, None
        
        finally:
            browser.close()

if __name__ == "__main__":
    logger.info("Starting specialized Powerball screenshot capture")
    success, html_path, img_path = capture_powerball()
    
    if success:
        logger.info("✅ Powerball screenshot capture completed successfully!")
        logger.info(f"HTML saved to: {html_path}")
        logger.info(f"Image saved to: {img_path}")
    else:
        logger.error("❌ Failed to capture Powerball screenshot")
    
    logger.info("Process complete")