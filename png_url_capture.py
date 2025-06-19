#!/usr/bin/env python3
"""
PNG Screenshot Capture from Database URLs
Captures PNG screenshots from URLs configured in ScheduleConfig database
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

def capture_png_screenshot(url, lottery_type):
    """Capture PNG screenshot from lottery URL using Selenium"""
    try:
        logger.info(f"Capturing PNG screenshot for {lottery_type} from {url}")
        
        # Generate PNG filename
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        safe_lottery_type = lottery_type.lower().replace(' ', '_').replace('+', '_plus_')
        filename = f"{timestamp}_{safe_lottery_type}.png"
        
        # Ensure screenshots directory exists
        screenshot_dir = os.path.join(os.getcwd(), 'screenshots')
        os.makedirs(screenshot_dir, exist_ok=True)
        filepath = os.path.join(screenshot_dir, filename)
        
        # Configure Chrome options for headless mode
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
            WebDriverWait(driver, 15).until(
                EC.presence_of_element_located((By.TAG_NAME, 'body'))
            )
            
            # Additional wait for dynamic content to load
            time.sleep(5)
            
            # Take PNG screenshot
            driver.save_screenshot(filepath)
            
        finally:
            driver.quit()
        
        # Verify PNG file was created
        if os.path.exists(filepath):
            file_size = os.path.getsize(filepath)
            logger.info(f"PNG screenshot captured: {filename} ({file_size} bytes)")
            return {
                'lottery_type': lottery_type,
                'url': url,
                'filepath': filepath,
                'filename': filename,
                'file_size': file_size,
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

def get_active_urls_from_database():
    """Get active URLs from ScheduleConfig database"""
    try:
        from models import ScheduleConfig
        from main import app
        
        with app.app_context():
            # Get all active URL configurations
            configs = ScheduleConfig.query.filter_by(active=True).all()
            
            url_list = []
            for config in configs:
                url_list.append({
                    'url': config.url,
                    'lottery_type': config.lottery_type
                })
            
            logger.info(f"Retrieved {len(url_list)} active URLs from database")
            return url_list
            
    except Exception as e:
        logger.error(f"Error retrieving URLs from database: {str(e)}")
        return []

def run_png_capture_from_database():
    """Run PNG screenshot capture for all active URLs from database"""
    logger.info("=== PNG SCREENSHOT CAPTURE FROM DATABASE STARTED ===")
    
    # Get URLs from database
    url_configs = get_active_urls_from_database()
    
    if not url_configs:
        logger.warning("No active URLs found in database")
        return []
    
    results = []
    successful_captures = 0
    
    for i, url_config in enumerate(url_configs):
        # Add delay between captures
        if i > 0:
            delay = 3 + (i % 3)  # Variable delay
            logger.info(f"Waiting {delay} seconds before next capture...")
            time.sleep(delay)
        
        # Capture PNG screenshot from URL
        result = capture_png_screenshot(url_config['url'], url_config['lottery_type'])
        results.append(result)
        
        if result and result['status'] == 'success':
            successful_captures += 1
    
    logger.info("=== PNG SCREENSHOT CAPTURE FROM DATABASE COMPLETED ===")
    logger.info(f"Successfully captured {successful_captures}/{len(url_configs)} PNG screenshots")
    
    # Display summary
    print(f"\nPNG SCREENSHOT CAPTURE SUMMARY:")
    print(f"Total URLs processed: {len(url_configs)}")
    print(f"Successful captures: {successful_captures}")
    print(f"Failed captures: {len(url_configs) - successful_captures}")
    
    for result in results:
        if result['status'] == 'success':
            print(f"✓ {result['lottery_type']}: {result['filename']} ({result['file_size']} bytes)")
        else:
            print(f"✗ {result['lottery_type']}: {result['status']}")
    
    return results

if __name__ == "__main__":
    results = run_png_capture_from_database()
    successful = len([r for r in results if r and r['status'] == 'success'])
    print(f"\nCaptured {successful} PNG screenshots from database URLs")