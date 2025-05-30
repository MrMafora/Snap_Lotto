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

# Disabled lock to prevent conflicts with step2_capture.py
# _screenshot_lock = threading.Lock()

def capture_screenshot_from_url(url, output_path):
    """Disabled to prevent conflicts with step2_capture.py"""
    logger.warning("Screenshot manager disabled - using step2_capture.py instead")
    return False
        
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