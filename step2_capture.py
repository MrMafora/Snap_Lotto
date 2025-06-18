#!/usr/bin/env python3
"""
Step 2: Screenshot Capture Module for Daily Automation
Captures actual screenshot images from official South African lottery websites using selenium
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

def setup_chrome_driver():
    """Set up Chrome driver with headless options"""
    try:
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--window-size=1200,800")
        chrome_options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
        
        driver = webdriver.Chrome(options=chrome_options)
        return driver
    except Exception as e:
        logger.error(f"Failed to setup Chrome driver: {str(e)}")
        return None

def capture_lottery_screenshot(url, lottery_type):
    """Capture actual screenshot image from lottery website using Selenium"""
    driver = None
    try:
        logger.info(f"Capturing screenshot of {lottery_type} from {url}")
        
        # Generate filename for screenshot
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        safe_lottery_type = lottery_type.lower().replace(' ', '_').replace('+', '_plus_')
        filename = f"{timestamp}_{safe_lottery_type}_screenshot.png"
        
        # Ensure screenshots directory exists
        screenshot_dir = os.path.join(os.getcwd(), 'screenshots')
        os.makedirs(screenshot_dir, exist_ok=True)
        filepath = os.path.join(screenshot_dir, filename)
        
        # Setup Chrome driver
        driver = setup_chrome_driver()
        if not driver:
            return None
        
        # Navigate to lottery page
        driver.get(url)
        
        # Wait for page to load
        time.sleep(5)
        
        # Wait for lottery results to be visible
        try:
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
        except:
            logger.warning(f"Timeout waiting for page elements on {lottery_type}")
        
        # Take screenshot
        driver.save_screenshot(filepath)
        
        logger.info(f"Screenshot captured and saved: {filename}")
        
        return filepath
        
    except Exception as e:
        logger.error(f"Failed to capture screenshot for {lottery_type}: {str(e)}")
        return None
    finally:
        if driver:
            driver.quit()

def capture_all_lottery_screenshots():
    """Capture screenshots from all lottery result URLs"""
    try:
        logger.info("=== STEP 2: SCREENSHOT CAPTURE STARTED ===")
        
        results = []
        
        # Capture screenshots from all result URLs
        for lottery_config in Config.RESULTS_URLS:
            url = lottery_config['url']
            lottery_type = lottery_config['lottery_type']
            
            # Capture screenshot
            filepath = capture_lottery_screenshot(url, lottery_type)
            
            if filepath:
                results.append({
                    'lottery_type': lottery_type,
                    'url': url,
                    'filepath': filepath,
                    'status': 'success'
                })
            else:
                results.append({
                    'lottery_type': lottery_type,
                    'url': url,
                    'filepath': None,
                    'status': 'failed'
                })
            
            # Small delay between captures
            time.sleep(2)
        
        # Log summary
        successful_captures = len([r for r in results if r['status'] == 'success'])
        total_captures = len(results)
        
        logger.info(f"=== STEP 2: SCREENSHOT CAPTURE COMPLETED ===")
        logger.info(f"Successfully captured {successful_captures}/{total_captures} screenshots")
        
        return results
        
    except Exception as e:
        logger.error(f"Failed to capture lottery screenshots: {str(e)}")
        return []

def run_capture():
    """Synchronous wrapper to run the capture function"""
    try:
        return capture_all_lottery_screenshots()
    except Exception as e:
        logger.error(f"Error running screenshot capture: {str(e)}")
        return []

if __name__ == "__main__":
    # Run screenshot capture when executed directly
    results = run_capture()
    
    # Print results summary
    print("\n=== SCREENSHOT CAPTURE RESULTS ===")
    for result in results:
        status_symbol = "✓" if result['status'] == 'success' else "✗"
        print(f"{status_symbol} {result['lottery_type']}: {result['status']}")
        if result['filepath']:
            print(f"  File: {os.path.basename(result['filepath'])}")
    
    successful = len([r for r in results if r['status'] == 'success'])
    total = len(results)
    print(f"\nTotal: {successful}/{total} screenshots captured successfully")