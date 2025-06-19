#!/usr/bin/env python3
"""
Visual Screenshot Capture Module
Captures high-quality PNG screenshots from South African lottery websites
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

class LotteryScreenshotCapture:
    def __init__(self):
        self.screenshot_dir = os.path.join(os.getcwd(), 'screenshots')
        os.makedirs(self.screenshot_dir, exist_ok=True)
    
    async def capture_screenshot(self, url, lottery_type, retries=3):
        """Capture high-quality screenshot of lottery results page"""
        for attempt in range(retries):
            try:
                logger.info(f"Capturing {lottery_type} screenshot from {url} (attempt {attempt + 1})")
                
                async with async_playwright() as p:
                    # Launch browser with optimized settings for screenshots
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
                    
                    # Create context with South African locale
                    context = await browser.new_context(
                        viewport={'width': 1920, 'height': 1080},
                        locale='en-ZA',
                        timezone_id='Africa/Johannesburg',
                        user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
                    )
                    
                    page = await context.new_page()
                    
                    # Navigate to the page
                    await page.goto(url, wait_until='networkidle', timeout=30000)
                    
                    # Wait for lottery results content to load
                    try:
                        await page.wait_for_selector('.lottery-results, .results, .winning-numbers', timeout=10000)
                    except:
                        logger.warning(f"Lottery results selector not found on {url}, proceeding anyway")
                    
                    # Additional wait for dynamic content
                    await page.wait_for_timeout(3000)
                    
                    # Generate filename
                    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                    safe_lottery_type = lottery_type.lower().replace(' ', '_').replace('+', '_plus_')
                    filename = f"{timestamp}_{safe_lottery_type}_screenshot.png"
                    filepath = os.path.join(self.screenshot_dir, filename)
                    
                    # Capture full page screenshot with high quality
                    await page.screenshot(
                        path=filepath,
                        full_page=True,
                        type='png',
                        quality=95,
                        clip=None
                    )
                    
                    await browser.close()
                    
                    # Verify screenshot was created
                    if os.path.exists(filepath) and os.path.getsize(filepath) > 10000:  # At least 10KB
                        logger.info(f"Successfully captured {lottery_type} screenshot: {filename}")
                        return filepath
                    else:
                        logger.error(f"Screenshot capture failed or file too small: {filename}")
                        return None
                        
            except Exception as e:
                logger.error(f"Error capturing {lottery_type} screenshot (attempt {attempt + 1}): {str(e)}")
                if attempt < retries - 1:
                    await asyncio.sleep(5)  # Wait before retry
                else:
                    logger.error(f"Failed to capture {lottery_type} screenshot after {retries} attempts")
                    return None
    
    async def capture_all_lottery_screenshots(self):
        """Capture screenshots from all lottery result pages"""
        results = {}
        
        # Get lottery URLs from config
        lottery_urls = Config.LOTTERY_URLS
        
        for lottery_type, url in lottery_urls.items():
            logger.info(f"Starting capture for {lottery_type}")
            
            # Add delay between captures to be respectful
            if results:  # Not the first capture
                await asyncio.sleep(8)  # 8 second delay between captures
            
            filepath = await self.capture_screenshot(url, lottery_type)
            results[lottery_type] = {
                'success': filepath is not None,
                'filepath': filepath,
                'url': url
            }
            
            if filepath:
                logger.info(f"✓ {lottery_type} screenshot captured successfully")
            else:
                logger.error(f"✗ {lottery_type} screenshot capture failed")
        
        return results

def run_visual_capture():
    """Run the visual screenshot capture process"""
    logger.info("=== VISUAL SCREENSHOT CAPTURE STARTED ===")
    
    async def main():
        capture = LotteryScreenshotCapture()
        results = await capture.capture_all_lottery_screenshots()
        
        success_count = sum(1 for r in results.values() if r['success'])
        total_count = len(results)
        
        logger.info(f"=== VISUAL SCREENSHOT CAPTURE COMPLETED ===")
        logger.info(f"Successfully captured: {success_count}/{total_count} screenshots")
        
        return success_count == total_count
    
    return asyncio.run(main())

if __name__ == "__main__":
    success = run_visual_capture()
    exit(0 if success else 1)