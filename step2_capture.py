#!/usr/bin/env python3
"""
Step 2: Screenshot Capture Module for Daily Automation
Captures actual screenshot images from official South African lottery websites using Playwright
"""

import os
import time
import logging
import asyncio
from datetime import datetime
from playwright.async_api import async_playwright
from config import Config

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def capture_lottery_screenshot(url, lottery_type):
    """Capture actual screenshot image from lottery website using Playwright with human-like behavior"""
    try:
        logger.info(f"Capturing screenshot of {lottery_type} from {url}")
        
        # Generate filename for screenshot
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        safe_lottery_type = lottery_type.lower().replace(' ', '_').replace('+', '_plus_')
        filename = f"{timestamp}_{safe_lottery_type}_screenshot.png"
        
        # Ensure screenshots directory exists
        screenshot_dir = os.path.join(os.getcwd(), 'screenshots')
        os.makedirs(screenshot_dir, exist_ok=True)
        filepath = os.path.join(screenshot_dir, filename)
        
        async with async_playwright() as p:
            # Launch browser with human-like settings
            browser = await p.chromium.launch(
                headless=True,
                args=[
                    '--no-sandbox',
                    '--disable-setuid-sandbox',
                    '--disable-dev-shm-usage',
                    '--disable-blink-features=AutomationControlled',
                    '--disable-extensions',
                    '--no-first-run',
                    '--disable-default-apps',
                    '--disable-background-timer-throttling',
                    '--disable-backgrounding-occluded-windows',
                    '--disable-renderer-backgrounding'
                ]
            )
            
            # Create browser context with realistic settings
            context = await browser.new_context(
                viewport={'width': 1920, 'height': 1080},
                user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                locale='en-ZA',
                timezone_id='Africa/Johannesburg',
                extra_http_headers={
                    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
                    'Accept-Language': 'en-ZA,en;q=0.9,en-US;q=0.8',
                    'Accept-Encoding': 'gzip, deflate, br',
                    'Cache-Control': 'no-cache',
                    'Sec-Fetch-Mode': 'navigate',
                    'Sec-Fetch-Site': 'none',
                    'Sec-Fetch-User': '?1',
                    'Upgrade-Insecure-Requests': '1'
                }
            )
            
            # Create new page
            page = await context.new_page()
            
            # Set additional human-like behavior
            await page.add_init_script("""
                // Remove webdriver property
                Object.defineProperty(navigator, 'webdriver', {
                    get: () => undefined,
                });
                
                // Mock plugins
                Object.defineProperty(navigator, 'plugins', {
                    get: () => [1, 2, 3, 4, 5],
                });
                
                // Mock languages
                Object.defineProperty(navigator, 'languages', {
                    get: () => ['en-ZA', 'en'],
                });
            """)
            
            try:
                # Navigate to lottery page with human-like timing
                logger.info(f"Navigating to {url}")
                await page.goto(url, wait_until='networkidle', timeout=60000)
                
                # Wait for page to stabilize (human-like behavior)
                await page.wait_for_timeout(2000)
                
                # Try to wait for lottery results content to load
                try:
                    # Look for common lottery result elements
                    await page.wait_for_selector('body', timeout=10000)
                    
                    # Additional wait for dynamic content
                    await page.wait_for_timeout(3000)
                    
                    # Scroll down slightly to trigger any lazy loading
                    await page.evaluate('window.scrollTo(0, 300)')
                    await page.wait_for_timeout(1000)
                    
                    # Scroll back to top for clean screenshot
                    await page.evaluate('window.scrollTo(0, 0)')
                    await page.wait_for_timeout(1000)
                    
                except Exception as wait_error:
                    logger.warning(f"Content wait timeout for {lottery_type}: {str(wait_error)}")
                
                # Take full page screenshot
                logger.info(f"Taking screenshot for {lottery_type}")
                await page.screenshot(
                    path=filepath,
                    full_page=True,
                    quality=90
                )
                
                # Verify file was created
                if os.path.exists(filepath):
                    file_size = os.path.getsize(filepath)
                    logger.info(f"Screenshot captured and saved: {filename} ({file_size} bytes)")
                    
                    # Close browser resources
                    await context.close()
                    await browser.close()
                    
                    return filepath
                else:
                    logger.error(f"Screenshot file was not created for {lottery_type}")
                    await context.close()
                    await browser.close()
                    return None
                
            except Exception as page_error:
                logger.error(f"Page error for {lottery_type}: {str(page_error)}")
                await context.close()
                await browser.close()
                return None
                
    except Exception as e:
        logger.error(f"Failed to capture screenshot for {lottery_type}: {str(e)}")
        return None

async def capture_all_lottery_screenshots():
    """Capture screenshots from all lottery result URLs with human-like behavior"""
    try:
        logger.info("=== STEP 2: SCREENSHOT CAPTURE STARTED ===")
        
        results = []
        
        # Capture screenshots from all result URLs with delays between requests
        for i, lottery_config in enumerate(Config.RESULTS_URLS):
            url = lottery_config['url']
            lottery_type = lottery_config['lottery_type']
            
            # Human-like delay between requests (2-5 seconds)
            if i > 0:
                delay = 3 + (i * 1)  # Increasing delay
                logger.info(f"Waiting {delay} seconds before next capture...")
                await asyncio.sleep(delay)
            
            # Capture screenshot
            filepath = await capture_lottery_screenshot(url, lottery_type)
            
            if filepath:
                results.append({
                    'lottery_type': lottery_type,
                    'url': url,
                    'filepath': filepath,
                    'status': 'success'
                })
            else:
                results.append({
                    'lottery_type': lottery_type,
                    'url': url,
                    'filepath': None,
                    'status': 'failed'
                })
        
        # Log summary
        successful_captures = len([r for r in results if r['status'] == 'success'])
        total_captures = len(results)
        
        logger.info(f"=== STEP 2: SCREENSHOT CAPTURE COMPLETED ===")
        logger.info(f"Successfully captured {successful_captures}/{total_captures} screenshots")
        
        return results
        
    except Exception as e:
        logger.error(f"Failed to capture lottery screenshots: {str(e)}")
        return []

def run_capture():
    """Synchronous wrapper to run the async capture function"""
    try:
        return asyncio.run(capture_all_lottery_screenshots())
    except Exception as e:
        logger.error(f"Error running screenshot capture: {str(e)}")
        return []

if __name__ == "__main__":
    # Run screenshot capture when executed directly
    results = run_capture()
    
    # Print results summary
    print("\n=== SCREENSHOT CAPTURE RESULTS ===")
    for result in results:
        status_symbol = "✓" if result['status'] == 'success' else "✗"
        print(f"{status_symbol} {result['lottery_type']}: {result['status']}")
        if result['filepath']:
            print(f"  File: {os.path.basename(result['filepath'])}")
    
    successful = len([r for r in results if r['status'] == 'success'])
    total = len(results)
    print(f"\nTotal: {successful}/{total} screenshots captured successfully")