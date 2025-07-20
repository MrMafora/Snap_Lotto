"""
Screenshot capture functionality for South African lottery websites
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
from models import Screenshot, db
from flask_login import current_user

# Configure logging
logger = logging.getLogger(__name__)

# South African lottery websites to capture
LOTTERY_URLS = {
    'LOTTO': 'https://www.nationallottery.co.za/lotto/results',
    'LOTTO PLUS 1': 'https://www.nationallottery.co.za/lotto-plus/results', 
    'LOTTO PLUS 2': 'https://www.nationallottery.co.za/lotto-plus-2/results',
    'POWERBALL': 'https://www.nationallottery.co.za/powerball/results',
    'POWERBALL PLUS': 'https://www.nationallottery.co.za/powerball-plus/results',
    'DAILY LOTTO': 'https://www.nationallottery.co.za/daily-lotto/results'
}

def setup_chrome_driver():
    """Setup Chrome driver with appropriate options for screenshot capture"""
    chrome_options = Options()
    chrome_options.add_argument('--headless')  # Run in background
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('--disable-gpu')
    chrome_options.add_argument('--window-size=1920,1080')  # Full HD resolution
    chrome_options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36')
    
    try:
        driver = webdriver.Chrome(options=chrome_options)
        return driver
    except Exception as e:
        logger.error(f"Failed to setup Chrome driver: {e}")
        return None

def capture_lottery_screenshot(lottery_type, url, output_dir='screenshots'):
    """
    Capture screenshot of a specific lottery results page
    
    Args:
        lottery_type (str): Type of lottery (LOTTO, POWERBALL, etc.)
        url (str): URL to capture
        output_dir (str): Directory to save screenshots
        
    Returns:
        dict: Result with success status and details
    """
    
    # Ensure output directory exists
    os.makedirs(output_dir, exist_ok=True)
    
    # Generate filename with timestamp
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = f"{timestamp}_{lottery_type.lower().replace(' ', '_')}.png"
    filepath = os.path.join(output_dir, filename)
    
    driver = setup_chrome_driver()
    if not driver:
        return {
            'success': False,
            'error': 'Failed to setup browser driver',
            'lottery_type': lottery_type
        }
    
    try:
        logger.info(f"Capturing screenshot for {lottery_type} from {url}")
        
        # Navigate to the lottery results page
        driver.get(url)
        
        # Wait for page to load
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.TAG_NAME, "body"))
        )
        
        # Additional wait for dynamic content
        time.sleep(3)
        
        # Scroll to ensure all content is loaded
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(2)
        driver.execute_script("window.scrollTo(0, 0);")
        time.sleep(1)
        
        # Take screenshot
        driver.save_screenshot(filepath)
        
        # Get file size
        file_size = os.path.getsize(filepath) if os.path.exists(filepath) else 0
        
        # Save screenshot info to database
        screenshot = Screenshot(
            lottery_type=lottery_type,
            url=url,
            filename=filename,
            file_path=filepath,
            file_size=file_size,
            capture_method='selenium',
            created_by=current_user.id if hasattr(current_user, 'id') else None
        )
        
        db.session.add(screenshot)
        db.session.commit()
        
        logger.info(f"Successfully captured screenshot for {lottery_type}: {filename}")
        
        return {
            'success': True,
            'lottery_type': lottery_type,
            'filename': filename,
            'filepath': filepath,
            'file_size': file_size,
            'screenshot_id': screenshot.id
        }
        
    except Exception as e:
        logger.error(f"Error capturing screenshot for {lottery_type}: {e}")
        return {
            'success': False,
            'error': str(e),
            'lottery_type': lottery_type
        }
        
    finally:
        if driver:
            driver.quit()

def capture_all_lottery_screenshots():
    """
    Capture screenshots for all South African lottery types
    
    Returns:
        dict: Summary of capture results
    """
    
    results = {
        'success': [],
        'failed': [],
        'total_processed': 0,
        'total_success': 0,
        'total_failed': 0
    }
    
    logger.info("Starting capture of all lottery screenshots")
    
    for lottery_type, url in LOTTERY_URLS.items():
        results['total_processed'] += 1
        
        result = capture_lottery_screenshot(lottery_type, url)
        
        if result['success']:
            results['success'].append(result)
            results['total_success'] += 1
            logger.info(f"✅ {lottery_type}: {result['filename']}")
        else:
            results['failed'].append(result)
            results['total_failed'] += 1
            logger.error(f"❌ {lottery_type}: {result.get('error', 'Unknown error')}")
    
    logger.info(f"Screenshot capture completed: {results['total_success']}/{results['total_processed']} successful")
    
    return results

def cleanup_old_screenshots(days_old=7):
    """
    Clean up old screenshot files and database records
    
    Args:
        days_old (int): Delete screenshots older than this many days
        
    Returns:
        dict: Cleanup results
    """
    
    from datetime import timedelta
    
    cutoff_date = datetime.utcnow() - timedelta(days=days_old)
    
    try:
        # Find old screenshots in database
        old_screenshots = Screenshot.query.filter(Screenshot.timestamp < cutoff_date).all()
        
        deleted_files = 0
        deleted_records = 0
        
        for screenshot in old_screenshots:
            # Delete file if it exists
            if os.path.exists(screenshot.file_path):
                try:
                    os.remove(screenshot.file_path)
                    deleted_files += 1
                    logger.info(f"Deleted old screenshot file: {screenshot.filename}")
                except Exception as e:
                    logger.warning(f"Failed to delete file {screenshot.file_path}: {e}")
            
            # Delete database record
            db.session.delete(screenshot)
            deleted_records += 1
        
        db.session.commit()
        
        logger.info(f"Cleanup completed: {deleted_files} files, {deleted_records} records")
        
        return {
            'success': True,
            'deleted_files': deleted_files,
            'deleted_records': deleted_records,
            'cutoff_date': cutoff_date
        }
        
    except Exception as e:
        logger.error(f"Error during screenshot cleanup: {e}")
        db.session.rollback()
        return {
            'success': False,
            'error': str(e)
        }

def get_latest_screenshots():
    """
    Get the latest screenshots for each lottery type
    
    Returns:
        list: Latest screenshots grouped by lottery type
    """
    
    try:
        # Get latest screenshot for each lottery type
        screenshots = db.session.query(Screenshot)\
            .filter(Screenshot.status == 'active')\
            .order_by(Screenshot.lottery_type, Screenshot.timestamp.desc())\
            .all()
        
        # Group by lottery type and keep only the latest
        latest_screenshots = {}
        for screenshot in screenshots:
            if screenshot.lottery_type not in latest_screenshots:
                latest_screenshots[screenshot.lottery_type] = screenshot
        
        return list(latest_screenshots.values())
        
    except Exception as e:
        logger.error(f"Error retrieving latest screenshots: {e}")
        return []