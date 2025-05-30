"""
Optimized Full-Page Screenshot Capture for Lottery Data
Focus on capturing complete pages efficiently
"""
import os
import sys
import time
import logging
from datetime import datetime
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def capture_full_page_screenshots():
    """Optimized capture with focus on full-page screenshots"""
    
    urls = [
        'https://www.nationallottery.co.za/results/lotto',
        'https://www.nationallottery.co.za/results/lotto-plus-1-results',
        'https://www.nationallottery.co.za/results/lotto-plus-2-results'
    ]
    
    screenshot_dir = os.path.join(os.getcwd(), 'screenshots')
    os.makedirs(screenshot_dir, exist_ok=True)
    
    logger.info("Starting optimized full-page lottery screenshot capture")
    
    with sync_playwright() as p:
        try:
            # Launch with optimized settings
            browser = p.chromium.launch(
                headless=True,
                args=[
                    '--no-sandbox',
                    '--disable-setuid-sandbox',
                    '--disable-dev-shm-usage',
                    '--disable-web-security',
                    '--disable-blink-features=AutomationControlled',
                    '--disable-features=VizDisplayCompositor',
                    '--window-size=1920,1080'
                ]
            )
            
            context = browser.new_context(
                viewport={'width': 1920, 'height': 1080},
                user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
            )
            
            page = context.new_page()
            
            for i, url in enumerate(urls, 1):
                try:
                    logger.info(f"Processing {i}/{len(urls)}: {url}")
                    
                    # Navigate with timeout
                    page.goto(url, timeout=30000, wait_until='networkidle')
                    
                    # Wait for content to load
                    time.sleep(3)
                    
                    # Scroll to ensure all content is loaded
                    page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                    time.sleep(1)
                    page.evaluate("window.scrollTo(0, 0)")
                    time.sleep(1)
                    
                    # Generate filename
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    lottery_type = url.split('/')[-1].replace('-', '_')
                    filename = f"{lottery_type}_{timestamp}.png"
                    filepath = os.path.join(screenshot_dir, filename)
                    
                    # Take full-page screenshot
                    logger.info(f"Capturing full-page screenshot: {filename}")
                    page.screenshot(path=filepath, full_page=True, timeout=15000)
                    
                    # Verify screenshot
                    if os.path.exists(filepath) and os.path.getsize(filepath) > 10000:
                        size_kb = os.path.getsize(filepath) // 1024
                        logger.info(f"✓ Full-page screenshot captured: {filename} ({size_kb}KB)")
                    else:
                        logger.error(f"✗ Screenshot failed or too small: {filename}")
                    
                    # Short delay between captures
                    time.sleep(2)
                    
                except Exception as e:
                    logger.error(f"Failed to capture {url}: {e}")
                    continue
            
            browser.close()
            logger.info("Full-page screenshot capture completed")
            
        except Exception as e:
            logger.error(f"Browser setup failed: {e}")
            return False
    
    return True

if __name__ == "__main__":
    success = capture_full_page_screenshots()
    if success:
        logger.info("Full-page capture process completed successfully")
    else:
        logger.error("Full-page capture process failed")
        sys.exit(1)