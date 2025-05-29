"""
Screenshot Management Module
Handles automated screenshot capture and synchronization for lottery data
"""

import os
import requests
import time
import random
import threading
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from models import Screenshot, db
import logging

# Force Chrome driver path globally
os.environ['CHROMEDRIVER_PATH'] = '/nix/store/3qnxr5x6gw3k9a9i7d0akz0m6bksbwff-chromedriver-125.0.6422.141/bin/chromedriver'

logger = logging.getLogger(__name__)

# Global lock to prevent multiple screenshot processes
_screenshot_lock = threading.Lock()

def setup_chrome_driver():
    """Simple Chrome driver setup with timeout protection"""
    options = webdriver.ChromeOptions()
    
    # Essential options only
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1920,1080")
    options.add_argument("--timeout=10")
    
    # Exclude automation switches
    options.add_experimental_option('excludeSwitches', ['enable-automation'])
    options.add_experimental_option('useAutomationExtension', False)
    
    # Human-like user agent
    options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36")
    
    try:
        # Use the working system Chrome driver path directly
        from selenium.webdriver.chrome.service import Service
        service = Service('/nix/store/3qnxr5x6gw3k9a9i7d0akz0m6bksbwff-chromedriver-125.0.6422.141/bin/chromedriver')
        driver = webdriver.Chrome(service=service, options=options)
        
        # Additional stealth measures
        driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        
        logger.info("Chrome driver initialized successfully")
        return driver
    except Exception as e:
        logger.error(f"Failed to setup Chrome driver: {str(e)}")
        return None

