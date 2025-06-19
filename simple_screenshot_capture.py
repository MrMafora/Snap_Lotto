#!/usr/bin/env python3
"""
Simple Screenshot Capture System
Handles connectivity issues and timeouts with robust retry logic
"""

import os
import time
import logging
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, WebDriverException
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def capture_screenshot_with_retry(url, lottery_type, max_retries=3):
    """
    Capture screenshot with robust retry logic and timeout handling
    """
    
    # Generate filename
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    safe_type = lottery_type.lower().replace(' ', '_').replace('+', '_plus')
    filename = f"{timestamp}_{safe_type}_capture.png"
    
    # Create screenshots directory
    screenshot_dir = os.path.join(os.getcwd(), 'screenshots')
    os.makedirs(screenshot_dir, exist_ok=True)
    filepath = os.path.join(screenshot_dir, filename)
    
    logger.info(f"Attempting to capture {lottery_type} from {url}")
    
    for attempt in range(max_retries):
        driver = None
        try:
            logger.info(f"Attempt {attempt + 1}/{max_retries}")
            
            # Configure Chrome with minimal options for reliability
            chrome_options = Options()
            chrome_options.add_argument('--headless')
            chrome_options.add_argument('--no-sandbox')
            chrome_options.add_argument('--disable-dev-shm-usage')
            chrome_options.add_argument('--disable-gpu')
            chrome_options.add_argument('--disable-extensions')
            chrome_options.add_argument('--disable-plugins')
            chrome_options.add_argument('--disable-images')  # Faster loading
            chrome_options.add_argument('--window-size=1366,768')  # Standard size
            chrome_options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')
            
            # Create driver with shorter timeouts
            driver = webdriver.Chrome(options=chrome_options)
            driver.set_page_load_timeout(45)  # 45 second timeout
            driver.implicitly_wait(10)
            
            # Navigate to URL
            logger.info(f"Loading: {url}")
            driver.get(url)
            
            # Wait for basic page structure
            try:
                WebDriverWait(driver, 20).until(
                    EC.presence_of_element_located((By.TAG_NAME, 'body'))
                )
                logger.info("Page body loaded")
            except TimeoutException:
                logger.warning("Page body timeout, proceeding with screenshot")
            
            # Brief wait for content
            time.sleep(5)
            
            # Take basic screenshot (viewport size)
            logger.info("Taking screenshot...")
            driver.save_screenshot(filepath)
            
            # Verify file creation
            if os.path.exists(filepath):
                file_size = os.path.getsize(filepath)
                if file_size > 5000:  # Minimum reasonable file size
                    logger.info(f"✓ SUCCESS: {filename} ({file_size} bytes)")
                    return {
                        'status': 'success',
                        'filename': filename,
                        'filepath': filepath,
                        'file_size': file_size,
                        'lottery_type': lottery_type,
                        'attempt': attempt + 1
                    }
                else:
                    raise Exception(f"Screenshot too small: {file_size} bytes")
            else:
                raise Exception("Screenshot file not created")
                
        except TimeoutException as e:
            logger.warning(f"Timeout on attempt {attempt + 1}: {str(e)}")
            if attempt < max_retries - 1:
                logger.info(f"Retrying in 10 seconds...")
                time.sleep(10)
            
        except WebDriverException as e:
            logger.warning(f"WebDriver error on attempt {attempt + 1}: {str(e)}")
            if attempt < max_retries - 1:
                time.sleep(5)
                
        except Exception as e:
            logger.warning(f"General error on attempt {attempt + 1}: {str(e)}")
            if attempt < max_retries - 1:
                time.sleep(5)
                
        finally:
            if driver:
                try:
                    driver.quit()
                except:
                    pass
    
    # All attempts failed
    logger.error(f"Failed to capture {lottery_type} after {max_retries} attempts")
    return {
        'status': 'failed',
        'lottery_type': lottery_type,
        'url': url,
        'error': f'Failed after {max_retries} attempts',
        'attempts': max_retries
    }

def capture_all_lottery_screenshots():
    """Capture screenshots from all lottery results pages"""
    
    results_urls = [
        {'url': 'https://www.nationallottery.co.za/results/lotto', 'lottery_type': 'Lotto'},
        {'url': 'https://www.nationallottery.co.za/results/lotto-plus-1-results', 'lottery_type': 'Lotto Plus 1'},
        {'url': 'https://www.nationallottery.co.za/results/lotto-plus-2-results', 'lottery_type': 'Lotto Plus 2'},
        {'url': 'https://www.nationallottery.co.za/results/powerball', 'lottery_type': 'Powerball'},
        {'url': 'https://www.nationallottery.co.za/results/powerball-plus', 'lottery_type': 'Powerball Plus'},
        {'url': 'https://www.nationallottery.co.za/results/daily-lotto', 'lottery_type': 'Daily Lotto'}
    ]
    
    logger.info(f"Starting screenshot capture for {len(results_urls)} lottery pages")
    
    results = []
    successful = 0
    
    for url_config in results_urls:
        result = capture_screenshot_with_retry(
            url_config['url'],
            url_config['lottery_type']
        )
        results.append(result)
        
        if result['status'] == 'success':
            successful += 1
        
        # Pause between captures to be respectful
        if len(results) < len(results_urls):
            logger.info("Pausing 5 seconds between captures...")
            time.sleep(5)
    
    logger.info(f"Completed: {successful}/{len(results_urls)} successful captures")
    return results

if __name__ == "__main__":
    results = capture_all_lottery_screenshots()
    
    print(f"\n=== SCREENSHOT CAPTURE RESULTS ===")
    successful = 0
    for result in results:
        if result['status'] == 'success':
            print(f"✓ {result['lottery_type']}: {result['filename']} ({result['file_size']} bytes)")
            successful += 1
        else:
            print(f"✗ {result['lottery_type']}: {result['error']}")
    
    print(f"\nSummary: {successful}/{len(results)} captures successful")