#!/usr/bin/env python3
"""
Robust Screenshot Capture System with Enhanced Error Handling
Designed to handle network issues and provide detailed diagnostics
"""

import logging
import sys
import os
import time
import glob
import asyncio
from datetime import datetime
from playwright.async_api import async_playwright

# Add current directory to path
sys.path.append('.')

def setup_logging():
    """Configure logging for screenshot capture"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout)  # Only stream handler for Cloud Run
        ]
    )
    return logging.getLogger(__name__)

def test_network_connectivity(url, logger):
    """Test if we can reach the lottery website using requests"""
    try:
        import requests
        response = requests.head(url, timeout=10, allow_redirects=True)
        logger.info(f"Network test: {url} returned status {response.status_code}")
        return response.status_code == 200
    except Exception as e:
        logger.error(f"Network test failed for {url}: {e}")
        return False

async def capture_with_retry(page, url, lottery_type, filepath, logger, max_retries=3):
    """Capture screenshot with robust retry logic"""
    
    for attempt in range(max_retries):
        try:
            logger.info(f"Attempt {attempt + 1}/{max_retries}: Navigating to {url}")
            
            # Navigate with progressive timeout increases
            timeout = 20000 + (attempt * 10000)  # 20s, 30s, 40s
            await page.goto(url, wait_until='domcontentloaded', timeout=timeout)
            
            # Wait for content to load
            await page.wait_for_timeout(2000 + (attempt * 1000))
            
            # Check if page loaded properly
            title = await page.title()
            logger.info(f"Page loaded: {title[:50]}...")
            
            # Take screenshot
            await page.screenshot(path=filepath, full_page=True)
            
            # Verify file was created and has reasonable size
            if os.path.exists(filepath):
                file_size = os.path.getsize(filepath)
                if file_size > 10000:  # At least 10KB
                    logger.info(f"✅ Successfully captured {lottery_type}: {os.path.basename(filepath)} ({file_size:,} bytes)")
                    return True
                else:
                    logger.warning(f"Screenshot too small ({file_size} bytes), retrying...")
                    os.remove(filepath)
            
        except Exception as e:
            logger.error(f"Attempt {attempt + 1} failed for {lottery_type}: {str(e)}")
            if attempt < max_retries - 1:
                wait_time = (attempt + 1) * 2  # Progressive backoff: 2s, 4s, 6s
                logger.info(f"Waiting {wait_time}s before retry...")
                await asyncio.sleep(wait_time)
            
            # Clean up failed file
            if os.path.exists(filepath):
                os.remove(filepath)
    
    logger.error(f"❌ Failed to capture {lottery_type} after {max_retries} attempts")
    return False

async def robust_screenshot_capture():
    """Main screenshot capture function with enhanced error handling"""
    
    logger = setup_logging()
    logger.info("=== STARTING ROBUST SCREENSHOT CAPTURE ===")
    
    # Lottery URLs
    lottery_urls = {
        'lotto': 'https://www.nationallottery.co.za/results/lotto',
        'lotto_plus_1': 'https://www.nationallottery.co.za/results/lotto-plus-1-results',
        'lotto_plus_2': 'https://www.nationallottery.co.za/results/lotto-plus-2-results',
        'powerball': 'https://www.nationallottery.co.za/results/powerball',
        'powerball_plus': 'https://www.nationallottery.co.za/results/powerball-plus',
        'daily_lotto': 'https://www.nationallottery.co.za/results/daily-lotto'
    }
    
    # Create screenshots directory
    os.makedirs('/tmp/screenshots', exist_ok=True)
    
    # Test network connectivity first
    logger.info("Testing network connectivity...")
    test_url = lottery_urls['lotto']
    if not test_network_connectivity(test_url, logger):
        logger.error("Network connectivity test failed - aborting screenshot capture")
        return 0
    
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    successful_captures = 0
    start_time = time.time()
    
    try:
        async with async_playwright() as p:
            # Try multiple browser paths
            browser_paths = [
                "/nix/store/zi4f80l169xlmivz8vja8wlphq74qqk0-chromium-125.0.6422.141/bin/chromium",
                "/usr/bin/chromium-browser", 
                "/usr/bin/chromium",
                None  # Use Playwright's bundled browser
            ]
            
            browser = None
            for browser_path in browser_paths:
                try:
                    if browser_path:
                        logger.info(f"Trying browser path: {browser_path}")
                        browser = await p.chromium.launch(
                            executable_path=browser_path,
                            headless=True,
                            args=[
                                '--no-sandbox',
                                '--disable-setuid-sandbox', 
                                '--disable-dev-shm-usage',
                                '--disable-gpu',
                                '--disable-web-security',
                                '--disable-features=VizDisplayCompositor',
                                '--no-first-run',
                                '--disable-extensions',
                                '--disable-default-apps',
                                '--disable-background-timer-throttling',
                                '--disable-backgrounding-occluded-windows',
                                '--disable-renderer-backgrounding'
                            ]
                        )
                    else:
                        logger.info("Using Playwright's bundled Chromium")
                        browser = await p.chromium.launch(headless=True)
                    
                    logger.info("Browser launched successfully")
                    break
                    
                except Exception as e:
                    logger.warning(f"Failed to launch browser with path {browser_path}: {e}")
                    continue
            
            if not browser:
                logger.error("Failed to launch any browser")
                return 0
            
            # Create browser context with optimized settings
            context = await browser.new_context(
                viewport={'width': 1920, 'height': 1080},
                user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
            )
            
            page = await context.new_page()
            
            # Process each lottery type
            for lottery_type, url in lottery_urls.items():
                # Safety check - abort if taking too long
                if time.time() - start_time > 600:  # 10 minutes max
                    logger.warning("Screenshot capture taking too long, aborting remaining captures")
                    break
                
                # Generate filename
                filename = f"{timestamp}_{lottery_type}.png"
                filepath = os.path.join('screenshots', filename)
                
                # Attempt capture with retry logic
                success = await capture_with_retry(page, url, lottery_type, filepath, logger)
                
                if success:
                    successful_captures += 1
                
                # Small delay between captures to be respectful
                await asyncio.sleep(1)
            
            await browser.close()
            
    except Exception as e:
        logger.error(f"Screenshot capture system failed: {str(e)}")
    
    # Final summary
    total_time = time.time() - start_time
    logger.info(f"Screenshot capture complete: {successful_captures}/6 successful in {total_time:.1f}s")
    
    # Return dict format expected by screenshot_capture.py
    failed_count = 6 - successful_captures
    return {
        'success_count': successful_captures,
        'failed_count': failed_count,
        'successful': ['LOTTO', 'LOTTO_PLUS_1', 'LOTTO_PLUS_2', 'POWERBALL', 'POWERBALL_PLUS', 'DAILY_LOTTO'][:successful_captures],
        'failed': ['LOTTO', 'LOTTO_PLUS_1', 'LOTTO_PLUS_2', 'POWERBALL', 'POWERBALL_PLUS', 'DAILY_LOTTO'][successful_captures:],
        'total_time': total_time
    }

def main():
    """Entry point for script execution"""
    return asyncio.run(robust_screenshot_capture())

if __name__ == "__main__":
    result = main()
    sys.exit(0 if result > 0 else 1)