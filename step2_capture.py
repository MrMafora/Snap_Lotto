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
    """Capture actual screenshot image from lottery website using Playwright"""
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
            # Launch browser with optimized settings
            browser = await p.chromium.launch(
                headless=True,
                args=[
                    '--no-sandbox',
                    '--disable-setuid-sandbox',
                    '--disable-dev-shm-usage',
                    '--disable-accelerated-2d-canvas',
                    '--no-first-run',
                    '--no-zygote',
                    '--disable-gpu'
                ]
            )
            
            # Create browser context with mobile viewport
            context = await browser.new_context(
                viewport={'width': 1200, 'height': 800},
                user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
            )
            
            # Create new page
            page = await context.new_page()
            
            try:
                # Navigate to lottery page with timeout
                await page.goto(url, wait_until='networkidle', timeout=60000)
                
                # Wait for page to fully load
                await page.wait_for_timeout(3000)
                
                # Take full page screenshot
                await page.screenshot(
                    path=filepath,
                    full_page=True,
                    quality=85
                )
                
                logger.info(f"Screenshot captured and saved: {filename}")
                
                # Close browser resources
                await context.close()
                await browser.close()
                
                return filepath
                
            except Exception as page_error:
                logger.error(f"Page error for {lottery_type}: {str(page_error)}")
                await context.close()
                await browser.close()
                return None
                
    except Exception as e:
        logger.error(f"Failed to capture screenshot for {lottery_type}: {str(e)}")
        return None

async def capture_all_lottery_screenshots():
    """Capture screenshots from all lottery result URLs"""
    try:
        logger.info("=== STEP 2: SCREENSHOT CAPTURE STARTED ===")
        
        results = []
        
        # Capture screenshots from all result URLs
        for lottery_config in Config.RESULTS_URLS:
            url = lottery_config['url']
            lottery_type = lottery_config['lottery_type']
            
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
            
            # Small delay between captures
            await asyncio.sleep(2)
        
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