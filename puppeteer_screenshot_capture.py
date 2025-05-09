"""
Capture Lottery Screenshots using Pyppeteer (Python port of Puppeteer)

This script uses Pyppeteer to capture screenshots from the lottery websites.
Pyppeteer is a Python port of Puppeteer, which is a Node.js library that provides
a high-level API to control Chrome/Chromium over the DevTools Protocol.
"""

import os
import sys
import asyncio
import logging
from datetime import datetime
from pyppeteer import launch

# Set up logging
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Ensure the screenshots directory exists
SCREENSHOTS_DIR = 'screenshots'
os.makedirs(SCREENSHOTS_DIR, exist_ok=True)

# South African Lottery URLs (both history and results pages)
LOTTERY_URLS = [
    # History URLs
    {'url': 'https://www.nationallottery.co.za/lotto-history', 'type': 'lotto_history'},
    {'url': 'https://www.nationallottery.co.za/lotto-plus-1-history', 'type': 'lotto_plus_1_history'},
    {'url': 'https://www.nationallottery.co.za/lotto-plus-2-history', 'type': 'lotto_plus_2_history'},
    {'url': 'https://www.nationallottery.co.za/powerball-history', 'type': 'powerball_history'},
    {'url': 'https://www.nationallottery.co.za/powerball-plus-history', 'type': 'powerball_plus_history'},
    {'url': 'https://www.nationallottery.co.za/daily-lotto-history', 'type': 'daily_lotto_history'},
    
    # Results URLs
    {'url': 'https://www.nationallottery.co.za/results/lotto', 'type': 'lotto_results'},
    {'url': 'https://www.nationallottery.co.za/results/lotto-plus-1-results', 'type': 'lotto_plus_1_results'},
    {'url': 'https://www.nationallottery.co.za/results/lotto-plus-2-results', 'type': 'lotto_plus_2_results'},
    {'url': 'https://www.nationallottery.co.za/results/powerball', 'type': 'powerball_results'},
    {'url': 'https://www.nationallottery.co.za/results/powerball-plus', 'type': 'powerball_plus_results'},
    {'url': 'https://www.nationallottery.co.za/results/daily-lotto', 'type': 'daily_lotto_results'},
]

async def capture_screenshot(browser, url, lottery_type):
    """
    Capture a screenshot from the URL using Pyppeteer
    
    Args:
        browser: Pyppeteer browser instance
        url (str): URL to capture
        lottery_type (str): Type of lottery
        
    Returns:
        dict: Result of the capture operation
    """
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{timestamp}_{lottery_type}.png"
    filepath = os.path.join(SCREENSHOTS_DIR, filename)
    html_filename = f"{timestamp}_{lottery_type}.html"
    html_filepath = os.path.join(SCREENSHOTS_DIR, html_filename)
    
    logger.info(f"Capturing {lottery_type} from {url}")
    
    try:
        # Create a new page
        page = await browser.newPage()
        
        # Set viewport size
        await page.setViewport({'width': 1280, 'height': 1024})
        
        # Set user agent to avoid being detected as a bot
        await page.setUserAgent('Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36')
        
        # Navigate to the URL with a timeout
        await page.goto(url, {'waitUntil': 'networkidle0', 'timeout': 60000})
        
        # Wait for content to be fully loaded
        await page.waitForSelector('body', {'visible': True, 'timeout': 30000})
        
        # Wait a moment for any dynamic content
        await asyncio.sleep(2)
        
        # Take screenshot
        await page.screenshot({'path': filepath, 'fullPage': True})
        logger.info(f"✅ Screenshot saved to {filepath}")
        
        # Save HTML content
        html_content = await page.content()
        with open(html_filepath, 'w', encoding='utf-8') as f:
            f.write(html_content)
        logger.info(f"✅ HTML content saved to {html_filepath}")
        
        # Close the page
        await page.close()
        
        return {
            'status': 'success',
            'path': filepath,
            'html_path': html_filepath
        }
    except Exception as e:
        logger.error(f"❌ Error capturing {lottery_type}: {str(e)}")
        return {
            'status': 'failed',
            'message': str(e)
        }

