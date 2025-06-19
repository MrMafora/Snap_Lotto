#!/usr/bin/env python3
"""
Visual Screenshot Capture System for SA National Lottery
Enhanced full-page capture with improved connectivity handling
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
import base64

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def capture_full_page_screenshot_robust(url, lottery_type, retries=2):
    """
    Capture full-page screenshot with enhanced connectivity handling
    """
    
    # Generate filename
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    safe_type = lottery_type.lower().replace(' ', '_').replace('+', '_plus')
    filename = f"{timestamp}_{safe_type}_fullpage.png"
    
    # Create screenshots directory
    screenshot_dir = os.path.join(os.getcwd(), 'screenshots')
    os.makedirs(screenshot_dir, exist_ok=True)
    filepath = os.path.join(screenshot_dir, filename)
    
    logger.info(f"Capturing full-page screenshot for {lottery_type}")
    
    for attempt in range(retries):
        driver = None
        try:
            logger.info(f"Attempt {attempt + 1}/{retries} for {lottery_type}")
            
            # Configure Chrome with enhanced options
            chrome_options = Options()
            chrome_options.add_argument('--headless')
            chrome_options.add_argument('--no-sandbox')
            chrome_options.add_argument('--disable-dev-shm-usage')
            chrome_options.add_argument('--disable-gpu')
            chrome_options.add_argument('--disable-extensions')
            chrome_options.add_argument('--window-size=1920,1080')
            chrome_options.add_argument('--start-maximized')
            chrome_options.add_argument('--disable-web-security')
            chrome_options.add_argument('--disable-features=VizDisplayCompositor')
            chrome_options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
            
            # Additional options for better connectivity
            chrome_options.add_argument('--ignore-certificate-errors')
            chrome_options.add_argument('--ignore-ssl-errors')
            chrome_options.add_argument('--allow-running-insecure-content')
            
            # Create driver with timeouts
            driver = webdriver.Chrome(options=chrome_options)
            driver.set_page_load_timeout(60)  # Increased timeout
            driver.implicitly_wait(15)
            
            # Set initial window size
            driver.set_window_size(1920, 1080)
            
            # Navigate to URL
            logger.info(f"Loading: {url}")
            driver.get(url)
            
            # Wait for page to load with multiple checks
            try:
                WebDriverWait(driver, 30).until(
                    EC.presence_of_element_located((By.TAG_NAME, 'body'))
                )
                logger.info("Page body loaded successfully")
            except TimeoutException:
                logger.warning("Body timeout - proceeding with available content")
            
            # Extended wait for dynamic content
            time.sleep(8)
            
            # Try multiple full-page capture methods
            screenshot_captured = False
            
            # Method 1: Chrome DevTools Protocol (best for full page)
            try:
                logger.info("Attempting CDP full-page capture...")
                result = driver.execute_cdp_cmd('Page.captureScreenshot', {
                    'format': 'png',
                    'captureBeyondViewport': True
                })
                
                screenshot_data = base64.b64decode(result['data'])
                with open(filepath, 'wb') as f:
                    f.write(screenshot_data)
                
                screenshot_captured = True
                logger.info("✓ CDP full-page capture successful")
                
            except Exception as e:
                logger.warning(f"CDP method failed: {e}")
                
                # Method 2: Scroll and resize approach
                try:
                    logger.info("Attempting scroll-resize capture...")
                    
                    # Scroll to load all content
                    driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                    time.sleep(3)
                    driver.execute_script("window.scrollTo(0, 0);")
                    time.sleep(2)
                    
                    # Get page dimensions
                    page_width = driver.execute_script("return Math.max(document.body.scrollWidth, document.documentElement.scrollWidth)")
                    page_height = driver.execute_script("return Math.max(document.body.scrollHeight, document.body.offsetHeight, document.documentElement.clientHeight, document.documentElement.scrollHeight, document.documentElement.offsetHeight)")
                    
                    logger.info(f"Page dimensions: {page_width}x{page_height}")
                    
                    # Resize to capture full page
                    driver.set_window_size(max(page_width, 1920), page_height)
                    time.sleep(4)
                    
                    # Take screenshot
                    driver.save_screenshot(filepath)
                    screenshot_captured = True
                    logger.info("✓ Scroll-resize capture successful")
                    
                except Exception as e2:
                    logger.warning(f"Scroll-resize method failed: {e2}")
                    
                    # Method 3: Standard viewport screenshot as fallback
                    try:
                        logger.info("Attempting standard viewport capture...")
                        driver.set_window_size(1920, 1080)
                        time.sleep(2)
                        driver.save_screenshot(filepath)
                        screenshot_captured = True
                        logger.info("✓ Standard viewport capture successful")
                        
                    except Exception as e3:
                        logger.error(f"All capture methods failed: {e3}")
            
            # Verify screenshot was created
            if screenshot_captured and os.path.exists(filepath):
                file_size = os.path.getsize(filepath)
                if file_size > 8000:  # Reasonable minimum size
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
                    logger.warning(f"Screenshot too small: {file_size} bytes")
                    if os.path.exists(filepath):
                        os.remove(filepath)
            
        except TimeoutException as e:
            logger.warning(f"Timeout on attempt {attempt + 1}: {str(e)}")
            
        except WebDriverException as e:
            logger.warning(f"WebDriver error on attempt {attempt + 1}: {str(e)}")
            
        except Exception as e:
            logger.warning(f"General error on attempt {attempt + 1}: {str(e)}")
            
        finally:
            if driver:
                try:
                    driver.quit()
                except:
                    pass
        
        # Wait before retry
        if attempt < retries - 1:
            wait_time = (attempt + 1) * 10
            logger.info(f"Waiting {wait_time} seconds before retry...")
            time.sleep(wait_time)
    
    # All attempts failed
    logger.error(f"Failed to capture {lottery_type} after {retries} attempts")
    return {
        'status': 'failed',
        'lottery_type': lottery_type,
        'url': url,
        'error': f'Failed after {retries} attempts - connectivity issues',
        'attempts': retries
    }

def capture_lottery_results_screenshots():
    """Capture screenshots from SA National Lottery results pages only"""
    
    # Results pages only (excluding history pages)
    results_urls = [
        {'url': 'https://www.nationallottery.co.za/results/lotto', 'lottery_type': 'Lotto'},
        {'url': 'https://www.nationallottery.co.za/results/lotto-plus-1-results', 'lottery_type': 'Lotto Plus 1'},
        {'url': 'https://www.nationallottery.co.za/results/lotto-plus-2-results', 'lottery_type': 'Lotto Plus 2'},
        {'url': 'https://www.nationallottery.co.za/results/powerball', 'lottery_type': 'Powerball'},
        {'url': 'https://www.nationallottery.co.za/results/powerball-plus', 'lottery_type': 'Powerball Plus'},
        {'url': 'https://www.nationallottery.co.za/results/daily-lotto', 'lottery_type': 'Daily Lotto'}
    ]
    
    logger.info(f"Starting full-page capture for {len(results_urls)} results pages")
    
    results = []
    successful = 0
    
    for i, url_config in enumerate(results_urls):
        logger.info(f"Processing {i+1}/{len(results_urls)}: {url_config['lottery_type']}")
        
        result = capture_full_page_screenshot_robust(
            url_config['url'],
            url_config['lottery_type']
        )
        results.append(result)
        
        if result['status'] == 'success':
            successful += 1
        
        # Respectful pause between captures
        if i < len(results_urls) - 1:
            logger.info("Pausing 8 seconds between captures...")
            time.sleep(8)
    
    logger.info(f"Capture completed: {successful}/{len(results_urls)} successful")
    return results

if __name__ == "__main__":
    results = capture_lottery_results_screenshots()
    
    print(f"\n=== FULL-PAGE SCREENSHOT RESULTS ===")
    successful = 0
    for result in results:
        if result['status'] == 'success':
            print(f"✓ {result['lottery_type']}: {result['filename']} ({result['file_size']} bytes)")
            successful += 1
        else:
            print(f"✗ {result['lottery_type']}: {result['error']}")
    
    print(f"\nFinal Summary: {successful}/{len(results)} full-page captures successful")