"""
Playwright-based Screenshot Capture System
Based on the original working implementation from GitHub
"""

import os
import time
import logging
from datetime import datetime
from playwright.sync_api import sync_playwright
from models import Screenshot, db
from flask_login import current_user

# Configure logging
logger = logging.getLogger(__name__)

# South African Lottery URLs
LOTTERY_URLS = {
    'LOTTO': 'https://www.nationallottery.co.za/results/lotto',
    'LOTTO PLUS 1': 'https://www.nationallottery.co.za/results/lotto-plus-1-results',
    'LOTTO PLUS 2': 'https://www.nationallottery.co.za/results/lotto-plus-2-results',
    'POWERBALL': 'https://www.nationallottery.co.za/results/powerball',
    'POWERBALL PLUS': 'https://www.nationallottery.co.za/results/powerball-plus',
    'DAILY LOTTO': 'https://www.nationallottery.co.za/results/daily-lotto'
}

def capture_lottery_screenshot_playwright(lottery_type, url, output_dir='screenshots'):
    """
    Capture complete full-page screenshot using Playwright (original method)
    
    Args:
        lottery_type (str): Type of lottery
        url (str): URL to capture
        output_dir (str): Directory to save screenshots
    
    Returns:
        dict: Result with success status and details
    """
    # Ensure output directory exists
    os.makedirs(output_dir, exist_ok=True)
    
    # Generate filename with timestamp
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = f"{timestamp}_{lottery_type.lower().replace(' ', '_')}_playwright.png"
    filepath = os.path.join(output_dir, filename)
    
    try:
        logger.info(f"PLAYWRIGHT METHOD: Capturing {lottery_type} from {url}")
        
        with sync_playwright() as p:
            # Launch browser with optimal settings
            browser = p.chromium.launch(
                headless=True,
                args=[
                    "--no-sandbox",
                    "--disable-setuid-sandbox",
                    "--disable-dev-shm-usage",
                    "--disable-blink-features=AutomationControlled"
                ]
            )
            
            # Create context with proper viewport
            context = browser.new_context(
                viewport={'width': 1280, 'height': 1600},
                user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
            )
            
            page = context.new_page()
            
            # Set extra headers for authenticity
            page.set_extra_http_headers({
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
                "Accept-Language": "en-US,en;q=0.9",
                "Accept-Encoding": "gzip, deflate, br",
                "Connection": "keep-alive",
                "Upgrade-Insecure-Requests": "1"
            })
            
            # Navigate and wait for network idle (critical for complete loading)
            page.goto(url, wait_until='networkidle')
            
            # Ensure all content is loaded by scrolling
            page.evaluate('window.scrollTo(0, document.body.scrollHeight)')
            page.wait_for_timeout(1000)  # Wait for any animations
            
            # CRITICAL: Use full_page=True for complete capture
            page.screenshot(path=filepath, full_page=True)
            
            # Get file info
            file_size = os.path.getsize(filepath)
            logger.info(f"PLAYWRIGHT screenshot saved: {filepath} ({file_size:,} bytes)")
            
            browser.close()
            
            # Save to database
            try:
                screenshot = Screenshot()
                screenshot.lottery_type = lottery_type
                screenshot.url = url
                screenshot.filename = filename
                screenshot.file_path = filepath
                screenshot.file_size = file_size
                screenshot.capture_method = 'playwright_fullpage'
                screenshot.status = 'active'
                if hasattr(current_user, 'id'):
                    screenshot.created_by = current_user.id
                
                db.session.add(screenshot)
                db.session.commit()
                
                return {
                    'success': True,
                    'lottery_type': lottery_type,
                    'filename': filename,
                    'filepath': filepath,
                    'file_size': file_size,
                    'method': 'playwright_fullpage'
                }
                
            except Exception as db_error:
                logger.error(f"Database error: {db_error}")
                db.session.rollback()
                return {
                    'success': False,
                    'error': f'Database error: {str(db_error)}',
                    'lottery_type': lottery_type
                }
        
    except Exception as e:
        logger.error(f"Playwright capture error for {lottery_type}: {e}")
        return {
            'success': False,
            'error': str(e),
            'lottery_type': lottery_type
        }

def capture_all_lottery_screenshots_playwright():
    """
    Capture all 6 lottery types using Playwright method
    
    Returns:
        dict: Overall results with success/failure counts
    """
    logger.info("Starting PLAYWRIGHT capture of all lottery screenshots...")
    
    results = {
        'success': [],
        'failed': [],
        'total_success': 0,
        'total_failed': 0
    }
    
    for lottery_type, url in LOTTERY_URLS.items():
        logger.info(f"Processing {lottery_type} with Playwright...")
        
        result = capture_lottery_screenshot_playwright(lottery_type, url)
        
        if result['success']:
            results['success'].append(result)
            results['total_success'] += 1
            logger.info(f"✅ PLAYWRIGHT: {lottery_type} captured successfully")
        else:
            results['failed'].append(result)
            results['total_failed'] += 1
            logger.error(f"❌ PLAYWRIGHT: {lottery_type} failed - {result.get('error', 'Unknown error')}")
        
        # Human-like delay between captures
        if lottery_type != 'DAILY LOTTO':  # Don't delay after the last one
            delay = 3
            logger.info(f"Waiting {delay} seconds before next capture...")
            time.sleep(delay)
    
    logger.info(f"PLAYWRIGHT capture completed: {results['total_success']}/6 successful")
    return results

def test_playwright_method():
    """
    Test the Playwright method on one lottery type
    
    Returns:
        bool: True if successful, False otherwise
    """
    logger.info("Testing PLAYWRIGHT method...")
    
    result = capture_lottery_screenshot_playwright('LOTTO', LOTTERY_URLS['LOTTO'])
    
    if result['success']:
        logger.info(f"✅ PLAYWRIGHT TEST SUCCESS: {result['filename']} ({result['file_size']:,} bytes)")
        return True
    else:
        logger.error(f"❌ PLAYWRIGHT TEST FAILED: {result.get('error', 'Unknown error')}")
        return False