async def capture_all_screenshots():
    """Capture all screenshots from the specified URLs using Pyppeteer"""
    logger.info("Starting to capture screenshots with Pyppeteer...")
    
    browser = None
    results = {}
    
    try:
        # Launch browser in headless mode
        browser = await launch(
            headless=True,
            args=[
                '--no-sandbox',
                '--disable-setuid-sandbox',
                '--disable-dev-shm-usage',
                '--disable-accelerated-2d-canvas',
                '--disable-gpu',
                '--window-size=1280,1024'
            ]
        )
        
        for lottery in LOTTERY_URLS:
            url = lottery['url']
            lottery_type = lottery['type']
            
            # Capture screenshot for this lottery
            result = await capture_screenshot(browser, url, lottery_type)
            results[lottery_type] = result
            
            # Add a delay between captures to be nice to the server
            await asyncio.sleep(3)
    except Exception as e:
        logger.error(f"Error in capture process: {str(e)}")
    finally:
        # Ensure browser is closed
        if browser:
            await browser.close()
    
    # Print summary
    success_count = sum(1 for result in results.values() if result.get('status') == 'success')
    total_count = len(LOTTERY_URLS)
    
    logger.info(f"\nCapture complete: {success_count}/{total_count} screenshots captured successfully.")
    
    # Log details for each capture
    for lottery_type, result in results.items():
        status = "✅" if result.get('status') == 'success' else "❌"
        message = result.get('path', '') if result.get('status') == 'success' else result.get('message', 'Unknown error')
        logger.info(f"{status} {lottery_type}: {message}")
    
    return results

def update_database(results):
    """Update database with screenshot paths"""
    try:
        from models import db, Screenshot
        from main import app
        
        with app.app_context():
            # Map of lottery types to database names
            lottery_type_map = {
                'lotto_history': 'Lotto',
                'lotto_plus_1_history': 'Lotto Plus 1',
                'lotto_plus_2_history': 'Lotto Plus 2',
                'powerball_history': 'Powerball',
                'powerball_plus_history': 'Powerball Plus',
                'daily_lotto_history': 'Daily Lotto',
                'lotto_results': 'Lotto Results',
                'lotto_plus_1_results': 'Lotto Plus 1 Results',
                'lotto_plus_2_results': 'Lotto Plus 2 Results',
                'powerball_results': 'Powerball Results',
                'powerball_plus_results': 'Powerball Plus Results',
                'daily_lotto_results': 'Daily Lotto Results',
            }
            
            updates = 0
            creates = 0
            
            for lottery_type, result in results.items():
                if result.get('status') != 'success':
                    logger.warning(f"Skipping {lottery_type} due to capture failure")
                    continue
                
                db_name = lottery_type_map.get(lottery_type)
                if not db_name:
                    logger.warning(f"No database mapping for {lottery_type}")
                    continue
                
                # Get filepath from result
                filepath = result.get('path')
                if not filepath:
                    logger.warning(f"No filepath for {lottery_type}")
                    continue
                
                # Look for exact match first
                screenshot = Screenshot.query.filter_by(lottery_type=db_name).first()
                
                if not screenshot:
                    # Try partial match
                    for s in Screenshot.query.all():
                        if db_name.lower() in s.lottery_type.lower():
                            screenshot = s
                            break
                
                if screenshot:
                    # Update existing record
                    old_path = screenshot.path
                    screenshot.path = filepath
                    screenshot.timestamp = datetime.now()
                    logger.info(f"Updated {db_name} record: {old_path} -> {filepath}")
                    updates += 1
                else:
                    # Create new record
                    url = next((lot['url'] for lot in LOTTERY_URLS if lot['type'] == lottery_type), '')
                    screenshot = Screenshot()
                    screenshot.lottery_type = db_name
                    screenshot.url = url
                    screenshot.path = filepath
                    screenshot.timestamp = datetime.now()
                    db.session.add(screenshot)
                    logger.info(f"Created new record for {db_name} with {filepath}")
                    creates += 1
            
            # Commit all changes
            db.session.commit()
            logger.info(f"Database updated successfully. {updates} records updated, {creates} records created.")
            return True
    except Exception as e:
        logger.error(f"Error updating database: {str(e)}")
        return False

if __name__ == "__main__":
    # Run the async screenshot capture
    results = asyncio.get_event_loop().run_until_complete(capture_all_screenshots())
    
    # Update database if requested
    if '--update-db' in sys.argv or '-u' in sys.argv:
        logger.info("\nUpdating database...")
        update_database(results)