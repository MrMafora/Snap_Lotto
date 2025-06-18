#!/usr/bin/env python3
"""
Simple Screenshot Capture for South African National Lottery URLs
Uses Playwright with optimized settings for Replit environment
"""

import os
import asyncio
import logging
from datetime import datetime
from playwright.async_api import async_playwright
from config import Config

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def capture_single_lottery_url(url, lottery_type):
    """Capture screenshot from a single lottery URL with human-like behavior"""
    try:
        logger.info(f"Capturing {lottery_type} from {url}")
        
        # Generate filename
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        safe_type = lottery_type.lower().replace(' ', '_').replace('+', '_plus_')
        filename = f"{timestamp}_{safe_type}.png"
        
        # Ensure screenshots directory exists
        os.makedirs('screenshots', exist_ok=True)
        filepath = os.path.join('screenshots', filename)
        
        async with async_playwright() as p:
            # Launch browser with explicit path and Replit-optimized settings
            browser = await p.chromium.launch(
                headless=True,
                executable_path="/home/runner/workspace/.cache/ms-playwright/chromium-1161/chrome-linux/chrome",
                args=[
                    '--no-sandbox',
                    '--disable-setuid-sandbox', 
                    '--disable-dev-shm-usage',
                    '--disable-web-security',
                    '--disable-features=VizDisplayCompositor',
                    '--remote-debugging-port=0'
                ]
            )
            
            # Create context with realistic settings
            context = await browser.new_context(
                viewport={'width': 1366, 'height': 768},
                user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                locale='en-ZA'
            )
            
            page = await context.new_page()
            
            # Navigate to lottery results page
            logger.info(f"Navigating to {url}")
            await page.goto(url, wait_until='networkidle', timeout=30000)
            
            # Human-like behavior: wait and scroll
            await page.wait_for_timeout(2000)
            await page.evaluate('window.scrollTo(0, 200)')
            await page.wait_for_timeout(1000)
            await page.evaluate('window.scrollTo(0, 0)')
            await page.wait_for_timeout(1000)
            
            # Take screenshot
            await page.screenshot(path=filepath, full_page=True)
            
            await context.close()
            await browser.close()
            
            # Verify file creation
            if os.path.exists(filepath):
                file_size = os.path.getsize(filepath)
                logger.info(f"✓ Screenshot saved: {filename} ({file_size} bytes)")
                return filepath
            else:
                logger.error(f"✗ Screenshot not created for {lottery_type}")
                return None
                
    except Exception as e:
        logger.error(f"Error capturing {lottery_type}: {str(e)}")
        return None

async def capture_all_lottery_urls():
    """Capture screenshots from all South African National Lottery URLs"""
    logger.info("=== STARTING LOTTERY SCREENSHOT CAPTURE ===")
    
    results = []
    
    # Process each lottery URL with human-like delays
    for i, lottery_config in enumerate(Config.RESULTS_URLS):
        url = lottery_config['url']
        lottery_type = lottery_config['lottery_type']
        
        # Add delay between requests (human-like behavior)
        if i > 0:
            delay = 2 + i  # Increasing delay between requests
            logger.info(f"Waiting {delay} seconds before next capture...")
            await asyncio.sleep(delay)
        
        # Capture screenshot
        filepath = await capture_single_lottery_url(url, lottery_type)
        
        results.append({
            'lottery_type': lottery_type,
            'url': url,
            'filepath': filepath,
            'status': 'success' if filepath else 'failed'
        })
    
    # Log summary
    successful = len([r for r in results if r['status'] == 'success'])
    total = len(results)
    logger.info(f"=== CAPTURE COMPLETE: {successful}/{total} screenshots captured ===")
    
    return results

def run_capture():
    """Run the async capture function"""
    try:
        return asyncio.run(capture_all_lottery_urls())
    except Exception as e:
        logger.error(f"Error running capture: {str(e)}")
        return []

if __name__ == "__main__":
    # Run capture and display results
    results = run_capture()
    
    print("\n=== SCREENSHOT CAPTURE RESULTS ===")
    for result in results:
        status = "✓" if result['status'] == 'success' else "✗"
        print(f"{status} {result['lottery_type']}: {result['status']}")
        if result['filepath']:
            print(f"  File: {os.path.basename(result['filepath'])}")
    
    successful = len([r for r in results if r['status'] == 'success'])
    total = len(results)
    print(f"\nTotal: {successful}/{total} screenshots captured successfully")