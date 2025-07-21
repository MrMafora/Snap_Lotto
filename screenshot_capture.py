#!/usr/bin/env python3
"""
Restored Screenshot Capture System Using Playwright with Chromium
This implementation uses the Chromium browser found in Replit's Nix store
"""

import os
import time
import logging
from datetime import datetime
from playwright.sync_api import sync_playwright
from models import Screenshot, db
from flask_login import current_user

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Path to Chromium in Replit environment (discovered via system scan)
CHROMIUM_PATH = "/nix/store/zi4f80l169xlmivz8vja8wlphq74qqk0-chromium-125.0.6422.141/bin/chromium"

# South African Lottery URLs - exact URLs from working system
LOTTERY_URLS = {
    'LOTTO': 'https://www.nationallottery.co.za/results/lotto',
    'LOTTO PLUS 1': 'https://www.nationallottery.co.za/results/lotto-plus-1-results',
    'LOTTO PLUS 2': 'https://www.nationallottery.co.za/results/lotto-plus-2-results',
    'POWERBALL': 'https://www.nationallottery.co.za/results/powerball',
    'POWERBALL PLUS': 'https://www.nationallottery.co.za/results/powerball-plus',
    'DAILY LOTTO': 'https://www.nationallottery.co.za/results/daily-lotto'
}

def capture_lottery_screenshot(lottery_type, url):
    """
    Capture a screenshot of a lottery website using Playwright with explicit Chromium path
    
    Args:
        lottery_type (str): Type of lottery (e.g., 'LOTTO', 'POWERBALL')
        url (str): URL to capture
        
    Returns:
        dict: Result with success status, filename, and other details
    """
    logger.info(f"Starting screenshot capture: {lottery_type} from {url}")
    
    try:
        with sync_playwright() as p:
            # Launch browser with explicit executable path and enhanced arguments
            browser = p.chromium.launch(
                executable_path=CHROMIUM_PATH,
                headless=True,
                args=[
                    '--no-sandbox',
                    '--disable-setuid-sandbox',
                    '--disable-dev-shm-usage',
                    '--disable-gpu',
                    '--disable-web-security',
                    '--disable-features=IsolateOrigins,site-per-process',
                    '--window-size=1920,1080',
                    '--disable-blink-features=AutomationControlled',
                    '--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36',
                    '--accept-lang=en-US,en;q=0.9',
                    '--disable-accelerated-2d-canvas',
                    '--disable-background-timer-throttling',
                    '--disable-backgrounding-occluded-windows',
                    '--disable-renderer-backgrounding',
                    '--force-color-profile=srgb'
                ]
            )
            
            # Create context with enhanced settings
            context = browser.new_context(
                viewport={'width': 1920, 'height': 1080},
                user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36',
                locale='en-US',
                timezone_id='Africa/Johannesburg',
                extra_http_headers={
                    'Accept-Language': 'en-US,en;q=0.9',
                    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                    'Accept-Encoding': 'gzip, deflate, br',
                    'Connection': 'keep-alive',
                    'Upgrade-Insecure-Requests': '1'
                }
            )
            
            # Create page from context
            page = context.new_page()
            
            # Add stealth scripts before navigation
            page.add_init_script("""
                Object.defineProperty(navigator, 'webdriver', {
                    get: () => undefined
                });
                Object.defineProperty(navigator, 'plugins', {
                    get: () => [1, 2, 3, 4, 5]
                });
                Object.defineProperty(navigator, 'languages', {
                    get: () => ['en-US', 'en']
                });
                window.chrome = { runtime: {} };
                Object.defineProperty(navigator, 'permissions', {
                    get: () => ({ query: () => Promise.resolve({ state: 'granted' }) })
                });
            """)
            
            # Navigate to the page with robust error handling
            logger.info(f"Navigating to {url}...")
            try:
                response = page.goto(url, wait_until='domcontentloaded', timeout=60000)
                if response and response.status >= 400:
                    logger.warning(f"HTTP {response.status} response")
            except Exception as nav_error:
                logger.warning(f"Navigation issue: {nav_error}")
                # Continue anyway - page might still be usable
            
            # Wait for content to load
            page.wait_for_timeout(3000)
            
            # Scroll to ensure full content loads
            page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            page.wait_for_timeout(1000)
            page.evaluate("window.scrollTo(0, 0)")
            
            # Generate filename
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            safe_lottery_type = lottery_type.lower().replace(' ', '_')
            filename = f"{timestamp}_{safe_lottery_type}.png"
            filepath = os.path.join('screenshots', filename)
            
            # Ensure screenshots directory exists
            os.makedirs('screenshots', exist_ok=True)
            
            # Take screenshot with full page
            logger.info(f"Taking screenshot: {filename}")
            page.screenshot(path=filepath, full_page=True)
            
            # Get file size
            file_size = os.path.getsize(filepath)
            logger.info(f"✅ Screenshot saved: {filename} ({file_size:,} bytes)")
            
            # Save to database
            try:
                screenshot = Screenshot(
                    lottery_type=lottery_type,
                    filename=filename,
                    file_path=filepath,
                    url=url
                )
                db.session.add(screenshot)
                db.session.commit()
                logger.info(f"Screenshot record saved to database")
            except Exception as db_error:
                logger.warning(f"Database save failed: {db_error}")
            
            browser.close()
            
            return {
                'success': True,
                'lottery_type': lottery_type,
                'filename': filename,
                'filepath': filepath,
                'file_size': file_size,
                'url': url
            }
            
    except Exception as e:
        logger.error(f"Screenshot capture error for {lottery_type}: {str(e)}")
        return {
            'success': False,
            'lottery_type': lottery_type,
            'error': str(e)
        }

