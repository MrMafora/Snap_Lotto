"""
Generate all lottery screenshots using Playwright or wkhtmltoimage.

This script:
1. Uses Playwright to capture screenshots from the National Lottery website
2. Falls back to wkhtmltoimage if Playwright fails
3. Updates the database with correct paths
4. Never creates placeholder images
"""
import os
import sys
import logging
import time
import subprocess
from datetime import datetime
import tempfile
import shutil
from models import Screenshot, db
from config import Config
from urllib.parse import urlparse
from main import app

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Ensure screenshot directory exists
os.makedirs(Config.SCREENSHOT_DIR, exist_ok=True)

def capture_with_playwright(url, output_path, lottery_type=None):
    """
    Capture a screenshot using Playwright
    
    Args:
        url (str): URL to capture
        output_path (str): Where to save the screenshot
        lottery_type (str, optional): Type of lottery for logging
        
    Returns:
        bool: Success status
    """
    try:
        from playwright.sync_api import sync_playwright
        
        logger.info(f"Capturing {lottery_type or 'screenshot'} from {url} using Playwright")
        
        with sync_playwright() as p:
            # Launch browser with maximum timeout and retries
            for attempt in range(3):
                try:
                    browser = p.chromium.launch(timeout=60000)
                    page = browser.new_page(viewport={"width": 1200, "height": 1600})
                    
                    # Navigate with generous timeout
                    page.goto(url, wait_until="networkidle", timeout=60000)
                    
                    # Wait for content to fully load
                    page.wait_for_timeout(3000)
                    
                    # Ensure screenshot directory exists
                    os.makedirs(os.path.dirname(output_path), exist_ok=True)
                    
                    # Take the screenshot with high quality
                    page.screenshot(path=output_path, full_page=True)
                    browser.close()
                    
                    # Verify the file was created successfully
                    if os.path.exists(output_path) and os.path.getsize(output_path) > 1000:
                        logger.info(f"Successfully captured {lottery_type or 'screenshot'}")
                        return True
                    else:
                        logger.warning(f"Screenshot file empty or too small: {output_path}")
                        # Try again
                        if os.path.exists(output_path):
                            os.remove(output_path)
                            
                except Exception as e:
                    logger.error(f"Playwright attempt {attempt+1} failed: {str(e)}")
                    if 'browser' in locals():
                        browser.close()
                    time.sleep(2)  # Wait before retry
            
            logger.error(f"All Playwright attempts failed for {lottery_type or url}")
            return False
                
    except ImportError:
        logger.error("Playwright not installed. Install with 'pip install playwright' and 'playwright install'.")
        return False
    except Exception as e:
        logger.error(f"Error capturing screenshot with Playwright: {str(e)}")
        return False

def capture_with_wkhtmltoimage(url, output_path, lottery_type=None):
    """
    Capture a screenshot using wkhtmltoimage command line tool
    This is a more reliable method for capturing screenshots
    
    Args:
        url (str): URL to capture
        output_path (str): Path to save the screenshot
        lottery_type (str, optional): Type of lottery for logging
        
    Returns:
        bool: Success status
    """
    try:
        # Check if wkhtmltoimage is installed
        try:
            subprocess.run(['which', 'wkhtmltoimage'], check=True, capture_output=True)
        except subprocess.CalledProcessError:
            logger.error("wkhtmltoimage not installed. Cannot use fallback method.")
            return False
            
        logger.info(f"Capturing {lottery_type or 'screenshot'} from {url} using wkhtmltoimage")
        
        # Ensure target directory exists
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        # Use wkhtmltoimage to capture the screenshot
        cmd = [
            'wkhtmltoimage',
            '--quality', '100',
            '--width', '1200', 
            '--height', '1600',
            '--javascript-delay', '5000',  # Wait for JavaScript
            '--no-stop-slow-scripts',  # Don't stop slow scripts
            url,
            output_path
        ]
        
        logger.info(f"Running command: {' '.join(cmd)}")
        
        # Run the command with timeout
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
        
        # Check if successful
        if result.returncode == 0 and os.path.exists(output_path) and os.path.getsize(output_path) > 1000:
            logger.info(f"Successfully captured {lottery_type or 'screenshot'} with wkhtmltoimage")
            return True
        else:
            logger.error(f"wkhtmltoimage failed: {result.stderr}")
            if os.path.exists(output_path):
                os.remove(output_path)
            return False
            
    except Exception as e:
        logger.error(f"Error capturing screenshot with wkhtmltoimage: {str(e)}")
        return False

