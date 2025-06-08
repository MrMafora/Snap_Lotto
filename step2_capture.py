#!/usr/bin/env python3
"""
Step 2: Screenshot Capture Module for Daily Automation
Captures fresh lottery screenshots from official South African lottery websites
"""

import os
import time
import logging
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from config import Config

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def setup_driver():
    """Set up Chrome WebDriver with optimized options"""
    try:
        chrome_options = Options()
        chrome_options.add_argument('--headless')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--window-size=1920,1080')
        chrome_options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')
        
        driver = webdriver.Chrome(options=chrome_options)
        return driver
    except Exception as e:
        logger.error(f"Failed to setup Chrome driver: {str(e)}")
        return None

def capture_lottery_screenshot(url, lottery_type, driver):
    """Capture a screenshot from a lottery URL"""
    try:
        logger.info(f"Capturing {lottery_type} from {url}")
        
        driver.get(url)
        time.sleep(3)  # Wait for page to load
        
        # Wait for main content to load
        try:
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
        except:
            logger.warning(f"Body element not found for {lottery_type}")
        
        # Generate filename
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        safe_lottery_type = lottery_type.lower().replace(' ', '_').replace('+', '_plus_')
        filename = f"{timestamp}_{safe_lottery_type}.png"
        
        # Ensure screenshots directory exists
        screenshot_dir = os.path.join(os.getcwd(), 'screenshots')
        os.makedirs(screenshot_dir, exist_ok=True)
        
        # Save screenshot
        filepath = os.path.join(screenshot_dir, filename)
        driver.save_screenshot(filepath)
        
        logger.info(f"Screenshot saved: {filename}")
        return filepath
        
    except Exception as e:
        logger.error(f"Failed to capture {lottery_type}: {str(e)}")
        return None

def capture_all_lottery_screenshots():
    """Capture screenshots from all lottery URLs"""
    logger.info("=== STEP 2: SCREENSHOT CAPTURE STARTED ===")
    
    driver = setup_driver()
    if not driver:
        logger.error("Failed to setup web driver")
        return False
    
    captured_count = 0
    total_urls = len(Config.RESULTS_URLS)
    
    try:
        for url_config in Config.RESULTS_URLS:
            url = url_config['url']
            lottery_type = url_config['lottery_type']
            
            filepath = capture_lottery_screenshot(url, lottery_type, driver)
            if filepath:
                captured_count += 1
            
            time.sleep(2)  # Respectful delay between requests
            
    except Exception as e:
        logger.error(f"Error during screenshot capture: {str(e)}")
    finally:
        driver.quit()
    
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