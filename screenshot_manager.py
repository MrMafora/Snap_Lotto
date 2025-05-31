"""
Screenshot Manager for Lottery Data Automation
Handles capturing screenshots from lottery websites
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

logger = logging.getLogger(__name__)

class ScreenshotManager:
    """Manages screenshot capture from lottery websites"""
    
    def __init__(self):
        self.screenshot_dir = Config.SCREENSHOT_DIR
        os.makedirs(self.screenshot_dir, exist_ok=True)
        
    def setup_driver(self):
        """Setup Chrome driver with optimized options"""
        chrome_options = Options()
        chrome_options.add_argument('--headless')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--window-size=1920,1080')
        chrome_options.add_argument('--disable-extensions')
        chrome_options.add_argument('--disable-images')
        
        driver = webdriver.Chrome(options=chrome_options)
        driver.implicitly_wait(10)
        return driver
        
    def capture_screenshot(self, url, lottery_type, retries=3):
        """Capture screenshot from lottery website"""
        driver = None
        try:
            driver = self.setup_driver()
            logger.info(f"Capturing screenshot for {lottery_type} from {url}")
            
            driver.get(url)
            time.sleep(3)  # Wait for page to load
            
            # Wait for results table to be present
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.CLASS_NAME, "results-table"))
            )
            
            # Generate filename
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{timestamp}_{lottery_type.lower().replace(' ', '_')}_results.png"
            filepath = os.path.join(self.screenshot_dir, filename)
            
            # Take screenshot
            driver.save_screenshot(filepath)
            logger.info(f"Screenshot saved: {filepath}")
            
            return {
                'success': True,
                'filepath': filepath,
                'filename': filename,
                'lottery_type': lottery_type,
                'url': url
            }
            
        except Exception as e:
            logger.error(f"Error capturing screenshot for {lottery_type}: {e}")
            if retries > 0:
                logger.info(f"Retrying... {retries} attempts remaining")
                time.sleep(2)
                return self.capture_screenshot(url, lottery_type, retries - 1)
            return {
                'success': False,
                'error': str(e),
                'lottery_type': lottery_type,
                'url': url
            }
        finally:
            if driver:
                driver.quit()
                
    def capture_all_screenshots(self, url_configs=None):
        """Capture screenshots for all lottery types"""
        if url_configs is None:
            url_configs = Config.RESULTS_URLS
            
        results = []
        for config in url_configs:
            result = self.capture_screenshot(config['url'], config['lottery_type'])
            results.append(result)
            time.sleep(2)  # Brief pause between captures
            
        return results
        
    def cleanup_old_screenshots(self, days=7):
        """Remove old screenshot files"""
        cutoff_time = time.time() - (days * 24 * 60 * 60)
        removed_count = 0
        
        for filename in os.listdir(self.screenshot_dir):
            filepath = os.path.join(self.screenshot_dir, filename)
            if os.path.isfile(filepath) and os.path.getmtime(filepath) < cutoff_time:
                try:
                    os.remove(filepath)
                    removed_count += 1
                    logger.info(f"Removed old screenshot: {filename}")
                except Exception as e:
                    logger.error(f"Error removing {filename}: {e}")
                    
        logger.info(f"Cleaned up {removed_count} old screenshots")
        return removed_count

def get_latest_screenshots():
    """Get list of latest screenshot files"""
    screenshot_dir = Config.SCREENSHOT_DIR
    if not os.path.exists(screenshot_dir):
        return []
        
    files = []
    for filename in os.listdir(screenshot_dir):
        if filename.endswith('.png'):
            filepath = os.path.join(screenshot_dir, filename)
            files.append({
                'filename': filename,
                'filepath': filepath,
                'mtime': os.path.getmtime(filepath)
            })
            
    # Sort by modification time, newest first
    files.sort(key=lambda x: x['mtime'], reverse=True)
    return files

def retake_selected_screenshots(app, urls_to_capture, use_threading=False):
    """Retake screenshots for selected lottery groups"""
    manager = ScreenshotManager()
    
    logger.info(f"Capturing screenshots for {len(urls_to_capture)} lottery sites")
    results = manager.capture_all_screenshots(urls_to_capture)
    
    success_count = sum(1 for r in results if r.get('success', False))
    logger.info(f"Screenshot capture completed: {success_count}/{len(results)} successful")
    
    return success_count