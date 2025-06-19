#!/usr/bin/env python3
"""
Visual Screenshot Capture Module using Selenium
Captures high-quality PNG screenshots from South African lottery websites
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

class LotteryScreenshotCapture:
    def __init__(self):
        self.screenshot_dir = os.path.join(os.getcwd(), 'screenshots')
        os.makedirs(self.screenshot_dir, exist_ok=True)
    
    def create_driver(self):
        """Create Chrome driver with optimal settings for screenshots"""
        chrome_options = Options()
        chrome_options.add_argument('--headless')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--window-size=1920,1080')
        chrome_options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
        chrome_options.add_argument('--accept-lang=en-ZA,en;q=0.9')
        chrome_options.add_argument('--disable-blink-features=AutomationControlled')
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        
        driver = webdriver.Chrome(options=chrome_options)
        driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        return driver
    
    def capture_screenshot(self, url, lottery_type, retries=3):
        """Capture high-quality screenshot of lottery results page"""
        for attempt in range(retries):
            driver = None
            try:
                logger.info(f"Capturing {lottery_type} screenshot from {url} (attempt {attempt + 1})")
                
                driver = self.create_driver()
                
                # Navigate to the page
                driver.get(url)
                
                # Wait for page to load
                WebDriverWait(driver, 20).until(
                    EC.presence_of_element_located((By.TAG_NAME, "body"))
                )
                
                # Additional wait for dynamic content
                time.sleep(5)
                
                # Try to wait for lottery-specific content
                try:
                    WebDriverWait(driver, 10).until(
                        EC.any_of(
                            EC.presence_of_element_located((By.CLASS_NAME, "results")),
                            EC.presence_of_element_located((By.CLASS_NAME, "lottery-results")),
                            EC.presence_of_element_located((By.CLASS_NAME, "winning-numbers")),
                            EC.presence_of_element_located((By.XPATH, "//*[contains(text(), 'WINNING NUMBERS')]"))
                        )
                    )
                except:
                    logger.warning(f"Lottery results content not found on {url}, proceeding with general capture")
                
                # Scroll to ensure full page is loaded
                driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(2)
                driver.execute_script("window.scrollTo(0, 0);")
                time.sleep(2)
                
                # Generate filename
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                safe_lottery_type = lottery_type.lower().replace(' ', '_').replace('+', '_plus_')
                filename = f"{timestamp}_{safe_lottery_type}_screenshot.png"
                filepath = os.path.join(self.screenshot_dir, filename)
                
                # Capture full page screenshot
                S = lambda X: driver.execute_script('return document.body.parentNode.scroll'+X)
                driver.set_window_size(1920, S('Height'))
                
                # Take the screenshot
                driver.save_screenshot(filepath)
                
                # Verify screenshot was created
                if os.path.exists(filepath) and os.path.getsize(filepath) > 10000:  # At least 10KB
                    logger.info(f"Successfully captured {lottery_type} screenshot: {filename}")
                    return filepath
                else:
                    logger.error(f"Screenshot capture failed or file too small: {filename}")
                    if os.path.exists(filepath):
                        os.remove(filepath)
                    return None
                        
            except Exception as e:
                logger.error(f"Error capturing {lottery_type} screenshot (attempt {attempt + 1}): {str(e)}")
                if attempt < retries - 1:
                    time.sleep(5)  # Wait before retry
                else:
                    logger.error(f"Failed to capture {lottery_type} screenshot after {retries} attempts")
                    return None
            finally:
                if driver:
                    driver.quit()
    
    def capture_all_lottery_screenshots(self):
        """Capture screenshots from all lottery result pages"""
        results = {}
        
        # Get lottery URLs from config
        lottery_urls = {item['lottery_type']: item['url'] for item in Config.RESULTS_URLS}
        
        for lottery_type, url in lottery_urls.items():
            logger.info(f"Starting capture for {lottery_type}")
            
            # Add delay between captures to be respectful
            if results:  # Not the first capture
                time.sleep(8)  # 8 second delay between captures
            
            filepath = self.capture_screenshot(url, lottery_type)
            results[lottery_type] = {
                'success': filepath is not None,
                'filepath': filepath,
                'url': url
            }
            
            if filepath:
                logger.info(f"✓ {lottery_type} screenshot captured successfully")
            else:
                logger.error(f"✗ {lottery_type} screenshot capture failed")
        
        return results

def run_visual_capture():
    """Run the visual screenshot capture process"""
    logger.info("=== VISUAL SCREENSHOT CAPTURE STARTED ===")
    
    capture = LotteryScreenshotCapture()
    results = capture.capture_all_lottery_screenshots()
    
    success_count = sum(1 for r in results.values() if r['success'])
    total_count = len(results)
    
    logger.info(f"=== VISUAL SCREENSHOT CAPTURE COMPLETED ===")
    logger.info(f"Successfully captured: {success_count}/{total_count} screenshots")
    
    return success_count == total_count

if __name__ == "__main__":
    success = run_visual_capture()
    exit(0 if success else 1)