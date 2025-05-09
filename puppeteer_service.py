"""
Puppeteer Service for Lottery Screenshots

This module provides a service to capture screenshots from lottery websites using Pyppeteer.
It can be imported and used as part of the main application.
"""

import os
import asyncio
import logging
import traceback
from datetime import datetime
from pyppeteer import launch

# Set up logging
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Ensure the screenshots directory exists
SCREENSHOTS_DIR = 'screenshots'
os.makedirs(SCREENSHOTS_DIR, exist_ok=True)

# Create a specific subfolder for HTML content if needed
HTML_DIR = os.path.join(SCREENSHOTS_DIR, 'html')
os.makedirs(HTML_DIR, exist_ok=True)

class PuppeteerService:
    """Service for capturing screenshots using Pyppeteer"""
    
    @staticmethod
    async def capture_screenshot(url, filename_prefix, fullpage=True):
        """
        Capture a screenshot from a URL
        
        Args:
            url (str): URL to capture
            filename_prefix (str): Prefix for the filename (e.g., lottery type)
            fullpage (bool): Whether to capture the full page
            
        Returns:
            tuple: (success, filepath, html_filepath, error_message)
        """
        browser = None
        
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            
            # Define PNG file path (primary screenshot)
            filename = f"{timestamp}_{filename_prefix}.png"
            filepath = os.path.join(SCREENSHOTS_DIR, filename)
            
            # Define HTML file path (stored in HTML_DIR subfolder)
            html_filename = f"{timestamp}_{filename_prefix}.html"
            html_filepath = os.path.join(HTML_DIR, html_filename)
            
            logger.info(f"Capturing screenshot from {url}")
            
            # Launch browser with appropriate settings for screenshot capture
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
            
            # Open new page
            page = await browser.newPage()
            
            # Set viewport size for consistent screenshots
            await page.setViewport({'width': 1280, 'height': 1024})
            
            # Set user agent to avoid detection
            await page.setUserAgent('Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36')
            
            # Navigate to the URL with appropriate wait conditions
            response = await page.goto(url, {'waitUntil': 'networkidle0', 'timeout': 60000})
            
            if not response.ok:
                logger.warning(f"Page response not OK: {response.status} for {url}")
            
            # Wait for content to be fully loaded
            await page.waitForSelector('body', {'visible': True, 'timeout': 30000})
            
            # Wait a moment for any dynamic content to render
            await asyncio.sleep(2)
            
            # Take screenshot - THIS IS THE CRITICAL PART
            # Make sure we're capturing with proper settings for a full page screenshot
            screenshot_options = {
                'path': filepath,
                'fullPage': fullpage,
                'type': 'png',
                'omitBackground': False,
                'encoding': 'binary'
            }
            await page.screenshot(screenshot_options)
            
            # Verify the file was created successfully
            if os.path.exists(filepath) and os.path.getsize(filepath) > 0:
                logger.info(f"✅ Screenshot successfully saved to {filepath} ({os.path.getsize(filepath)} bytes)")
            else:
                logger.error(f"❌ Screenshot file not created or empty: {filepath}")
                # If screenshot fails, try one more time with different settings
                screenshot_options = {
                    'path': filepath,
                    'fullPage': False,  # Try without fullPage
                    'type': 'png'
                }
                await page.screenshot(screenshot_options)
                if os.path.exists(filepath) and os.path.getsize(filepath) > 0:
                    logger.info(f"✅ Retry successful: Screenshot saved to {filepath} ({os.path.getsize(filepath)} bytes)")
            
            # Save HTML content for backup/debugging
            html_content = await page.content()
            with open(html_filepath, 'w', encoding='utf-8') as f:
                f.write(html_content)
            logger.info(f"HTML content saved to {html_filepath}")
            
            return True, filepath, html_filepath, None
        except Exception as e:
            error_message = f"Error capturing screenshot: {str(e)}"
            logger.error(error_message)
            traceback.print_exc()
            return False, None, None, error_message
        finally:
            # Ensure browser is closed
            if browser:
                await browser.close()
    
    @staticmethod
    async def capture_multiple_screenshots(urls_with_types):
        """
        Capture multiple screenshots
        
        Args:
            urls_with_types (list): List of dictionaries with 'url' and 'type' keys
            
        Returns:
            dict: Results for each lottery type
        """
        browser = None
        results = {}
        
        try:
            # Launch browser with optimal settings for screenshots
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
            
            for item in urls_with_types:
                url = item['url']
                lottery_type = item['type']
                
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                
                # Define PNG file path (this is the primary screenshot file)
                filename = f"{timestamp}_{lottery_type}.png"
                filepath = os.path.join(SCREENSHOTS_DIR, filename)
                
                # Define HTML file path (stored in HTML_DIR subfolder)
                html_filename = f"{timestamp}_{lottery_type}.html"
                html_filepath = os.path.join(HTML_DIR, html_filename)
                
                logger.info(f"Capturing {lottery_type} from {url}")
                
                try:
                    # Create a new page
                    page = await browser.newPage()
                    
                    # Set viewport size for consistent screenshots
                    await page.setViewport({'width': 1280, 'height': 1024})
                    
                    # Set user agent to avoid detection
                    await page.setUserAgent('Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36')
                    
                    # Navigate to the URL with appropriate wait conditions
                    response = await page.goto(url, {'waitUntil': 'networkidle0', 'timeout': 60000})
                    
                    if not response.ok:
                        logger.warning(f"Page response not OK: {response.status} for {url}")
                    
                    # Wait for content to be fully loaded
                    await page.waitForSelector('body', {'visible': True, 'timeout': 30000})
                    
                    # Wait a moment for any dynamic content to fully render
                    await asyncio.sleep(2)
                    
                    # Take screenshot - THIS IS THE CRITICAL PART
                    # Make sure we're capturing with proper settings for a full page screenshot
                    screenshot_options = {
                        'path': filepath,
                        'fullPage': True,
                        'type': 'png',
                        'omitBackground': False,
                        'encoding': 'binary'
                    }
                    await page.screenshot(screenshot_options)
                    
                    # Verify the file was created successfully
                    if os.path.exists(filepath) and os.path.getsize(filepath) > 0:
                        logger.info(f"✅ Screenshot successfully saved to {filepath} ({os.path.getsize(filepath)} bytes)")
                    else:
                        logger.error(f"❌ Screenshot file not created or empty: {filepath}")
                        # If screenshot fails, try one more time with different settings
                        screenshot_options = {
                            'path': filepath,
                            'fullPage': False,  # Try without fullPage
                            'type': 'png'
                        }
                        await page.screenshot(screenshot_options)
                        if os.path.exists(filepath) and os.path.getsize(filepath) > 0:
                            logger.info(f"✅ Retry successful: Screenshot saved to {filepath} ({os.path.getsize(filepath)} bytes)")
                    
                    # Save HTML content for backup/debugging
                    html_content = await page.content()
                    with open(html_filepath, 'w', encoding='utf-8') as f:
                        f.write(html_content)
                    logger.info(f"✅ HTML content saved to {html_filepath}")
                    
                    # Close the page
                    await page.close()
                    
                    results[lottery_type] = {
                        'status': 'success',
                        'path': filepath,
                        'html_path': html_filepath,
                        'url': url
                    }
                except Exception as e:
                    logger.error(f"❌ Error capturing {lottery_type}: {str(e)}")
                    traceback.print_exc()
                    results[lottery_type] = {
                        'status': 'failed',
                        'message': str(e),
                        'url': url
                    }
                
                # Add a delay between captures to avoid rate limiting
                await asyncio.sleep(3)
        except Exception as e:
            logger.error(f"Error in capture process: {str(e)}")
            traceback.print_exc()
        finally:
            # Ensure browser is closed
            if browser:
                await browser.close()
        
        return results