def capture_all_lottery_screenshots():
    """
    Capture screenshots for all lottery types - ensuring only ONE per type
    
    Returns:
        dict: Summary of results
    """
    logger.info("Starting capture of all lottery screenshots...")
    
    # First, clean up old screenshots for each lottery type to ensure only 1 per type
    cleanup_duplicate_screenshots()
    
    results = {
        'success': [],
        'failed': [],
        'total_success': 0,
        'total_failed': 0,
        'total_processed': 0
    }
    
    for lottery_type, url in LOTTERY_URLS.items():
        logger.info(f"Processing {lottery_type}...")
        
        # Delete existing screenshots for this lottery type before capturing new one
        try:
            from models import Screenshot, db
            existing_screenshots = Screenshot.query.filter_by(lottery_type=lottery_type).all()
            for screenshot in existing_screenshots:
                # Delete file if it exists
                if screenshot.file_path and os.path.exists(screenshot.file_path):
                    try:
                        os.remove(screenshot.file_path)
                        logger.info(f"Deleted old file: {screenshot.file_path}")
                    except Exception as e:
                        logger.warning(f"Could not delete file {screenshot.file_path}: {e}")
                # Delete database record
                db.session.delete(screenshot)
            db.session.commit()
            logger.info(f"Cleaned up existing {lottery_type} screenshots")
        except Exception as e:
            logger.warning(f"Error cleaning up existing screenshots for {lottery_type}: {e}")
        
        # Now capture new screenshot
        result = capture_lottery_screenshot(lottery_type, url)
        
        if result['success']:
            results['success'].append(result)
            results['total_success'] += 1
        else:
            results['failed'].append(result)
            results['total_failed'] += 1
        
        results['total_processed'] += 1
        
        # Brief pause between captures
        if lottery_type != list(LOTTERY_URLS.keys())[-1]:
            time.sleep(2)
    
    logger.info(f"Capture complete: {results['total_success']}/{results['total_processed']} successful")
    logger.info(f"Total screenshots in system: exactly {results['total_success']} (one per lottery type)")
    return results

def cleanup_duplicate_screenshots():
    """Remove duplicate screenshots, keeping only the latest one per lottery type"""
    try:
        from models import Screenshot, db
        
        lottery_types = ['LOTTO', 'LOTTO PLUS 1', 'LOTTO PLUS 2', 'POWERBALL', 'POWERBALL PLUS', 'DAILY LOTTO']
        total_deleted = 0
        
        for lottery_type in lottery_types:
            # Get all screenshots for this lottery type, ordered by timestamp (newest first)
            screenshots = Screenshot.query.filter_by(lottery_type=lottery_type).order_by(Screenshot.timestamp.desc()).all()
            
            if len(screenshots) > 1:
                # Keep the first (newest) one, delete the rest
                screenshots_to_delete = screenshots[1:]  # Skip the first (newest)
                
                for screenshot in screenshots_to_delete:
                    # Delete file if it exists
                    if screenshot.file_path and os.path.exists(screenshot.file_path):
                        try:
                            os.remove(screenshot.file_path)
                        except Exception as e:
                            logger.warning(f"Could not delete file {screenshot.file_path}: {e}")
                    
                    # Delete database record
                    db.session.delete(screenshot)
                    total_deleted += 1
        
        db.session.commit()
        logger.info(f"Cleanup complete: deleted {total_deleted} duplicate screenshots")
        
    except Exception as e:
        logger.error(f"Error during cleanup: {e}")

def test_screenshot_capture():
    """Test screenshot capture with one lottery type"""
    logger.info("Testing screenshot capture system...")
    
    # Test with LOTTO
    result = capture_lottery_screenshot('LOTTO', LOTTERY_URLS['LOTTO'])
    
    if result['success']:
        logger.info(f"✅ TEST SUCCESS: Screenshot system working! File: {result['filename']}")
        return True
    else:
        logger.error(f"❌ TEST FAILED: {result.get('error', 'Unknown error')}")
        return False

def cleanup_old_screenshots(days_old=7):
    """Clean up old screenshots"""
    logger.info(f"Cleaning up screenshots older than {days_old} days...")
    
    try:
        from datetime import timedelta
        cutoff_date = datetime.now() - timedelta(days=days_old)
        
        # Find old screenshots in database
        old_screenshots = Screenshot.query.filter(Screenshot.timestamp < cutoff_date).all()
        
        deleted_files = 0
        deleted_records = 0
        
        for screenshot in old_screenshots:
            # Delete file if it exists
            if screenshot.file_path and os.path.exists(screenshot.file_path):
                try:
                    os.remove(screenshot.file_path)
                    deleted_files += 1
                except Exception as e:
                    logger.warning(f"Could not delete file {screenshot.file_path}: {e}")
            
            # Delete database record
            db.session.delete(screenshot)
            deleted_records += 1
        
        db.session.commit()
        
        logger.info(f"Cleanup complete: {deleted_files} files and {deleted_records} records removed")
        
        return {
            'success': True,
            'deleted_files': deleted_files,
            'deleted_records': deleted_records
        }
        
    except Exception as e:
        logger.error(f"Cleanup error: {e}")
        return {
            'success': False,
            'error': str(e)
        }

if __name__ == '__main__':
    print("Testing screenshot capture system with Chromium...")
    if test_screenshot_capture():
        print("✅ Screenshot system working! Running full capture...")
        results = capture_all_lottery_screenshots()
        print(f"Captured {results['total_success']}/{results['total_processed']} lottery types")
    else:
        print("❌ Screenshot system test failed")