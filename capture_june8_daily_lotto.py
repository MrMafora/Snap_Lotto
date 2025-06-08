#!/usr/bin/env python3
"""
Capture June 8th Daily Lotto results from official lottery website
"""
import os
import sys
import logging
import time
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def capture_daily_lotto_screenshot():
    """Capture fresh Daily Lotto screenshot from official website"""
    
    # Setup Chrome options
    chrome_options = Options()
    chrome_options.add_argument('--headless')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('--disable-gpu')
    chrome_options.add_argument('--window-size=1920,1080')
    chrome_options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')
    
    try:
        driver = webdriver.Chrome(options=chrome_options)
        
        url = 'https://www.nationallottery.co.za/results/daily-lotto'
        logger.info(f"Accessing official Daily Lotto results: {url}")
        
        driver.get(url)
        
        # Wait for page to load completely
        wait = WebDriverWait(driver, 15)
        wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))
        
        # Additional wait for dynamic content
        time.sleep(5)
        
        # Create timestamp for filename
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f'{timestamp}_daily_lotto.png'
        
        # Ensure screenshots directory exists
        screenshots_dir = 'screenshots'
        os.makedirs(screenshots_dir, exist_ok=True)
        
        filepath = os.path.join(screenshots_dir, filename)
        
        # Capture screenshot
        driver.save_screenshot(filepath)
        logger.info(f"Fresh Daily Lotto screenshot captured: {filepath}")
        
        driver.quit()
        return filepath
        
    except Exception as e:
        logger.error(f"Screenshot capture failed: {e}")
        try:
            driver.quit()
        except:
            pass
        return None

if __name__ == "__main__":
    result = capture_daily_lotto_screenshot()
    if result:
        print(f"SUCCESS: {result}")
    else:
        print("FAILED: Could not capture screenshot")
        sys.exit(1)