def capture_screenshot(url, filename_prefix, fullpage=True):
    """
    Synchronous wrapper for capturing a screenshot
    
    Args:
        url (str): URL to capture
        filename_prefix (str): Prefix for the filename
        fullpage (bool): Whether to capture the full page
        
    Returns:
        tuple: (success, filepath, html_filepath, error_message)
    """
    return asyncio.get_event_loop().run_until_complete(
        PuppeteerService.capture_screenshot(url, filename_prefix, fullpage)
    )

def capture_single_screenshot(lottery_type, url):
    """
    Synchronous wrapper for capturing a single screenshot
    with lottery type and URL
    
    Args:
        lottery_type (str): Type of lottery (used for filename)
        url (str): URL to capture
        
    Returns:
        dict: Result dictionary with status, path, etc.
    """
    try:
        # Create a safe filename from lottery type
        safe_filename = lottery_type.replace(' ', '_').lower()
        
        # Capture the screenshot
        success, filepath, html_filepath, error_message = capture_screenshot(url, safe_filename)
        
        if success and filepath:
            return {
                'status': 'success',
                'path': filepath,
                'html_path': html_filepath,
                'url': url
            }
        else:
            return {
                'status': 'failed',
                'error': error_message or 'Unknown error',
                'url': url
            }
    except Exception as e:
        logger.error(f"Error in capture_single_screenshot for {lottery_type}: {str(e)}")
        return {
            'status': 'failed',
            'error': str(e),
            'url': url
        }

