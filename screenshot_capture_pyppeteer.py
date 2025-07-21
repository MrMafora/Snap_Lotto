#!/usr/bin/env python3
"""
Pyppeteer-based screenshot capture for South African lottery websites
Designed as a Replit-friendly alternative to Selenium and Playwright
"""

import asyncio
import logging
import os
import time
from datetime import datetime
from pyppeteer import launch
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine
import os

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Screenshot directory
SCREENSHOT_DIR = os.path.join(os.getcwd(), 'screenshots')

# South African National Lottery URLs (exact URLs from database)
LOTTERY_URLS = {
    'LOTTO': 'https://www.nationallottery.co.za/results/lotto',
    'LOTTO PLUS 1': 'https://www.nationallottery.co.za/results/lotto-plus-1-results',
    'LOTTO PLUS 2': 'https://www.nationallottery.co.za/results/lotto-plus-2-results',
    'POWERBALL': 'https://www.nationallottery.co.za/results/powerball',
    'POWERBALL PLUS': 'https://www.nationallottery.co.za/results/powerball-plus',
    'DAILY LOTTO': 'https://www.nationallottery.co.za/results/daily-lotto'
}

async def capture_single_lottery_screenshot_pyppeteer(lottery_type, url, output_dir=SCREENSHOT_DIR):
    """
    Capture a single lottery screenshot using Pyppeteer
    
    Args:
        lottery_type (str): Type of lottery
        url (str): URL to capture
        output_dir (str): Directory to save screenshots
    
    Returns:
        dict: Result with success status and details
    """
    # Ensure output directory exists
    os.makedirs(output_dir, exist_ok=True)
    
    # Generate unique filename
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S') 
    unique_id = int(time.time() * 1000000) % 1000000
    filename = f"{timestamp}_{lottery_type.lower().replace(' ', '_')}_{unique_id}.png"
    filepath = os.path.join(output_dir, filename)
    
    try:
        logger.info(f"Starting PYPPETEER capture: {lottery_type} from {url}")
        
        # Launch browser with Replit-friendly settings
        browser = await launch(
            headless=True,
            args=[
                '--no-sandbox',
                '--disable-setuid-sandbox',
                '--disable-dev-shm-usage',
                '--disable-blink-features=AutomationControlled',
                '--disable-web-security',
                '--allow-running-insecure-content',
                '--disable-features=VizDisplayCompositor',
                '--disable-extensions',
                '--remote-debugging-port=9222'
            ],
            executablePath=None,  # Let pyppeteer handle browser location
            handleSIGINT=False,
            handleSIGTERM=False,
            handleSIGHUP=False,
            autoClose=True
        )
        
        # Create page with optimal viewport
        page = await browser.newPage()
        await page.setViewport({'width': 1920, 'height': 1080})
        
        # Set realistic user agent and headers
        await page.setUserAgent('Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
        await page.setExtraHTTPHeaders({
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Cache-Control': 'max-age=0'
        })
        
        # Navigate with network idle wait
        logger.info(f"Navigating to {url}...")
        await page.goto(url, {'waitUntil': 'networkidle2', 'timeout': 30000})
        
        # Scroll to ensure complete content loads
        await page.evaluate('window.scrollTo(0, document.body.scrollHeight)')
        await asyncio.sleep(2)  # Allow dynamic content to load
        
        # Take full page screenshot
        logger.info("Taking full page screenshot...")
        await page.screenshot({'path': filepath, 'fullPage': True})
        
        # Verify file creation
        if not os.path.exists(filepath):
            raise Exception(f"Screenshot file not created: {filepath}")
            
        file_size = os.path.getsize(filepath)
        logger.info(f"✓ PYPPETEER SUCCESS: {filepath} ({file_size:,} bytes)")
        
        await browser.close()
        
        # Log successful capture
        logger.info(f"Screenshot captured successfully for {lottery_type}")
        
        return {
            'success': True,
            'lottery_type': lottery_type,
            'filename': filename,
            'filepath': filepath,
            'file_size': file_size,
            'url': url
        }
        
    except Exception as e:
        logger.error(f"Pyppeteer capture error for {lottery_type}: {e}")
        return {
            'success': False,
            'error': str(e),
            'lottery_type': lottery_type
        }

def capture_all_lottery_screenshots_pyppeteer():
    """
    Capture all 6 lottery types using Pyppeteer
    
    Returns:
        dict: Overall results with success/failure counts
    """
    logger.info("Starting PYPPETEER capture of all lottery screenshots...")
    
    results = {
        'success': [],
        'failed': [],
        'total_success': 0,
        'total_failed': 0,
        'total_processed': 6
    }
    
    async def capture_all():
        for lottery_type, url in LOTTERY_URLS.items():
            logger.info(f"Processing {lottery_type} with Pyppeteer...")
            
            result = await capture_single_lottery_screenshot_pyppeteer(lottery_type, url)
            
            if result['success']:
                results['success'].append(result)
                results['total_success'] += 1
                logger.info(f"✅ PYPPETEER: {lottery_type} captured successfully")
            else:
                results['failed'].append(result)
                results['total_failed'] += 1
                logger.error(f"❌ PYPPETEER: {lottery_type} failed - {result.get('error', 'Unknown error')}")
            
            # Human-like delay between captures
            if lottery_type != 'DAILY LOTTO':  # Don't delay after the last one
                delay = 3
                logger.info(f"Waiting {delay} seconds before next capture...")
                await asyncio.sleep(delay)
    
    # Run the async capture process
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        loop.run_until_complete(capture_all())
    finally:
        loop.close()
    
    logger.info(f"PYPPETEER capture completed: {results['total_success']}/6 successful")
    return results

def test_pyppeteer_method():
    """
    Test the Pyppeteer method on one lottery type
    
    Returns:
        bool: True if successful, False otherwise
    """
    logger.info("Testing PYPPETEER method...")
    
    async def test_single():
        result = await capture_single_lottery_screenshot_pyppeteer('LOTTO', LOTTERY_URLS['LOTTO'])
        return result
    
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        result = loop.run_until_complete(test_single())
    finally:
        loop.close()
    
    if result['success']:
        logger.info(f"✅ PYPPETEER TEST SUCCESS: {result['filename']} ({result['file_size']:,} bytes)")
        return True
    else:
        logger.error(f"❌ PYPPETEER TEST FAILED: {result.get('error', 'Unknown error')}")
        return False

def cleanup_old_screenshots(days_old=7):
    """Clean up old screenshots - placeholder for compatibility"""
    logger.info(f"Cleanup requested for files older than {days_old} days")
    return {
        'success': True,
        'deleted_files': 0,
        'deleted_records': 0,
        'message': 'Cleanup functionality placeholder'
    }

if __name__ == '__main__':
    print("Testing Pyppeteer screenshot capture...")
    success = test_pyppeteer_method()
    if success:
        print("✅ Pyppeteer working! Running full capture...")
        results = capture_all_lottery_screenshots_pyppeteer()
        print(f"Final Results: {results['total_success']}/6 lottery types captured")