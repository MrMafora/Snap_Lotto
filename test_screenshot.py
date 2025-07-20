#!/usr/bin/env python3
"""
Test the screenshot capture system with simplified Chrome configuration
"""

import os
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_simple_chrome():
    """Test basic Chrome driver setup"""
    
    chrome_options = Options()
    
    # Simplified options for Replit
    chrome_options.add_argument('--headless')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('--disable-gpu')
    chrome_options.add_argument('--remote-debugging-port=9222')
    chrome_options.add_argument('--window-size=1920,1080')
    chrome_options.add_argument('--user-agent=Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
    
    try:
        logger.info("Testing Chrome driver setup...")
        driver = webdriver.Chrome(options=chrome_options)
        
        logger.info("✅ Chrome driver created successfully")
        
        # Test navigation
        logger.info("Testing navigation to SA National Lottery...")
        driver.get("https://www.nationallottery.co.za")
        logger.info("✅ Navigation successful")
        
        # Take test screenshot
        os.makedirs('screenshots', exist_ok=True)
        screenshot_path = 'screenshots/test_capture.png'
        driver.save_screenshot(screenshot_path)
        
        if os.path.exists(screenshot_path):
            size = os.path.getsize(screenshot_path)
            logger.info(f"✅ Screenshot captured successfully: {size} bytes")
        else:
            logger.error("❌ Screenshot file not created")
            
        driver.quit()
        return True
        
    except Exception as e:
        logger.error(f"❌ Chrome driver test failed: {e}")
        return False

if __name__ == "__main__":
    print("🧪 Testing Chrome Driver Setup")
    print("=" * 40)
    
    success = test_simple_chrome()
    
    if success:
        print("✅ Chrome driver test passed - screenshot system should work")
    else:
        print("❌ Chrome driver test failed - needs configuration fixes")