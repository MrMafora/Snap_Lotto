#!/usr/bin/env python3
"""
Test lottery screenshot capture with one URL to identify timing issues
"""

import os
import sys
import logging
import time
from datetime import datetime
from playwright.sync_api import sync_playwright

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_lottery_screenshot():
    """Test lottery screenshot capture with specific URL"""
    logger.info("Testing lottery screenshot capture")
    
    try:
        # Start Playwright
        playwright = sync_playwright().start()
        logger.info("Playwright started")
        
        # Launch browser
        browser = playwright.chromium.launch(
            executable_path='/nix/store/zi4f80l169xlmivz8vja8wlphq74qqk0-chromium-125.0.6422.141/bin/chromium',
            headless=True,
            args=[
                '--no-sandbox',
                '--disable-dev-shm-usage',
                '--disable-gpu',
                '--disable-setuid-sandbox'
            ]
        )
        logger.info("Browser launched")
        
        # Create context and page
        context = browser.new_context(viewport={'width': 1920, 'height': 1080})
        page = context.new_page()
        logger.info("Page created")
        
        # Test with Daily Lotto URL (typically fastest loading)
        test_url = "https://www.nationallottery.co.za/results/daily-lotto"
        lottery_type = "Daily Lotto"
        
        logger.info(f"Navigating to {lottery_type}: {test_url}")
        
        start_time = time.time()
        page.goto(test_url, wait_until='domcontentloaded', timeout=15000)
        nav_time = time.time() - start_time
        logger.info(f"Navigation completed in {nav_time:.2f} seconds")
        
        # Wait for page to stabilize
        page.wait_for_timeout(2000)
        logger.info("Page stabilized")
        
        # Check page title
        title = page.title()
        logger.info(f"Page title: {title}")
        
        # Take screenshot
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"test_lottery_{timestamp}.png"
        
        # Ensure screenshots directory exists
        screenshot_dir = os.path.join(os.getcwd(), 'screenshots')
        os.makedirs(screenshot_dir, exist_ok=True)
        
        filepath = os.path.join(screenshot_dir, filename)
        
        screenshot_start = time.time()
        page.screenshot(path=filepath, full_page=True)
        screenshot_time = time.time() - screenshot_start
        logger.info(f"Screenshot completed in {screenshot_time:.2f} seconds")
        
        # Cleanup
        page.close()
        context.close()
        browser.close()
        playwright.stop()
        
        # Verify file
        if os.path.exists(filepath):
            file_size = os.path.getsize(filepath)
            logger.info(f"SUCCESS: Screenshot saved with size {file_size} bytes")
            logger.info(f"Total time: {time.time() - start_time:.2f} seconds")
            return True
        else:
            logger.error("FAILED: Screenshot file not found")
            return False
            
    except Exception as e:
        logger.error(f"FAILED: {str(e)}")
        return False

if __name__ == "__main__":
    success = test_lottery_screenshot()
    sys.exit(0 if success else 1)