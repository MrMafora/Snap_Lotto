#!/usr/bin/env python3
"""
Step 2: PNG Screenshot Capture Module for Daily Automation
Captures PNG screenshots from SA National Lottery URLs using Playwright
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
from selenium.common.exceptions import TimeoutException, WebDriverException

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
        
        # Generate PNG filename
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        safe_lottery_type = lottery_type.lower().replace(' ', '_').replace('+', '_plus_')
        filename = f"{timestamp}_{safe_lottery_type}.png"
        
        # Ensure screenshots directory exists
        screenshot_dir = os.path.join(os.getcwd(), 'screenshots')
        os.makedirs(screenshot_dir, exist_ok=True)
        filepath = os.path.join(screenshot_dir, filename)
        
        # Configure Chrome options for enhanced full page capture
        chrome_options = Options()
        chrome_options.add_argument('--headless')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--window-size=1920,1080')
        chrome_options.add_argument('--start-maximized')
        chrome_options.add_argument('--disable-web-security')
        chrome_options.add_argument('--disable-features=VizDisplayCompositor')
        chrome_options.add_argument('--ignore-certificate-errors')
        chrome_options.add_argument('--ignore-ssl-errors')
        chrome_options.add_argument('--allow-running-insecure-content')
        chrome_options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
        
        # Create driver with enhanced timeouts
        driver = webdriver.Chrome(options=chrome_options)
        driver.set_page_load_timeout(90)  # Extended timeout for slow connections
        driver.implicitly_wait(20)
        
        try:
            # Set initial window size
            driver.set_window_size(1920, 1080)
            
            logger.info(f"Loading URL: {url}")
            # Navigate to URL with retry logic
            max_load_attempts = 2
            page_loaded = False
            
            for load_attempt in range(max_load_attempts):
                try:
                    driver.get(url)
                    page_loaded = True
                    break
                except Exception as load_e:
                    logger.warning(f"Load attempt {load_attempt + 1} failed: {str(load_e)}")
                    if load_attempt < max_load_attempts - 1:
                        time.sleep(15)
            
            if not page_loaded:
                raise Exception("Failed to load page after multiple attempts")
            
            # Wait for page to load with extended timeout
            try:
                WebDriverWait(driver, 30).until(
                    EC.presence_of_element_located((By.TAG_NAME, 'body'))
                )
                logger.info("Page body loaded successfully")
            except TimeoutException:
                logger.warning("Body load timeout - proceeding with capture")
            
            # Extended wait for dynamic content and page rendering
            time.sleep(8)
            
            # Try to capture full page using Chrome's built-in capabilities
            try:
                # Method 1: Use Chrome DevTools Protocol for full page screenshot
                result = driver.execute_cdp_cmd('Page.captureScreenshot', {
                    'format': 'png',
                    'captureBeyondViewport': True
                })
                
                # Decode base64 image and save
                import base64
                screenshot_data = base64.b64decode(result['data'])
                with open(filepath, 'wb') as f:
                    f.write(screenshot_data)
                
                logger.info("Full page screenshot captured using CDP")
                
            except Exception as e:
                logger.warning(f"CDP method failed: {e}, trying standard approach")
                
                # Method 2: Fallback to scrolling and resizing approach
                # Scroll to ensure all content is loaded
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
                time.sleep(3)
                
                # Take standard screenshot
                success = driver.save_screenshot(filepath)
                
                if not success:
                    raise Exception("Failed to save screenshot")
            
        finally:
            driver.quit()
        
        # Check if PNG file was created
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

def get_urls_from_database():
    """Get active results page URLs from ScheduleConfig database"""
    try:
        from models import ScheduleConfig
        from main import app
        
        with app.app_context():
            configs = ScheduleConfig.query.filter_by(active=True).all()
            
            url_list = []
            for config in configs:
                # Only include results pages, not history pages
                if '/results/' in config.url:
                    url_list.append({
                        'url': config.url,
                        'lottery_type': config.lottery_type
                    })
            
            logger.info(f"Retrieved {len(url_list)} active results page URLs from database")
            return url_list
            
    except Exception as e:
        logger.error(f"Error retrieving URLs from database: {str(e)}")
        # Fallback to hardcoded results URLs if database fails
        return [
            {'url': 'https://www.nationallottery.co.za/results/lotto', 'lottery_type': 'Lotto'},
            {'url': 'https://www.nationallottery.co.za/results/lotto-plus-1-results', 'lottery_type': 'Lotto Plus 1'},
            {'url': 'https://www.nationallottery.co.za/results/lotto-plus-2-results', 'lottery_type': 'Lotto Plus 2'},
            {'url': 'https://www.nationallottery.co.za/results/powerball', 'lottery_type': 'Powerball'},
            {'url': 'https://www.nationallottery.co.za/results/powerball-plus', 'lottery_type': 'Powerball Plus'},
            {'url': 'https://www.nationallottery.co.za/results/daily-lotto', 'lottery_type': 'Daily Lotto'}
        ]

def run_screenshot_capture():
    """Run PNG screenshot capture for all active URLs from database"""
    logger.info("=== STEP 2: PNG SCREENSHOT CAPTURE STARTED ===")
    
    # Get URLs from database
    url_configs = get_urls_from_database()
    
    if not url_configs:
        logger.warning("No URLs found for screenshot capture")
        return []
    
    results = []
    successful_captures = 0
    
    for i, url_config in enumerate(url_configs):
        # Add delay between captures
        if i > 0:
            delay = 3 + (i % 3)  # Variable delay between 3-5 seconds
            logger.info(f"Waiting {delay} seconds before next capture...")
            time.sleep(delay)
        
        # Capture PNG screenshot from URL
        result = capture_url_screenshot(url_config['url'], url_config['lottery_type'])
        results.append(result)
        
        if result and result['status'] == 'success':
            successful_captures += 1
    
    logger.info("=== STEP 2: PNG SCREENSHOT CAPTURE COMPLETED ===")
    logger.info(f"Successfully captured {successful_captures}/{len(url_configs)} PNG screenshots")
    
    return results

if __name__ == "__main__":
    results = run_screenshot_capture()
    print(f"Captured {len([r for r in results if r and r['status'] == 'success'])} PNG screenshots")