def capture_screenshot_from_url(url, output_path):
    """Capture a screenshot from a given URL with lottery website protection handling"""
    # Prevent multiple screenshot processes from running simultaneously
    if not _screenshot_lock.acquire(blocking=False):
        logger.warning("Screenshot capture already in progress, skipping")
        return False
    
    try:
        # Simple, working Chrome setup
        options = webdriver.ChromeOptions()
        options.add_argument('--headless')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--window-size=1920,1080')
        
        from selenium.webdriver.chrome.service import Service
        service = Service('/nix/store/3qnxr5x6gw3k9a9i7d0akz0m6bksbwff-chromedriver-125.0.6422.141/bin/chromedriver')
        
        try:
            driver = webdriver.Chrome(service=service, options=options)
            driver.set_page_load_timeout(15)
        except Exception as e:
            logger.error(f"Failed to create driver: {e}")
            return False
        
        try:
            logger.info(f"Capturing screenshot from {url}")
            
            # Set shorter timeout and ensure screenshots directory exists
            driver.set_page_load_timeout(15)
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            
            try:
                # Navigate directly to the lottery website
                logger.info(f"Navigating to {url}")
                driver.get(url)
                
                # Wait for page to load
                time.sleep(5)
                
                # Simple screenshot without complex scrolling
                logger.info("Taking screenshot...")
                screenshot_success = driver.save_screenshot(output_path)
                
                if screenshot_success and os.path.exists(output_path):
                    file_size = os.path.getsize(output_path)
                    logger.info(f"Screenshot saved: {output_path} ({file_size} bytes)")
                    
                    # Apply smart cropping if file is valid
                    if file_size > 1000:
                        try:
                            crop_white_space(output_path, output_path)
                            logger.info("Smart cropping applied")
                        except Exception as crop_error:
                            logger.warning(f"Smart cropping failed: {crop_error}")
                        
                        return True
                    else:
                        logger.error("Screenshot file too small")
                        return False
                else:
                    logger.error("Failed to save screenshot")
                    return False
                
                logger.info(f"Page loaded and scrolled, ready for full screenshot")
                
            except Exception as load_error:
                logger.warning(f"Page load timeout, continuing with screenshot: {load_error}")
            
            # Take full-page screenshot with retry mechanism
            for attempt in range(3):
                try:
                    logger.info(f"Capturing full-page screenshot (attempt {attempt + 1})")
                    
                    # Get the full page height including all content
                    total_height = driver.execute_script("""
                        return Math.max(
                            document.body.scrollHeight,
                            document.body.offsetHeight,
                            document.documentElement.clientHeight,
                            document.documentElement.scrollHeight,
                            document.documentElement.offsetHeight
                        );
                    """)
                    
                    # Ensure minimum height for lottery pages
                    total_height = max(total_height, 2000)
                    logger.info(f"Full page height calculated: {total_height}px")
                    
                    # Set browser to capture the complete page
                    driver.set_window_size(1920, total_height)
                    time.sleep(3)
                    
                    # Scroll to bottom to ensure all content is loaded
                    driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                    time.sleep(2)
                    
                    # Scroll back to top for clean screenshot
                    driver.execute_script("window.scrollTo(0, 0);")
                    time.sleep(1)
                    
                    # Take the full screenshot first
                    temp_path = output_path.replace('.png', '_temp.png')
                    driver.save_screenshot(temp_path)
                    
                    # Crop the screenshot to remove white space and focus on lottery content
                    if os.path.exists(temp_path):
                        try:
                            from PIL import Image
                            import numpy as np
                            
                            # Open and process the image
                            img = Image.open(temp_path)
                            img_array = np.array(img)
                            
                            # Find the content boundaries by detecting non-white areas
                            # Look for areas that aren't pure white (255,255,255)
                            gray = np.mean(img_array, axis=2)
                            content_mask = gray < 250  # Slightly less than pure white to catch subtle content
                            
                            # Find bounding box of content
                            rows = np.any(content_mask, axis=1)
                            cols = np.any(content_mask, axis=0)
                            
                            if np.any(rows) and np.any(cols):
                                top, bottom = np.where(rows)[0][[0, -1]]
                                left, right = np.where(cols)[0][[0, -1]]
                                
                                # Add small padding around content
                                padding = 50
                                top = max(0, top - padding)
                                left = max(0, left - padding)
                                bottom = min(img_array.shape[0], bottom + padding)
                                right = min(img_array.shape[1], right + padding)
                                
                                # Crop the image to content area
                                cropped_img = img.crop((left, top, right, bottom))
                                cropped_img.save(output_path, 'PNG', quality=95)
                                
                                logger.info(f"✓ Screenshot cropped from {img.size} to {cropped_img.size}")
                            else:
                                # If no content detected, save original
                                img.save(output_path, 'PNG', quality=95)
                                logger.warning("No content boundaries detected, saving original")
                            
                            # Clean up temp file
                            os.remove(temp_path)
                            
                        except ImportError:
                            # If PIL not available, use original screenshot
                            os.rename(temp_path, output_path)
                            logger.warning("PIL not available, using uncropped screenshot")
                        except Exception as crop_error:
                            # If cropping fails, use original screenshot
                            os.rename(temp_path, output_path)
                            logger.warning(f"Cropping failed, using original: {crop_error}")
                    
                    # Verify final screenshot was created
                    if os.path.exists(output_path):
                        size = os.path.getsize(output_path)
                        logger.info(f"Final screenshot saved! File size: {size} bytes")
                        
                        if size > 5000:
                            logger.info("✓ Screenshot captured and optimized successfully")
                            return True
                        else:
                            logger.warning(f"Screenshot small ({size} bytes) but saved")
                            return True
                    else:
                        logger.error(f"Screenshot file not created on attempt {attempt + 1}")
                        if attempt < 2:
                            time.sleep(2)
                        
                except Exception as screenshot_error:
                    logger.error(f"Screenshot attempt {attempt + 1} failed: {screenshot_error}")
                    if attempt < 2:
                        time.sleep(2)
            
            logger.error("All screenshot attempts failed")
            return False
            
        except Exception as e:
            logger.error(f"Error capturing screenshot from {url}: {str(e)}")
            return False
        finally:
            try:
                if driver:
                    driver.quit()
            except:
                pass  # Ignore cleanup errors
                
    finally:
        _screenshot_lock.release()

def retake_all_screenshots(app, use_threading=True):
    """Retake all screenshots from configured URLs"""
    with app.app_context():
        try:
            screenshots = Screenshot.query.all()
            count = 0
            
            for screenshot in screenshots:
                if retake_single_screenshot(screenshot, app):
                    count += 1
                    
            logger.info(f"Successfully retook {count} screenshots")
            return count
            
        except Exception as e:
            logger.error(f"Error retaking all screenshots: {str(e)}")
            return 0

def retake_screenshot_by_id(screenshot_id, app):
    """Retake a specific screenshot by ID"""
    with app.app_context():
        try:
            screenshot = Screenshot.query.get(screenshot_id)
            if not screenshot:
                logger.error(f"Screenshot with ID {screenshot_id} not found")
                return False
                
            return retake_single_screenshot(screenshot, app)
            
        except Exception as e:
            logger.error(f"Error retaking screenshot {screenshot_id}: {str(e)}")
            return False

