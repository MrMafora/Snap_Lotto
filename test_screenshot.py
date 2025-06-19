#!/usr/bin/env python3
"""
Test improved full page screenshot capture
"""

import os
import time
import logging
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_full_page_capture():
    """Test improved full page capture"""
    
    url = "https://www.nationallottery.co.za/results/lotto"
    lottery_type = "Lotto Results"
    
    # Generate filename with timestamp
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    safe_type = lottery_type.lower().replace(' ', '_')
    filename = f"{timestamp}_{safe_type}_fullpage.png"
    
    # Create screenshots directory
    screenshot_dir = os.path.join(os.getcwd(), 'screenshots')
    os.makedirs(screenshot_dir, exist_ok=True)
    filepath = os.path.join(screenshot_dir, filename)
    
    logger.info(f"Testing full page capture for {lottery_type}")
    logger.info(f"URL: {url}")
    
    # Configure Chrome options for full page capture
    chrome_options = Options()
    chrome_options.add_argument('--headless')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('--disable-gpu')
    chrome_options.add_argument('--window-size=1920,1080')
    chrome_options.add_argument('--start-maximized')
    chrome_options.add_argument('--disable-web-security')
    chrome_options.add_argument('--disable-features=VizDisplayCompositor')
    chrome_options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
    
    # Create driver
    driver = webdriver.Chrome(options=chrome_options)
    
    try:
        # Set window size for full page capture
        driver.set_window_size(1920, 1080)
        
        # Navigate to URL
        logger.info("Loading page...")
        driver.get(url)
        
        # Wait for page to load
        WebDriverWait(driver, 15).until(
            EC.presence_of_element_located((By.TAG_NAME, 'body'))
        )
        
        # Additional wait for dynamic content and page rendering
        logger.info("Waiting for content to load...")
        time.sleep(5)
        
        # Scroll to ensure all content is loaded
        logger.info("Scrolling to load all content...")
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(2)
        driver.execute_script("window.scrollTo(0, 0);")
        time.sleep(1)
        
        # Get accurate page dimensions
        page_width = driver.execute_script("return document.body.scrollWidth")
        page_height = driver.execute_script("return Math.max(document.body.scrollHeight, document.body.offsetHeight, document.documentElement.clientHeight, document.documentElement.scrollHeight, document.documentElement.offsetHeight)")
        
        logger.info(f"Page dimensions: {page_width}x{page_height}")
        
        # Set window size to capture full page
        driver.set_window_size(max(page_width, 1920), page_height)
        
        # Wait for resize and final render
        logger.info("Resizing for full page capture...")
        time.sleep(3)
        
        # Take full page PNG screenshot
        logger.info("Taking screenshot...")
        success = driver.save_screenshot(filepath)
        
        if not success:
            raise Exception("Failed to save screenshot")
        
        # Verify file was created and get size
        if os.path.exists(filepath):
            file_size = os.path.getsize(filepath)
            logger.info(f"✓ SUCCESS: {filename} created ({file_size} bytes)")
            return {
                'status': 'success',
                'filename': filename,
                'filepath': filepath,
                'file_size': file_size,
                'page_dimensions': f"{page_width}x{page_height}"
            }
        else:
            logger.error("Screenshot file was not created")
            return {'status': 'failed', 'error': 'File not created'}
            
    except Exception as e:
        logger.error(f"Error capturing screenshot: {str(e)}")
        return {'status': 'failed', 'error': str(e)}
        
    finally:
        driver.quit()

if __name__ == "__main__":
    result = test_full_page_capture()
    
    if result['status'] == 'success':
        print(f"\n✓ Full page screenshot captured successfully!")
        print(f"File: {result['filename']}")
        print(f"Size: {result['file_size']} bytes")
        print(f"Page dimensions: {result['page_dimensions']}")
    else:
        print(f"\n✗ Screenshot capture failed: {result['error']}")