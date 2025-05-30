"""
Step 2: Advanced Screenshot Capture System with Stealth Techniques
Uses sophisticated anti-detection methods to capture lottery screenshots
"""
import os
import time
import random
import logging
from datetime import datetime
from playwright.sync_api import sync_playwright
import requests

logger = logging.getLogger(__name__)

# More diverse user agents with recent versions
USER_AGENTS = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0',
    'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36 Edg/119.0.0.0',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Safari/605.1.15'
]

# South African IP ranges and locations for more realistic requests
SA_VIEWPORT_SIZES = [
    {'width': 1920, 'height': 1080},
    {'width': 1366, 'height': 768},
    {'width': 1280, 'height': 720},
    {'width': 1440, 'height': 900}
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

def capture_with_stealth_browser():
    """Advanced stealth capture with multiple anti-detection techniques"""
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
            # Launch Chrome with maximum stealth settings using system browser
            browser = p.chromium.launch(
                headless=True,
                executable_path='/nix/store/zi4f80l169xlmivz8vja8wlphq74qqk0-chromium-125.0.6422.141/bin/chromium',
                args=[
                    '--no-sandbox',
                    '--disable-dev-shm-usage',
                    '--disable-blink-features=AutomationControlled',
                    '--disable-features=VizDisplayCompositor',
                    '--disable-extensions',
                    '--disable-plugins',
                    '--disable-web-security',
                    '--disable-background-timer-throttling',
                    '--disable-backgrounding-occluded-windows',
                    '--disable-renderer-backgrounding',
                    '--disable-field-trial-config',
                    '--disable-back-forward-cache',
                    '--disable-hang-monitor',
                    '--disable-ipc-flooding-protection',
                    '--disable-prompt-on-repost',
                    '--disable-sync',
                    '--force-color-profile=srgb',
                    '--metrics-recording-only',
                    '--no-first-run',
                    '--enable-automation=false',
                    '--password-store=basic',
                    '--use-mock-keychain',
                    '--hide-scrollbars',
                    '--mute-audio'
                ]
            )
            
            # Create context with realistic settings
            viewport = random.choice(SA_VIEWPORT_SIZES)
            user_agent = random.choice(USER_AGENTS)
            
            context = browser.new_context(
                user_agent=user_agent,
                viewport=viewport,
                locale='en-ZA',
                timezone_id='Africa/Johannesburg',
                permissions=['geolocation'],
                geolocation={'latitude': -26.2041, 'longitude': 28.0473},  # Johannesburg coordinates
                extra_http_headers={
                    'Accept-Language': 'en-ZA,en;q=0.9',
                    'Accept-Encoding': 'gzip, deflate, br',
                    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                    'Connection': 'keep-alive',
                    'Upgrade-Insecure-Requests': '1',
                    'Cache-Control': 'max-age=0'
                }
            )
            
            page = context.new_page()
            
            # Add stealth scripts to avoid detection
            page.add_init_script("""
                Object.defineProperty(navigator, 'webdriver', {
                    get: () => undefined,
                });
                
                Object.defineProperty(navigator, 'plugins', {
                    get: () => [1, 2, 3, 4, 5],
                });
                
                Object.defineProperty(navigator, 'languages', {
                    get: () => ['en-US', 'en'],
                });
                
                window.chrome = {
                    runtime: {},
                };
                
                Object.defineProperty(navigator, 'permissions', {
                    get: () => ({
                        query: () => Promise.resolve({ state: 'granted' }),
                    }),
                });
            """)
            
            # Set realistic timeouts
            page.set_default_timeout(20000)
            
            for i, url in enumerate(urls):
                try:
                    logger.info(f"Attempting stealth capture from: {url}")
                    
                    # Navigate with realistic behavior
                    page.goto(url, wait_until='domcontentloaded', timeout=20000)
                    
                    # Simulate human behavior
                    time.sleep(random.uniform(3, 6))
                    
                    # Random mouse movements and scrolling
                    page.mouse.move(random.randint(100, 500), random.randint(100, 400))
                    page.mouse.wheel(0, random.randint(100, 300))
                    time.sleep(random.uniform(1, 3))
                    
                    # Wait for lottery content to load
                    try:
                        page.wait_for_selector('body', timeout=5000)
                    except:
                        pass
                    
                    # Take screenshot
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    lottery_type = url.split('/')[-1].replace('-', '_')
                    filename = f"{timestamp}_{lottery_type}.png"
                    filepath = os.path.join(screenshot_dir, filename)
                    
                    page.screenshot(path=filepath, full_page=True, timeout=10000)
                    
                    if os.path.exists(filepath) and os.path.getsize(filepath) > 5000:
                        logger.info(f"Screenshot captured successfully: {filename}")
                        success_count += 1
                    else:
                        logger.warning(f"Screenshot too small or missing: {filename}")
                    
                except Exception as e:
                    logger.error(f"Failed to capture {url}: {e}")
                    continue
                
                # Random delay between captures to avoid rate limiting
                time.sleep(random.uniform(4, 8))
            
            browser.close()
            
    except Exception as e:
        logger.error(f"Stealth browser setup failed: {e}")
        return False, 0
    
    return success_count > 0, success_count

def capture_lottery_screenshots():
    """Main capture function with fallback strategies"""
    logger.info("Starting lottery screenshot capture with advanced techniques")
    
    # Test site accessibility first
    if not test_site_accessibility():
        logger.warning("Site appears to be blocking all requests")
    
    # Try stealth browser approach
    success, count = capture_with_stealth_browser()
    
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