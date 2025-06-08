#!/usr/bin/env python3
"""
Step 2: Screenshot Capture Module for Daily Automation
Captures fresh lottery screenshots from official South African lottery websites
"""

import os
import time
import logging
from datetime import datetime
from playwright.sync_api import sync_playwright
from config import Config

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def setup_browser():
    """Set up Playwright browser with optimized options"""
    try:
        playwright = sync_playwright().start()
        browser = playwright.chromium.launch(
            headless=True,
            args=[
                '--no-sandbox',
                '--disable-dev-shm-usage',
                '--disable-gpu'
            ]
        )
        
        context = browser.new_context(
            viewport={'width': 1920, 'height': 1080},
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        )
        
        return playwright, browser, context
    except Exception as e:
        logger.error(f"Failed to setup Playwright browser: {str(e)}")
        return None, None, None

def capture_lottery_screenshot(url, lottery_type, page):
    """Capture a screenshot from a lottery URL using Playwright"""
    try:
        logger.info(f"Capturing {lottery_type} from {url}")
        
        page.goto(url, wait_until='networkidle')
        page.wait_for_timeout(3000)  # Wait for page to stabilize
        
        # Generate filename
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        safe_lottery_type = lottery_type.lower().replace(' ', '_').replace('+', '_plus_')
        filename = f"{timestamp}_{safe_lottery_type}.png"
        
        # Ensure screenshots directory exists
        screenshot_dir = os.path.join(os.getcwd(), 'screenshots')
        os.makedirs(screenshot_dir, exist_ok=True)
        
        # Save screenshot
        filepath = os.path.join(screenshot_dir, filename)
        page.screenshot(path=filepath, full_page=True)
        
        logger.info(f"Screenshot saved: {filename}")
        return filepath
        
    except Exception as e:
        logger.error(f"Failed to capture {lottery_type}: {str(e)}")
        return None

def capture_all_lottery_screenshots():
    """Capture screenshots from all lottery URLs using Playwright"""
    logger.info("=== STEP 2: SCREENSHOT CAPTURE STARTED ===")
    
    playwright, browser, context = setup_browser()
    if not playwright or not browser or not context:
        logger.error("Failed to setup Playwright browser")
        return False
    
    captured_count = 0
    total_urls = len(Config.RESULTS_URLS)
    
    try:
        page = context.new_page()
        
        for url_config in Config.RESULTS_URLS:
            url = url_config['url']
            lottery_type = url_config['lottery_type']
            
            filepath = capture_lottery_screenshot(url, lottery_type, page)
            if filepath:
                captured_count += 1
            
            time.sleep(2)  # Respectful delay between requests
            
    except Exception as e:
        logger.error(f"Error during screenshot capture: {str(e)}")
    finally:
        if browser:
            browser.close()
        if playwright:
            playwright.stop()
    
    success = captured_count > 0
    
    if success:
        logger.info(f"=== STEP 2: CAPTURE COMPLETED - {captured_count}/{total_urls} screenshots captured ===")
    else:
        logger.error("=== STEP 2: CAPTURE FAILED - No screenshots captured ===")
        
    return success

def run_capture():
    """Run the screenshot capture process"""
    return capture_all_lottery_screenshots()

if __name__ == "__main__":
    run_capture()