def retake_single_screenshot(screenshot, app):
    """Retake a single screenshot object"""
    try:
        from models import db
        
        # Ensure screenshots directory exists
        screenshot_dir = os.path.join(os.getcwd(), 'screenshots')
        os.makedirs(screenshot_dir, exist_ok=True)
        
        # Generate filename based on lottery type and URL
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        url_part = screenshot.url.split('/')[-1] if screenshot.url else 'unknown'
        filename = f"{timestamp}_{url_part}.png"
        output_path = os.path.join(screenshot_dir, filename)
        
        logger.info(f"Attempting to retake screenshot: {screenshot.lottery_type} from {screenshot.url}")
        
        # Capture screenshot using human-like browser behavior
        if capture_screenshot_from_url(screenshot.url, output_path):
            # Update database record with new path and timestamp
            screenshot.path = output_path
            screenshot.timestamp = datetime.utcnow()
            screenshot.processed = False  # Mark as unprocessed for fresh data
            
            with app.app_context():
                db.session.commit()
            
            logger.info(f"✓ Successfully updated screenshot for {screenshot.lottery_type}")
            logger.info(f"✓ New file saved: {output_path}")
            return True
        else:
            logger.warning(f"Failed to capture screenshot for {screenshot.lottery_type}")
            return False
            
    except Exception as e:
        logger.error(f"Error retaking screenshot for {screenshot.lottery_type}: {str(e)}")
        return False

def cleanup_old_screenshots():
    """Clean up old screenshot files to save space"""
    try:
        screenshot_dir = os.path.join(os.getcwd(), 'screenshots')
        if not os.path.exists(screenshot_dir):
            return 0
            
        # Get all files in screenshot directory
        files = os.listdir(screenshot_dir)
        png_files = [f for f in files if f.endswith('.png')]
        
        # Sort by modification time, keep only the latest 50
        file_paths = [(f, os.path.join(screenshot_dir, f)) for f in png_files]
        file_paths.sort(key=lambda x: os.path.getmtime(x[1]), reverse=True)
        
        deleted_count = 0
        for filename, filepath in file_paths[50:]:  # Keep latest 50, delete rest
            try:
                os.remove(filepath)
                deleted_count += 1
                logger.info(f"Deleted old screenshot: {filename}")
            except Exception as e:
                logger.error(f"Error deleting {filename}: {str(e)}")
                
        return deleted_count
        
    except Exception as e:
        logger.error(f"Error during cleanup: {str(e)}")
        return 0

def retake_selected_screenshots(app, selected_urls, use_threading=True):
    """Retake screenshots for specific lottery URLs
    
    Args:
        app: Flask application instance
        selected_urls (list): List of URLs to capture screenshots for
        use_threading (bool): Whether to use threading for captures
        
    Returns:
        int: Number of screenshots successfully captured
    """
    if not selected_urls:
        logger.warning("No URLs provided for screenshot capture")
        return 0
        
    with _screenshot_lock:
        logger.info(f"Starting selective screenshot capture for {len(selected_urls)} URLs")
        
        with app.app_context():
            success_count = 0
            
            for url in selected_urls:
                try:
                    logger.info(f"Capturing screenshot for: {url}")
                    # Generate output path for screenshot
                    from urllib.parse import urlparse
                    import re
                    
                    # Create filename from URL
                    parsed = urlparse(url)
                    filename = re.sub(r'[^\w\-_.]', '_', parsed.path.strip('/'))
                    if not filename:
                        filename = parsed.netloc.replace('.', '_')
                    filename = f"{filename}_{int(time.time())}.png"
                    
                    output_path = os.path.join(os.getcwd(), 'screenshots', filename)
                    success = capture_screenshot_from_url(url, output_path)
                    if success:
                        success_count += 1
                        logger.info(f"Successfully captured screenshot for {url}")
                    else:
                        logger.warning(f"Failed to capture screenshot for {url}")
                        
                    # Small delay between captures to avoid rate limiting
                    time.sleep(2)
                    
                except Exception as e:
                    logger.error(f"Error capturing screenshot for {url}: {str(e)}")
                    
            logger.info(f"Selective screenshot capture completed. {success_count}/{len(selected_urls)} successful")
            return success_count

def init_scheduler(app):
    """Initialize screenshot scheduler (placeholder for future automation)"""
    logger.info("Screenshot manager initialized")
    return True