"""
Quick Screenshot Capture - Simple and Reliable
Fixes the hanging browser issue with a minimal approach
"""

import os
import time
import logging
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service

logger = logging.getLogger(__name__)

def quick_capture_screenshot(url, output_path, timeout=15):
    """
    Capture a screenshot quickly without complex features that cause hanging
    """
    driver = None
    try:
        # Simple Chrome options
        options = Options()
        options.add_argument("--headless")
        options.add_argument("--no-sandbox") 
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-gpu")
        options.add_argument("--window-size=1920,1080")
        
        # Create driver with timeout
        service = Service()
        driver = webdriver.Chrome(service=service, options=options)
        driver.set_page_load_timeout(timeout)
        
        # Ensure directory exists
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        logger.info(f"Loading {url}")
        driver.get(url)
        
        # Brief wait for content
        time.sleep(2)
        
        # Take screenshot
        logger.info(f"Capturing screenshot to {output_path}")
        success = driver.save_screenshot(output_path)
        
        if success and os.path.exists(output_path):
            file_size = os.path.getsize(output_path)
            logger.info(f"Screenshot captured: {file_size} bytes")
            return file_size > 1000
        else:
            logger.error("Screenshot failed")
            return False
            
    except Exception as e:
        logger.error(f"Screenshot error: {e}")
        return False
    finally:
        if driver:
            try:
                driver.quit()
            except:
                pass

def test_quick_capture():
    """Test the quick capture function"""
    test_url = "https://www.nationallottery.co.za/results/lotto"
    test_path = "screenshots/test_quick.png"
    
    print(f"Testing quick capture for {test_url}")
    result = quick_capture_screenshot(test_url, test_path)
    print(f"Result: {result}")
    
    if result and os.path.exists(test_path):
        file_size = os.path.getsize(test_path)
        print(f"Screenshot saved: {file_size} bytes")
    
    return result

if __name__ == "__main__":
    test_quick_capture()