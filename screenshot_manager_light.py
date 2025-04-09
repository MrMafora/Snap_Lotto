"""
Lightweight screenshot manager for capturing lottery website screenshots
using requests instead of Playwright to reduce dependencies
"""
import os
import logging
import traceback
from datetime import datetime
from pathlib import Path
import threading
import requests
from io import BytesIO
from PIL import Image
from models import db, Screenshot

logger = logging.getLogger(__name__)

# Create directory for screenshots if it doesn't exist
SCREENSHOT_DIR = os.path.join(os.getcwd(), 'screenshots')
os.makedirs(SCREENSHOT_DIR, exist_ok=True)

# Thread semaphore to limit concurrent screenshots
# This prevents "can't start new thread" errors by limiting resource usage
MAX_CONCURRENT_THREADS = 3
screenshot_semaphore = threading.Semaphore(MAX_CONCURRENT_THREADS)

def capture_screenshot_light(url, lottery_type=None):
    """
    Capture screenshot of the specified URL using requests instead of Playwright.
    This is a lightweight alternative that doesn't require browser engines.
    
    Warning: This method may not work for websites that require JavaScript to render content.
    
    Args:
        url (str): The URL to capture
        lottery_type (str, optional): The type of lottery. If None, extracted from URL.
        
    Returns:
        tuple: (filepath, screenshot_data, None) or (None, None, None) if failed
    """
    if not lottery_type:
        lottery_type = extract_lottery_type_from_url(url)
    
    try:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{timestamp}_{url.split('/')[-1]}.png"
        filepath = os.path.join(SCREENSHOT_DIR, filename)
        
        logger.info(f"Capturing screenshot from {url} using requests")
        
        # Set headers to mimic a browser
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9",
            "Accept-Encoding": "gzip, deflate, br",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",
            "DNT": "1"
        }
        
        # Fetch the page content
        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()  # Raise exception for 4XX/5XX responses
        
        # Save the content directly as text/html
        html_content = response.text
        
        # Generate a simple image with the URL for the screenshot record
        # This will be used just as a placeholder
        img = Image.new('RGB', (1200, 800), color = (20, 20, 20))
        
        # Save the image to the file system
        img.save(filepath)
        
        # Save HTML content to a file with the same name but .html extension
        html_filepath = os.path.splitext(filepath)[0] + '.html'
        with open(html_filepath, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        logger.info(f"Screenshot saved to {filepath} and HTML saved to {html_filepath}")
        
        # Read the saved screenshot file to return its content
        with open(filepath, 'rb') as f:
            screenshot_data = f.read()
        
        return filepath, screenshot_data, None
                
    except Exception as e:
        logger.error(f"Error capturing screenshot with requests: {str(e)}")
        traceback.print_exc()
        return None, None, None

def extract_lottery_type_from_url(url):
    """
    Extract lottery type from URL.
    
    Args:
        url (str): URL to extract lottery type from
        
    Returns:
        str: Lottery type or 'Unknown' if not found
    """
    url_lower = url.lower()
    
    if 'lotto-plus-1' in url_lower or 'lotto-plus-1-results' in url_lower:
        return 'Lotto Plus 1'
    elif 'lotto-plus-2' in url_lower or 'lotto-plus-2-results' in url_lower:
        return 'Lotto Plus 2'
    elif 'powerball-plus' in url_lower:
        return 'Powerball Plus'
    elif 'powerball' in url_lower:
        return 'Powerball'
    elif 'daily-lotto' in url_lower:
        return 'Daily Lotto'
    elif 'lotto' in url_lower:
        return 'Lotto'
    
    return 'Unknown'

def capture_screenshot(url, lottery_type=None):
    """
    Main function to capture screenshot of the specified URL.
    This wrapper function will try to use the lightweight method first,
    and fall back to Playwright if available and needed.
    
    Args:
        url (str): The URL to capture
        lottery_type (str, optional): The type of lottery. If None, extracted from URL.
        
    Returns:
        tuple: (filepath, screenshot_data, zoom_filepath) or (None, None, None) if failed
    """
    if not lottery_type:
        lottery_type = extract_lottery_type_from_url(url)
    
    # Try with lightweight method first
    result = capture_screenshot_light(url, lottery_type)
    
    # If lightweight method worked, return its result
    if result and result[0]:
        filepath, screenshot_data, _ = result
        
        # Create a Screenshot record in the database
        try:
            screenshot = Screenshot(
                url=url,
                lottery_type=lottery_type,
                timestamp=datetime.now(),
                path=filepath,
                processed=False
            )
            db.session.add(screenshot)
            db.session.commit()
            logger.info(f"Screenshot record added to database for {lottery_type}")
        except Exception as e:
            logger.error(f"Error saving screenshot record to database: {str(e)}")
        
        return result
    
    # Otherwise, try to use Playwright if it's available as a fallback
    try:
        logger.info("Lightweight screenshot failed, trying with Playwright if available")
        
        # Import Playwright only if needed, to avoid dependency issues if not installed
        try:
            from screenshot_manager_playwright import capture_screenshot_with_playwright
            logger.info("Using Playwright as fallback for screenshot capture")
            return capture_screenshot_with_playwright(url, lottery_type)
        except ImportError:
            logger.warning("Playwright not available. Cannot capture screenshot of dynamic content.")
            return None, None, None
    except Exception as e:
        logger.error(f"Error capturing screenshot with fallback method: {str(e)}")
        return None, None, None

def cleanup_old_screenshots(days_to_keep=7):
    """
    Clean up old screenshots to save disk space.
    
    Args:
        days_to_keep (int): Number of days of screenshots to keep
    """
    try:
        from datetime import timedelta
        
        # Calculate cutoff date
        cutoff_date = datetime.now() - timedelta(days=days_to_keep)
        logger.info(f"Cleaning up screenshots older than {cutoff_date}")
        
        # Find old screenshots
        old_screenshots = Screenshot.query.filter(Screenshot.timestamp < cutoff_date).all()
        
        # Delete files and records
        for screenshot in old_screenshots:
            try:
                # Delete file if it exists
                if os.path.isfile(screenshot.path):
                    os.remove(screenshot.path)
                    logger.info(f"Deleted old screenshot file: {screenshot.path}")
                
                # Check for related HTML file and delete if it exists
                html_path = os.path.splitext(screenshot.path)[0] + '.html'
                if os.path.isfile(html_path):
                    os.remove(html_path)
                    logger.info(f"Deleted related HTML file: {html_path}")
                
                # Delete database record
                db.session.delete(screenshot)
                
            except Exception as e:
                logger.error(f"Error deleting screenshot {screenshot.id}: {str(e)}")
        
        # Commit the transaction
        db.session.commit()
        logger.info(f"Cleaned up {len(old_screenshots)} old screenshots")
        
    except Exception as e:
        logger.error(f"Error cleaning up old screenshots: {str(e)}")