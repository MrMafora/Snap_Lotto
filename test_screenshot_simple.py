#!/usr/bin/env python3
"""
Simple screenshot test to diagnose Playwright issues
"""

import os
import sys
import logging
from datetime import datetime
from playwright.sync_api import sync_playwright

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_simple_screenshot():
    """Test basic screenshot functionality"""
    logger.info("Starting simple screenshot test")
    
    try:
        # Start Playwright
        playwright = sync_playwright().start()
        logger.info("Playwright started successfully")
        
        # Launch browser with system Chromium
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
        logger.info("Browser launched successfully")
        
        # Create context and page
        context = browser.new_context(viewport={'width': 1280, 'height': 720})
        page = context.new_page()
        logger.info("Page created successfully")
        
        # Test with a simple, reliable URL
        test_url = "https://httpbin.org/html"
        logger.info(f"Navigating to test URL: {test_url}")
        
        page.goto(test_url, timeout=10000)
        logger.info("Navigation completed")
        
        # Take screenshot
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"test_screenshot_{timestamp}.png"
        
        # Ensure screenshots directory exists
        screenshot_dir = os.path.join(os.getcwd(), 'screenshots')
        os.makedirs(screenshot_dir, exist_ok=True)
        
        filepath = os.path.join(screenshot_dir, filename)
        page.screenshot(path=filepath)
        logger.info(f"Screenshot saved: {filepath}")
        
        # Cleanup
        page.close()
        context.close()
        browser.close()
        playwright.stop()
        
        # Verify file exists
        if os.path.exists(filepath):
            file_size = os.path.getsize(filepath)
            logger.info(f"SUCCESS: Screenshot file created with size {file_size} bytes")
            return True
        else:
            logger.error("FAILED: Screenshot file not found")
            return False
            
    except Exception as e:
        logger.error(f"FAILED: {str(e)}")
        return False

if __name__ == "__main__":
    success = test_simple_screenshot()
    sys.exit(0 if success else 1)