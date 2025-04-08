import os
import logging
import urllib.request
import urllib.error
import time
from datetime import datetime
from models import Screenshot
from app import db

logger = logging.getLogger(__name__)

# Create directory for screenshots if it doesn't exist
SCREENSHOT_DIR = os.path.join(os.getcwd(), 'screenshots')
os.makedirs(SCREENSHOT_DIR, exist_ok=True)

def take_screenshot(url):
    """
    A simplified function to capture the HTML of the specified URL.
    Instead of taking an actual screenshot, it saves the HTML content for OCR processing.
    
    Args:
        url (str): The URL to capture
        
    Returns:
        str: Path to the saved HTML file, or None if failed
    """
    try:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{timestamp}_{url.split('/')[-1]}.html"
        filepath = os.path.join(SCREENSHOT_DIR, filename)
        
        logger.info(f"Capturing content from {url}")
        
        # Add user agent to avoid being blocked
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3'
        }
        
        req = urllib.request.Request(url, headers=headers)
        
        with urllib.request.urlopen(req, timeout=30) as response:
            html_content = response.read()
            
            # Save the HTML content to file
            with open(filepath, 'wb') as f:
                f.write(html_content)
            
            logger.info(f"HTML content saved to {filepath}")
            return filepath
            
    except urllib.error.URLError as e:
        logger.error(f"Error opening URL: {str(e)}")
        return None
    except Exception as e:
        logger.error(f"Error capturing content: {str(e)}")
        return None

def capture_screenshot(url, lottery_type=None):
    """
    Capture content from the specified URL and save metadata to database.
    
    Args:
        url (str): The URL to capture
        lottery_type (str, optional): The type of lottery. If None, extracted from URL.
        
    Returns:
        str: Path to the saved file, or None if failed
    """
    # Extract lottery type from URL if not provided
    if not lottery_type:
        lottery_type = extract_lottery_type_from_url(url)
    
    # Run screenshot/content capture function
    filepath = take_screenshot(url)
    
    if filepath:
        # Save content info to database
        screenshot = Screenshot(
            url=url,
            lottery_type=lottery_type,
            timestamp=datetime.utcnow(),
            path=filepath,
            processed=False
        )
        
        db.session.add(screenshot)
        db.session.commit()
        
        logger.info(f"Content capture record saved to database with ID {screenshot.id}")
        return filepath
    
    return None

def extract_lottery_type_from_url(url):
    """Extract lottery type from the URL"""
    url_lower = url.lower()
    
    if 'lotto-plus-1' in url_lower:
        return 'Lotto Plus 1'
    elif 'lotto-plus-2' in url_lower:
        return 'Lotto Plus 2'
    elif 'powerball-plus' in url_lower:
        return 'Powerball Plus'
    elif 'powerball' in url_lower:
        return 'Powerball'
    elif 'daily-lotto' in url_lower:
        return 'Daily Lotto'
    elif 'lotto' in url_lower:
        return 'Lotto'
    else:
        return 'Unknown'

def get_unprocessed_screenshots():
    """Get all unprocessed screenshots from the database"""
    return Screenshot.query.filter_by(processed=False).all()

def mark_screenshot_as_processed(screenshot_id):
    """Mark a screenshot as processed in the database"""
    screenshot = Screenshot.query.get(screenshot_id)
    if screenshot:
        screenshot.processed = True
        db.session.commit()
        logger.info(f"Screenshot {screenshot_id} marked as processed")
