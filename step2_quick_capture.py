"""
Quick Full-Page Screenshot Capture for Lottery Data
Simplified approach focused on reliability and complete page capture
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

def quick_full_page_capture():
    """Quick and reliable full-page capture approach"""
    
    urls = [
        'https://www.nationallottery.co.za/results/lotto',
        'https://www.nationallottery.co.za/results/lotto-plus-1-results',
        'https://www.nationallottery.co.za/results/lotto-plus-2-results'
    ]
    
    screenshot_dir = os.path.join(os.getcwd(), 'screenshots')
    os.makedirs(screenshot_dir, exist_ok=True)
    
    logger.info("Starting quick full-page lottery capture")
    
    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=True,
            args=['--no-sandbox', '--disable-setuid-sandbox', '--disable-dev-shm-usage']
        )
        
        page = browser.new_page(viewport={'width': 1366, 'height': 768})
        
        for i, url in enumerate(urls, 1):
            try:
                logger.info(f"Processing {i}/{len(urls)}: {url}")
                
                # Navigate quickly
                page.goto(url, timeout=20000)
                
                # Brief wait for content
                time.sleep(2)
                
                # Quick scroll to load content
                page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                time.sleep(1)
                page.evaluate("window.scrollTo(0, 0)")
                time.sleep(1)
                
                # Generate filename
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                lottery_type = url.split('/')[-1].replace('-', '_')
                filename = f"{lottery_type}_{timestamp}.png"
                filepath = os.path.join(screenshot_dir, filename)
                
                # Take screenshot with shorter timeout
                logger.info(f"Capturing: {filename}")
                page.screenshot(path=filepath, full_page=True, timeout=5000)
                
                # Quick verification
                if os.path.exists(filepath) and os.path.getsize(filepath) > 8000:
                    size_kb = os.path.getsize(filepath) // 1024
                    logger.info(f"✓ Captured: {filename} ({size_kb}KB)")
                else:
                    logger.error(f"✗ Failed: {filename}")
                
            except Exception as e:
                logger.error(f"Error capturing {url}: {e}")
                continue
        
        browser.close()
    
    return True

if __name__ == "__main__":
    success = quick_full_page_capture()
    sys.exit(0 if success else 1)