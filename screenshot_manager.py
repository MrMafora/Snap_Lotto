"""
Fixed Screenshot Management Module
Simplified version that resolves the threading lock issues
"""

import os
import time
import threading
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
import logging

logger = logging.getLogger(__name__)

# Simple lock for sequential processing
_screenshot_lock = threading.Lock()

def capture_screenshot_from_url(url, output_path):
    """Simplified screenshot capture with proper lock handling"""
    logger.info(f"Starting screenshot capture for: {url}")
    driver = None
    
    try:
        # Simple Chrome setup
        options = Options()
        options.add_argument('--headless')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--window-size=1920,1080')
        options.add_argument('--disable-gpu')
        
        # Use system Chrome driver
        service = Service('/nix/store/3qnxr5x6gw3k9a9i7d0akz0m6bksbwff-chromedriver-125.0.6422.141/bin/chromedriver')
        driver = webdriver.Chrome(service=service, options=options)
        
        # Set timeout and navigate
        driver.set_page_load_timeout(20)
        driver.get(url)
        time.sleep(3)  # Wait for page to load
        
        # Create output directory
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        # Take screenshot
        driver.save_screenshot(output_path)
        
        # Verify screenshot was created
        if os.path.exists(output_path) and os.path.getsize(output_path) > 5000:
            logger.info(f"Screenshot captured successfully: {output_path}")
            return True
        else:
            logger.warning(f"Screenshot file too small or missing: {output_path}")
            return False
            
    except Exception as e:
        logger.error(f"Screenshot capture failed for {url}: {str(e)}")
        return False
    finally:
        if driver:
            try:
                driver.quit()
            except:
                pass

def retake_selected_screenshots(app, selected_urls, use_threading=False):
    """Capture screenshots for specific URLs with proper sequential processing"""
    if not selected_urls:
        logger.warning("No URLs provided for screenshot capture")
        return 0
    
    # Use lock to ensure one-at-a-time processing
    with _screenshot_lock:
        logger.info(f"Starting sequential screenshot capture for {len(selected_urls)} URLs")
        success_count = 0
        
        for url in selected_urls:
            try:
                logger.info(f"Processing URL: {url}")
                
                # Generate filename from URL
                from urllib.parse import urlparse
                import re
                parsed = urlparse(url)
                filename = re.sub(r'[^\w\-_.]', '_', parsed.path.strip('/'))
                if not filename:
                    filename = parsed.netloc.replace('.', '_')
                filename = f"{filename}_{int(time.time())}.png"
                
                output_path = os.path.join(os.getcwd(), 'screenshots', filename)
                
                if capture_screenshot_from_url(url, output_path):
                    success_count += 1
                    logger.info(f"✓ Screenshot captured: {filename}")
                else:
                    logger.warning(f"✗ Failed to capture: {url}")
                
                # Delay between captures
                time.sleep(2)
                
            except Exception as e:
                logger.error(f"Error processing {url}: {str(e)}")
        
        logger.info(f"Screenshot capture completed. {success_count}/{len(selected_urls)} successful")
        return success_count