def capture_multiple_screenshots(urls_with_types):
    """
    Synchronous wrapper for capturing multiple screenshots
    
    Args:
        urls_with_types (list): List of dictionaries with 'url' and 'type' keys
        
    Returns:
        dict: Results for each lottery type
    """
    return asyncio.get_event_loop().run_until_complete(
        PuppeteerService.capture_multiple_screenshots(urls_with_types)
    )

def update_screenshot_database(results, screenshot_model, db, map_type_to_db=None):
    """
    Update database with screenshot paths
    
    Args:
        results (dict): Results from capture_multiple_screenshots
        screenshot_model: Database model for screenshots
        db: SQLAlchemy database instance
        map_type_to_db (dict, optional): Mapping from lottery types to database names
        
    Returns:
        tuple: (success, updates, creates)
    """
    if map_type_to_db is None:
        map_type_to_db = {
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
    
    try:
        updates = 0
        creates = 0
        
        for lottery_type, result in results.items():
            if result.get('status') != 'success':
                logger.warning(f"Skipping {lottery_type} due to capture failure")
                continue
            
            db_name = map_type_to_db.get(lottery_type)
            if not db_name:
                logger.warning(f"No database mapping for {lottery_type}")
                continue
            
            # Get filepath from result
            filepath = result.get('path')
            if not filepath:
                logger.warning(f"No filepath for {lottery_type}")
                continue
            
            # Look for exact match first
            screenshot = screenshot_model.query.filter_by(lottery_type=db_name).first()
            
            if not screenshot:
                # Try partial match
                for s in screenshot_model.query.all():
                    if db_name.lower() in s.lottery_type.lower():
                        screenshot = s
                        break
            
            # Get HTML path from result if available
            html_filepath = result.get('html_path')
            
            if screenshot:
                # Update existing record
                old_path = screenshot.path
                screenshot.path = filepath
                
                # Update HTML path if available
                if html_filepath:
                    screenshot.html_path = html_filepath
                    logger.info(f"Updated HTML path: {html_filepath}")
                
                screenshot.timestamp = datetime.now()
                logger.info(f"Updated {db_name} record: {old_path} -> {filepath}")
                updates += 1
            else:
                # Create new record
                url = result.get('url', '')
                
                screenshot = screenshot_model(
                    lottery_type=db_name,
                    url=url,
                    path=filepath,
                    html_path=html_filepath,  # Set HTML path when creating new record
                    timestamp=datetime.now()
                )
                db.session.add(screenshot)
                logger.info(f"Created new record for {db_name} with {filepath}")
                creates += 1
        
        # Commit all changes
        db.session.commit()
        logger.info(f"Database updated successfully. {updates} records updated, {creates} records created.")
        return True, updates, creates
    except Exception as e:
        logger.error(f"Error updating database: {str(e)}")
        return False, 0, 0

# Default lottery URLs for convenience (dictionary format for easier access)
LOTTERY_URLS = {
    # History URLs
    'Lotto': 'https://www.nationallottery.co.za/lotto-history',
    'Lotto Plus 1': 'https://www.nationallottery.co.za/lotto-plus-1-history',
    'Lotto Plus 2': 'https://www.nationallottery.co.za/lotto-plus-2-history',
    'Powerball': 'https://www.nationallottery.co.za/powerball-history',
    'Powerball Plus': 'https://www.nationallottery.co.za/powerball-plus-history',
    'Daily Lotto': 'https://www.nationallottery.co.za/daily-lotto-history',
    
    # Results URLs
    'Lotto Results': 'https://www.nationallottery.co.za/results/lotto',
    'Lotto Plus 1 Results': 'https://www.nationallottery.co.za/results/lotto-plus-1-results',
    'Lotto Plus 2 Results': 'https://www.nationallottery.co.za/results/lotto-plus-2-results',
    'Powerball Results': 'https://www.nationallottery.co.za/results/powerball',
    'Powerball Plus Results': 'https://www.nationallottery.co.za/results/powerball-plus',
    'Daily Lotto Results': 'https://www.nationallottery.co.za/results/daily-lotto',
}

# Legacy format for backward compatibility
LOTTERY_URLS_LIST = [
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

# Simple test function
if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "single":
        # Test single screenshot capture
        url = 'https://www.nationallottery.co.za/lotto-history'
        success, filepath, html_filepath, error = capture_screenshot(url, 'test_lotto')
        if success:
            print(f"Screenshot captured successfully: {filepath}")
            print(f"HTML content saved to: {html_filepath}")
        else:
            print(f"Error: {error}")
    elif len(sys.argv) > 1 and sys.argv[1] == "single_new":
        # Test single screenshot capture using new function
        lottery_type = "Lotto"
        if lottery_type in LOTTERY_URLS:
            url = LOTTERY_URLS[lottery_type]
            result = capture_single_screenshot(lottery_type, url)
            status = "Success" if result.get('status') == 'success' else "Failed"
            print(f"{lottery_type}: {status}")
            if result.get('status') == 'success':
                print(f"  Screenshot: {result.get('path')}")
                print(f"  HTML path: {result.get('html_path')}")
            else:
                print(f"  Error: {result.get('error')}")
        else:
            print(f"Error: Lottery type '{lottery_type}' not found in LOTTERY_URLS")
    else:
        # Test multiple screenshot capture (using legacy format for compatibility)
        # Convert first two items from the dictionary to list format
        test_urls = []
        for i, (lottery_type, url) in enumerate(LOTTERY_URLS.items()):
            if i < 2:  # Just test first two
                test_urls.append({'type': lottery_type, 'url': url})
        
        results = capture_multiple_screenshots(test_urls)  # Just capture first two URLs for testing
        
        # Print results
        for lottery_type, result in results.items():
            status = "Success" if result.get('status') == 'success' else "Failed"
            print(f"{lottery_type}: {status}")
            if result.get('status') == 'success':
                print(f"  Screenshot: {result.get('path')}")
                print(f"  HTML content: {result.get('html_path')}")
            else:
                print(f"  Error: {result.get('message')}")
                
        print("\nTesting single_screenshot function:")
        # Test the single_screenshot function with the first URL
        first_type = list(LOTTERY_URLS.keys())[0]
        first_url = LOTTERY_URLS[first_type]
        result = capture_single_screenshot(first_type, first_url)
        status = "Success" if result.get('status') == 'success' else "Failed"
        print(f"{first_type}: {status}")
        if result.get('status') == 'success':
            print(f"  Screenshot: {result.get('path')}")
            print(f"  HTML path: {result.get('html_path')}")
        else:
            print(f"  Error: {result.get('error')}")