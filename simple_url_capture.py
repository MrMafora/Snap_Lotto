#!/usr/bin/env python3
"""
Simple URL PNG Screenshot Capture
Captures PNG screenshots directly from SA National Lottery URLs using Selenium
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

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# SA National Lottery URLs
LOTTERY_URLS = [
    {'url': 'https://www.nationallottery.co.za/results/lotto', 'lottery_type': 'Lotto'},
    {'url': 'https://www.nationallottery.co.za/results/lotto-plus-1-results', 'lottery_type': 'Lotto Plus 1'},
    {'url': 'https://www.nationallottery.co.za/results/lotto-plus-2-results', 'lottery_type': 'Lotto Plus 2'},
    {'url': 'https://www.nationallottery.co.za/results/powerball', 'lottery_type': 'Powerball'},
    {'url': 'https://www.nationallottery.co.za/results/powerball-plus', 'lottery_type': 'Powerball Plus'},
    {'url': 'https://www.nationallottery.co.za/results/daily-lotto', 'lottery_type': 'Daily Lotto'}
]

def capture_url_screenshot(url, lottery_type):
    """Capture PNG screenshot from lottery URL using Selenium"""
    try:
        logger.info(f"Capturing PNG screenshot for {lottery_type} from {url}")
        
        # Generate filename
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        safe_lottery_type = lottery_type.lower().replace(' ', '_').replace('+', '_plus_')
        filename = f"{timestamp}_{safe_lottery_type}_url.png"
        
        # Ensure screenshots directory exists
        screenshot_dir = os.path.join(os.getcwd(), 'screenshots')
        os.makedirs(screenshot_dir, exist_ok=True)
        filepath = os.path.join(screenshot_dir, filename)
        
        # Configure Chrome options
        chrome_options = Options()
        chrome_options.add_argument('--headless')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--window-size=1920,1080')
        chrome_options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
        
        # Create driver
        driver = webdriver.Chrome(options=chrome_options)
        
        try:
            # Navigate to URL
            driver.get(url)
            
            # Wait for page to load
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.TAG_NAME, 'body'))
            )
            
            # Additional wait for dynamic content
            time.sleep(3)
            
            # Take screenshot
            driver.save_screenshot(filepath)
            
        finally:
            driver.quit()
        
        # Check if file was created
        if os.path.exists(filepath):
            file_size = os.path.getsize(filepath)
            logger.info(f"PNG screenshot captured: {filename} ({file_size} bytes)")
            return {
                'lottery_type': lottery_type,
                'url': url,
                'filepath': filepath,
                'filename': filename,
                'status': 'success'
            }
        else:
            logger.error(f"Failed to create PNG screenshot for {lottery_type}")
            return {
                'lottery_type': lottery_type,
                'url': url,
                'filepath': None,
                'filename': None,
                'status': 'failed'
            }
            
    except Exception as e:
        logger.error(f"Error capturing PNG screenshot for {lottery_type}: {str(e)}")
        return {
            'lottery_type': lottery_type,
            'url': url,
            'filepath': None,
            'filename': None,
            'status': 'error',
            'error': str(e)
        }

def run_url_screenshot_capture():
    """Run PNG screenshot capture for all lottery URLs"""
    logger.info("=== URL PNG SCREENSHOT CAPTURE STARTED ===")
    
    results = []
    successful_captures = 0
    
    for i, url_config in enumerate(LOTTERY_URLS):
        # Add delay between captures
        if i > 0:
            delay = 3 + i  # Progressive delay
            logger.info(f"Waiting {delay} seconds before next capture...")
            time.sleep(delay)
        
        # Capture PNG screenshot from URL
        result = capture_url_screenshot(url_config['url'], url_config['lottery_type'])
        results.append(result)
        
        if result and result['status'] == 'success':
            successful_captures += 1
    
    logger.info("=== URL PNG SCREENSHOT CAPTURE COMPLETED ===")
    logger.info(f"Successfully captured {successful_captures}/{len(LOTTERY_URLS)} PNG screenshots")
    
    return results

if __name__ == "__main__":
    results = run_url_screenshot_capture()
    print(f"Captured {len([r for r in results if r and r['status'] == 'success'])} PNG screenshots")