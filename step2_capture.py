"""
Step 2: Screenshot Capture System - Working Playwright Version
Uses Playwright to capture current lottery screenshots from GitHub working solution
"""
import os
import time
import random
import logging
from datetime import datetime
from playwright.sync_api import sync_playwright

logger = logging.getLogger(__name__)

# User agents to rotate through (from working GitHub repo)
USER_AGENTS = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/115.0',
    'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
]

def capture_lottery_screenshots():
    """Capture live screenshots from South African National Lottery website using Playwright"""
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
            # Launch browser with anti-detection features using system Chromium
            browser = p.chromium.launch(
                headless=True,
                executable_path='/nix/store/zi4f80l169xlmivz8vja8wlphq74qqk0-chromium-125.0.6422.141/bin/chromium',
                args=[
                    '--no-sandbox',
                    '--disable-dev-shm-usage',
                    '--disable-blink-features=AutomationControlled',
                    '--disable-web-security',
                    '--disable-features=VizDisplayCompositor',
                    '--user-agent=' + random.choice(USER_AGENTS)
                ]
            )
            
            # Create context with random user agent
            user_agent = random.choice(USER_AGENTS)
            context = browser.new_context(
                user_agent=user_agent,
                viewport={'width': 1366, 'height': 768}
            )
            
            page = context.new_page()
            
            # Hide webdriver property
            page.add_init_script("""
                Object.defineProperty(navigator, 'webdriver', {
                    get: () => undefined,
                });
            """)
            
            for i, url in enumerate(urls):
                try:
                    logger.info(f"Attempting screenshot capture from: {url}")
                    
                    # Navigate with retry logic
                    page.goto(url, wait_until='networkidle', timeout=30000)
                    
                    # Human-like behavior - wait and scroll
                    time.sleep(random.uniform(2, 4))
                    
                    # Scroll to ensure content loads
                    page.evaluate("window.scrollTo(0, document.body.scrollHeight/2)")
                    time.sleep(random.uniform(1, 2))
                    page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                    time.sleep(random.uniform(1, 3))
                    page.evaluate("window.scrollTo(0, 0)")
                    time.sleep(random.uniform(1, 2))
                    
                    # Wait for lottery results to load
                    page.wait_for_timeout(3000)
                    
                    # Take screenshot
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    lottery_type = url.split('/')[-1].replace('-', '_')
                    filename = f"{timestamp}_{lottery_type}.png"
                    filepath = os.path.join(screenshot_dir, filename)
                    
                    page.screenshot(path=filepath, full_page=True)
                    
                    if os.path.exists(filepath):
                        size = os.path.getsize(filepath)
                        logger.info(f"Screenshot captured successfully: {filename} ({size} bytes)")
                        success_count += 1
                    else:
                        logger.error(f"Screenshot file not created: {filename}")
                        
                except Exception as e:
                    logger.error(f"Failed to capture screenshot from {url}: {e}")
                    continue
                
                # Delay between captures to avoid detection
                if i < len(urls) - 1:
                    time.sleep(random.uniform(3, 6))
            
            browser.close()
            
    except Exception as e:
        logger.error(f"Screenshot capture failed: {e}")
        return False, 0
    
    if success_count > 0:
        logger.info(f"Screenshot capture completed: {success_count}/{len(urls)} successful")
        return True, success_count
    else:
        logger.error("No screenshots could be captured")
        return False, 0

def capture_lottery_screenshots_automated():
    """Automated capture method with timeout protection"""
    
    import signal
    
    def timeout_handler(signum, frame):
        logger.warning("Screenshot capture timed out after 120 seconds")
        raise TimeoutError("Screenshot capture timeout")
    
    # Set 2 minute timeout
    signal.signal(signal.SIGALRM, timeout_handler)
    signal.alarm(120)
    
    try:
        result = capture_lottery_screenshots()
        signal.alarm(0)  # Cancel timeout
        return result
    except Exception as e:
        signal.alarm(0)  # Cancel timeout
        logger.error(f"Automated screenshot capture failed: {e}")
        return False, 0

if __name__ == "__main__":
    # Test the screenshot capture
    logging.basicConfig(level=logging.INFO)
    success, count = capture_lottery_screenshots()
    print(f"Screenshot capture result: {success}, Count: {count}")