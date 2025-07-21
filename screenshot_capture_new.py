"""
REBUILT Full-Page Screenshot Capture System
Complete rebuild to ensure proper header-to-footer capture
"""

import os
import time
import random
import logging
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from models import Screenshot, db
from flask_login import current_user

# Configure logging
logger = logging.getLogger(__name__)

# South African Lottery URLs - Direct from database
LOTTERY_URLS = {
    'LOTTO': 'https://www.nationallottery.co.za/results/lotto',
    'LOTTO PLUS 1': 'https://www.nationallottery.co.za/results/lotto-plus-1-results',
    'LOTTO PLUS 2': 'https://www.nationallottery.co.za/results/lotto-plus-2-results',
    'POWERBALL': 'https://www.nationallottery.co.za/results/powerball',
    'POWERBALL PLUS': 'https://www.nationallottery.co.za/results/powerball-plus',
    'DAILY LOTTO': 'https://www.nationallottery.co.za/results/daily-lotto'
}

def setup_chrome_driver_fullpage():
    """
    Setup Chrome driver specifically optimized for full-page screenshots
    """
    chrome_options = Options()
    
    # Essential headless settings
    chrome_options.add_argument('--headless')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('--disable-gpu')
    
    # CRITICAL: Start with large initial window size
    chrome_options.add_argument('--window-size=1920,2000')
    
    # Disable unnecessary features for clean capture
    chrome_options.add_argument('--disable-extensions')
    chrome_options.add_argument('--disable-plugins')
    chrome_options.add_argument('--disable-images')  # Faster loading
    
    # User agent
    chrome_options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
    
    try:
        driver = webdriver.Chrome(options=chrome_options)
        
        # CRITICAL: Set initial large viewport
        driver.set_window_size(1920, 2000)
        
        return driver
    except Exception as e:
        logger.error(f"Failed to setup Chrome driver: {e}")
        return None

def capture_full_page_screenshot(driver, filepath):
    """
    Capture complete full-page screenshot using proper method
    """
    try:
        # STEP 1: Ensure we're at absolute top
        driver.execute_script("window.scrollTo(0, 0);")
        time.sleep(1)
        
        # STEP 2: Get total document dimensions
        dimensions = driver.execute_script("""
            return {
                scrollHeight: document.documentElement.scrollHeight,
                scrollWidth: document.documentElement.scrollWidth,
                clientHeight: document.documentElement.clientHeight,
                clientWidth: document.documentElement.clientWidth,
                offsetHeight: document.documentElement.offsetHeight,
                offsetWidth: document.documentElement.offsetWidth
            };
        """)
        
        # Calculate actual page dimensions
        page_width = max(dimensions['scrollWidth'], dimensions['offsetWidth'], 1920)
        page_height = max(dimensions['scrollHeight'], dimensions['offsetHeight'], dimensions['clientHeight'])
        
        logger.info(f"Page dimensions detected: {page_width}x{page_height}")
        
        # STEP 3: Set browser viewport to EXACT page size
        driver.set_window_size(page_width, page_height)
        time.sleep(2)  # Allow resize to complete
        
        # STEP 4: Ensure still at top after resize
        driver.execute_script("window.scrollTo(0, 0);")
        driver.execute_script("document.documentElement.scrollTop = 0;")
        driver.execute_script("document.body.scrollTop = 0;")
        time.sleep(1)
        
        # STEP 5: Take screenshot
        success = driver.save_screenshot(filepath)
        
        if success and os.path.exists(filepath):
            file_size = os.path.getsize(filepath)
            logger.info(f"Screenshot saved: {filepath} ({file_size:,} bytes, {page_width}x{page_height})")
            return {
                'success': True,
                'file_size': file_size,
                'width': page_width,
                'height': page_height
            }
        else:
            logger.error("Screenshot save failed")
            return {'success': False, 'error': 'Save failed'}
            
    except Exception as e:
        logger.error(f"Screenshot capture error: {e}")
        return {'success': False, 'error': str(e)}

def capture_lottery_screenshot_new(lottery_type, url, output_dir='screenshots'):
    """
    NEW: Capture complete full-page screenshot with proper header inclusion
    """
    # Ensure output directory exists
    os.makedirs(output_dir, exist_ok=True)
    
    # Generate filename with timestamp
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = f"{timestamp}_{lottery_type.lower().replace(' ', '_')}_new.png"
    filepath = os.path.join(output_dir, filename)
    
    driver = setup_chrome_driver_fullpage()
    if not driver:
        return {
            'success': False,
            'error': 'Failed to setup browser driver',
            'lottery_type': lottery_type
        }
    
    try:
        logger.info(f"NEW METHOD: Capturing {lottery_type} from {url}")
        
        # Navigate to page
        driver.get(url)
        
        # Wait for page to load completely
        WebDriverWait(driver, 15).until(
            EC.presence_of_element_located((By.TAG_NAME, "body"))
        )
        
        # Additional wait for content
        time.sleep(5)
        
        # Capture full-page screenshot
        result = capture_full_page_screenshot(driver, filepath)
        
        if result['success']:
            # Save to database
            try:
                screenshot = Screenshot()
                screenshot.lottery_type = lottery_type
                screenshot.url = url
                screenshot.filename = filename
                screenshot.file_path = filepath
                screenshot.file_size = result['file_size']
                screenshot.capture_method = 'selenium_new_fullpage'
                screenshot.status = 'active'
                if hasattr(current_user, 'id'):
                    screenshot.created_by = current_user.id
                
                db.session.add(screenshot)
                db.session.commit()
                
                return {
                    'success': True,
                    'lottery_type': lottery_type,
                    'filename': filename,
                    'filepath': filepath,
                    'file_size': result['file_size'],
                    'dimensions': f"{result['width']}x{result['height']}"
                }
                
            except Exception as db_error:
                logger.error(f"Database error: {db_error}")
                db.session.rollback()
                return {
                    'success': False,
                    'error': f'Database error: {str(db_error)}',
                    'lottery_type': lottery_type
                }
        else:
            return {
                'success': False,
                'error': result.get('error', 'Screenshot capture failed'),
                'lottery_type': lottery_type
            }
        
    except Exception as e:
        logger.error(f"Error capturing {lottery_type}: {e}")
        return {
            'success': False,
            'error': str(e),
            'lottery_type': lottery_type
        }
        
    finally:
        if driver:
            driver.quit()

def test_new_screenshot_method():
    """
    Test the new screenshot method on one lottery type
    """
    logger.info("Testing NEW screenshot method...")
    
    # Test with LOTTO first
    result = capture_lottery_screenshot_new('LOTTO', LOTTERY_URLS['LOTTO'])
    
    if result['success']:
        logger.info(f"✅ NEW METHOD SUCCESS: {result['filename']} ({result['file_size']:,} bytes)")
        logger.info(f"   Dimensions: {result['dimensions']}")
        return True
    else:
        logger.error(f"❌ NEW METHOD FAILED: {result.get('error', 'Unknown error')}")
        return False