def capture_screenshot(url, lottery_type):
    """
    Capture a screenshot using Playwright
    
    Args:
        url (str): URL to capture
        lottery_type (str): Type of lottery
        
    Returns:
        tuple: (success status, file path)
    """
    # Generate a clean filename
    clean_type = lottery_type.replace(' ', '_').lower()
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = f"{clean_type}_{timestamp}.png"
    output_path = os.path.join(Config.SCREENSHOT_DIR, filename)
    
    # Use Playwright to capture the screenshot
    if capture_with_playwright(url, output_path, lottery_type):
        return True, output_path
    
    # Playwright failed, try again with a different browser
    try:
        from playwright.sync_api import sync_playwright
        
        # Try with Firefox instead of Chromium
        logger.info(f"Retrying {lottery_type} with Firefox browser")
        
        with sync_playwright() as p:
            try:
                browser = p.firefox.launch(timeout=60000)
                page = browser.new_page(viewport={"width": 1200, "height": 1600})
                page.goto(url, wait_until="networkidle", timeout=60000)
                page.wait_for_timeout(3000)
                page.screenshot(path=output_path, full_page=True)
                browser.close()
                
                if os.path.exists(output_path) and os.path.getsize(output_path) > 1000:
                    logger.info(f"Successfully captured {lottery_type} with Firefox")
                    return True, output_path
            except Exception as e:
                logger.error(f"Firefox capture failed: {str(e)}")
                if 'browser' in locals():
                    browser.close()
    except Exception as e:
        logger.error(f"Error setting up Firefox capture: {str(e)}")
    
    # All methods failed
    logger.error(f"Failed to capture screenshot for {lottery_type}")
    return False, None

def update_database(url, lottery_type, screenshot_path):
    """
    Update the database with the new screenshot path
    
    Args:
        url (str): URL that was captured
        lottery_type (str): Type of lottery
        screenshot_path (str): Path to the screenshot file
        
    Returns:
        bool: Success status
    """
    try:
        # Find existing screenshot in the database
        screenshot = Screenshot.query.filter_by(
            lottery_type=lottery_type
        ).first()
        
        if screenshot:
            # Update existing screenshot
            screenshot.path = screenshot_path
            screenshot.timestamp = datetime.now()
            screenshot.url = url
            
            # Delete old file if it exists and is different
            if screenshot.path and screenshot.path != screenshot_path and os.path.exists(screenshot.path):
                try:
                    os.remove(screenshot.path)
                except Exception as e:
                    logger.warning(f"Could not remove old screenshot: {str(e)}")
        else:
            # Create new screenshot record
            screenshot = Screenshot(
                lottery_type=lottery_type,
                path=screenshot_path,
                timestamp=datetime.now(),
                url=url
            )
            db.session.add(screenshot)
            
        # Commit changes
        db.session.commit()
        logger.info(f"Successfully updated database for {lottery_type}")
        return True
        
    except Exception as e:
        logger.error(f"Error updating database: {str(e)}")
        return False

def capture_all_screenshots():
    """
    Capture screenshots for all lottery types
    
    Returns:
        dict: Results of all screenshots
    """
    results = {}
    
    # Use the URLs from Config
    for result_url in Config.RESULTS_URLS:
        url = result_url['url']
        lottery_type = result_url['lottery_type']
        
        logger.info(f"Processing {lottery_type} from {url}")
        
        # Capture the screenshot
        success, path = capture_screenshot(url, lottery_type)
        
        if success and path:
            # Update the database
            db_success = update_database(url, lottery_type, path)
            
            results[lottery_type] = {
                'status': 'success' if db_success else 'database_error',
                'path': path,
                'url': url
            }
        else:
            results[lottery_type] = {
                'status': 'failed',
                'url': url
            }
    
    return results

if __name__ == "__main__":
    print("Generating all screenshot files...")
    
    with app.app_context():
        # Capture all screenshots
        results = capture_all_screenshots()
        
        # Print results
        print("\nResults:")
        for lottery_type, result in results.items():
            status = result['status']
            if status == 'success':
                print(f"  ✓ {lottery_type}: Successfully captured and stored (Path: {result['path']})")
            elif status == 'database_error':
                print(f"  ⚠ {lottery_type}: Captured but database update failed (Path: {result['path']})")
            else:
                print(f"  ✗ {lottery_type}: Failed to capture")
        
        # Count successes and failures
        success_count = sum(1 for result in results.values() if result['status'] == 'success')
        db_error_count = sum(1 for result in results.values() if result['status'] == 'database_error')
        fail_count = sum(1 for result in results.values() if result['status'] == 'failed')
        
        print(f"\nSummary: {success_count} successful, {db_error_count} database errors, {fail_count} failed")
        print("\nDownload Route:")
        print("  To download a screenshot, use the URL: /download-screenshot/<screenshot_id>")
        print("  The file will be served as an attachment with the correct filename.")