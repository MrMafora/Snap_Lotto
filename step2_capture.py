"""
Step 2: Advanced Screenshot Capture System
Uses multiple bypass techniques to capture lottery screenshots
"""
import os
import time
import random
import logging
from datetime import datetime
from playwright.sync_api import sync_playwright
import requests

logger = logging.getLogger(__name__)

# Rotate through different user agents
USER_AGENTS = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/119.0',
    'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
]

def test_site_accessibility():
    """Test if the lottery site is accessible via requests first"""
    test_urls = [
        'https://www.nationallottery.co.za/results/lotto',
        'https://www.nationallottery.co.za/results/powerball'
    ]
    
    for url in test_urls:
        try:
            response = requests.get(url, timeout=10, headers={
                'User-Agent': random.choice(USER_AGENTS),
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.5',
                'Accept-Encoding': 'gzip, deflate',
                'Connection': 'keep-alive'
            })
            logger.info(f"Site accessibility test - {url}: Status {response.status_code}")
            if response.status_code == 200:
                return True
        except Exception as e:
            logger.info(f"Site accessibility test failed for {url}: {e}")
    
    return False

def capture_with_minimal_browser():
    """Try capturing with minimal browser footprint"""
    urls = [
        'https://www.nationallottery.co.za/results/lotto',
        'https://www.nationallottery.co.za/results/lotto-plus-1-results', 
        'https://www.nationallottery.co.za/results/lotto-plus-2-results',
        'https://www.nationallottery.co.za/results/powerball',
        'https://www.nationallottery.co.za/results/powerball-plus',
        'https://www.nationallottery.co.za/results/daily-lotto'
    ]
    
    screenshot_dir = os.path.join(os.getcwd(), 'screenshots')
    os.makedirs(screenshot_dir, exist_ok=True)
    
    success_count = 0
    
    try:
        with sync_playwright() as p:
            # Use Firefox instead of Chrome for better stealth
            browser = p.firefox.launch(
                headless=True,
                args=[
                    '--no-sandbox',
                    '--disable-dev-shm-usage'
                ]
            )
            
            context = browser.new_context(
                user_agent=random.choice(USER_AGENTS),
                viewport={'width': 1280, 'height': 720},
                locale='en-ZA'  # South African locale
            )
            
            page = context.new_page()
            
            # Set shorter timeouts to fail fast
            page.set_default_timeout(8000)
            
            for i, url in enumerate(urls):
                try:
                    logger.info(f"Attempting minimal capture from: {url}")
                    
                    # Simple navigation without waiting for network idle
                    page.goto(url, timeout=8000)
                    
                    # Wait briefly for content
                    time.sleep(3)
                    
                    # Take screenshot immediately
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    lottery_type = url.split('/')[-1].replace('-', '_')
                    filename = f"{timestamp}_{lottery_type}.png"
                    filepath = os.path.join(screenshot_dir, filename)
                    
                    page.screenshot(path=filepath, timeout=5000)
                    
                    if os.path.exists(filepath) and os.path.getsize(filepath) > 1000:
                        logger.info(f"Screenshot captured: {filename}")
                        success_count += 1
                    
                except Exception as e:
                    logger.error(f"Failed to capture {url}: {e}")
                    continue
                
                # Brief delay between captures
                time.sleep(random.uniform(2, 4))
            
            browser.close()
            
    except Exception as e:
        logger.error(f"Browser setup failed: {e}")
        return False, 0
    
    return success_count > 0, success_count

def capture_lottery_screenshots():
    """Main capture function with fallback strategies"""
    logger.info("Starting lottery screenshot capture with advanced techniques")
    
    # Test site accessibility first
    if not test_site_accessibility():
        logger.warning("Site appears to be blocking all requests")
    
    # Try minimal browser approach
    success, count = capture_with_minimal_browser()
    
    if success:
        logger.info(f"Screenshot capture completed: {count} screenshots captured")
        return True, count
    else:
        logger.error("All capture methods failed - lottery website is blocking access")
        return False, 0

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    success, count = capture_lottery_screenshots()
    print(f"Capture result: {success}, Count: {count}")