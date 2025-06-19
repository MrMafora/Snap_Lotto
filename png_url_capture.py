#!/usr/bin/env python3
"""
PNG Screenshot Capture using Playwright for SA National Lottery Results Pages
Captures full-page PNG screenshots with improved reliability
"""

import os
import asyncio
import logging
from datetime import datetime
from playwright.async_api import async_playwright

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def capture_full_page_screenshot(url, lottery_type, retries=3):
    """
    Capture full-page PNG screenshot using Playwright
    
    Args:
        url: Lottery results URL
        lottery_type: Type of lottery (e.g., 'Lotto', 'Powerball')
        retries: Number of retry attempts
        
    Returns:
        Dictionary with capture result information
    """
    
    # Generate filename
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    safe_type = lottery_type.lower().replace(' ', '_').replace('+', '_plus')
    filename = f"{timestamp}_{safe_type}_fullpage.png"
    
    # Create screenshots directory
    screenshot_dir = os.path.join(os.getcwd(), 'screenshots')
    os.makedirs(screenshot_dir, exist_ok=True)
    filepath = os.path.join(screenshot_dir, filename)
    
    logger.info(f"Capturing full-page PNG for {lottery_type} from {url}")
    
    for attempt in range(retries):
        try:
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
                        '--single-process',
                        '--disable-gpu'
                    ]
                )
                
                # Create new page with mobile viewport initially
                page = await browser.new_page(
                    viewport={'width': 1920, 'height': 1080},
                    user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
                )
                
                # Set longer timeout for slow websites
                page.set_default_timeout(30000)
                
                # Navigate to URL
                logger.info(f"Loading page: {url}")
                await page.goto(url, wait_until='networkidle', timeout=30000)
                
                # Wait for content to load
                await page.wait_for_load_state('domcontentloaded')
                await asyncio.sleep(3)
                
                # Take full page screenshot
                logger.info("Taking full-page screenshot...")
                await page.screenshot(
                    path=filepath,
                    full_page=True,
                    type='png'
                )
                
                await browser.close()
                
                # Verify file was created
                if os.path.exists(filepath):
                    file_size = os.path.getsize(filepath)
                    logger.info(f"✓ Screenshot saved: {filename} ({file_size} bytes)")
                    
                    return {
                        'status': 'success',
                        'filename': filename,
                        'filepath': filepath,
                        'file_size': file_size,
                        'lottery_type': lottery_type,
                        'url': url,
                        'timestamp': timestamp
                    }
                else:
                    raise Exception("Screenshot file was not created")
                    
        except Exception as e:
            logger.warning(f"Attempt {attempt + 1}/{retries} failed for {lottery_type}: {str(e)}")
            if attempt == retries - 1:
                logger.error(f"Failed to capture {lottery_type} after {retries} attempts")
                return {
                    'status': 'failed',
                    'lottery_type': lottery_type,
                    'url': url,
                    'error': str(e),
                    'attempts': retries
                }
            await asyncio.sleep(2)  # Wait before retry

async def capture_all_results_screenshots():
    """Capture screenshots from all SA National Lottery results pages"""
    
    # Results page URLs (excluding history pages)
    results_urls = [
        {'url': 'https://www.nationallottery.co.za/results/lotto', 'lottery_type': 'Lotto'},
        {'url': 'https://www.nationallottery.co.za/results/lotto-plus-1-results', 'lottery_type': 'Lotto Plus 1'},
        {'url': 'https://www.nationallottery.co.za/results/lotto-plus-2-results', 'lottery_type': 'Lotto Plus 2'},
        {'url': 'https://www.nationallottery.co.za/results/powerball', 'lottery_type': 'Powerball'},
        {'url': 'https://www.nationallottery.co.za/results/powerball-plus', 'lottery_type': 'Powerball Plus'},
        {'url': 'https://www.nationallottery.co.za/results/daily-lotto', 'lottery_type': 'Daily Lotto'}
    ]
    
    logger.info(f"Starting full-page PNG capture for {len(results_urls)} results pages")
    
    results = []
    
    for url_config in results_urls:
        result = await capture_full_page_screenshot(
            url_config['url'], 
            url_config['lottery_type']
        )
        results.append(result)
        
        # Brief pause between captures
        await asyncio.sleep(1)
    
    # Summary
    successful = len([r for r in results if r['status'] == 'success'])
    failed = len([r for r in results if r['status'] == 'failed'])
    
    logger.info(f"PNG capture completed: {successful} successful, {failed} failed")
    
    return results

def run_png_capture():
    """Synchronous wrapper for PNG capture"""
    return asyncio.run(capture_all_results_screenshots())

if __name__ == "__main__":
    results = run_png_capture()
    
    print("\n=== PNG CAPTURE RESULTS ===")
    for result in results:
        if result['status'] == 'success':
            print(f"✓ {result['lottery_type']}: {result['filename']} ({result['file_size']} bytes)")
        else:
            print(f"✗ {result['lottery_type']}: {result['error']}")