"""
Ultimate Screenshot Capture - Maximum Stealth Approach
Uses the most advanced anti-detection techniques available
"""
import os
import time
import random
import logging
from datetime import datetime
from playwright.sync_api import sync_playwright
import base64

logger = logging.getLogger(__name__)

# Real South African user agents from actual browsers
SA_USER_AGENTS = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/119.0'
]

def capture_with_ultimate_stealth():
    """Ultimate stealth capture with maximum human simulation"""
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
            # Use system Chromium with maximum stealth
            browser = p.chromium.launch(
                headless=False,  # Try non-headless first
                executable_path='/nix/store/zi4f80l169xlmivz8vja8wlphq74qqk0-chromium-125.0.6422.141/bin/chromium',
                args=[
                    '--no-sandbox',
                    '--disable-dev-shm-usage',
                    '--disable-blink-features=AutomationControlled',
                    '--exclude-switches=enable-automation',
                    '--disable-extensions-except',
                    '--disable-plugins-discovery',
                    '--disable-web-security',
                    '--allow-running-insecure-content',
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
                    '--password-store=basic',
                    '--use-mock-keychain',
                    '--disable-component-extensions-with-background-pages',
                    '--disable-default-apps',
                    '--mute-audio',
                    '--no-default-browser-check',
                    '--autoplay-policy=user-gesture-required',
                    '--disable-background-mode',
                    '--disable-features=TranslateUI,BlinkGenPropertyTrees',
                    '--disable-extensions',
                    '--disable-plugins'
                ]
            )
            
            # Create ultra-realistic context
            context = browser.new_context(
                user_agent=random.choice(SA_USER_AGENTS),
                viewport={'width': 1366, 'height': 768},
                locale='en-ZA',
                timezone_id='Africa/Johannesburg',
                geolocation={'latitude': -26.2041, 'longitude': 28.0473},
                permissions=['geolocation'],
                color_scheme='light',
                extra_http_headers={
                    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
                    'Accept-Language': 'en-ZA,en-GB;q=0.9,en;q=0.8,af;q=0.7',
                    'Accept-Encoding': 'gzip, deflate, br',
                    'Cache-Control': 'max-age=0',
                    'Connection': 'keep-alive',
                    'Upgrade-Insecure-Requests': '1',
                    'Sec-Fetch-Dest': 'document',
                    'Sec-Fetch-Mode': 'navigate',
                    'Sec-Fetch-Site': 'none',
                    'Sec-Fetch-User': '?1'
                }
            )
            
            page = context.new_page()
            
            # Maximum stealth injection
            page.add_init_script("""
                // Remove webdriver property
                Object.defineProperty(navigator, 'webdriver', {
                    get: () => undefined,
                });
                
                // Override plugins
                Object.defineProperty(navigator, 'plugins', {
                    get: () => [
                        { name: 'Chrome PDF Plugin', filename: 'internal-pdf-viewer' },
                        { name: 'Chrome PDF Viewer', filename: 'mhjfbmdgcfjbbpaeojofohoefgiehjai' },
                        { name: 'Native Client', filename: 'internal-nacl-plugin' }
                    ],
                });
                
                // Override languages
                Object.defineProperty(navigator, 'languages', {
                    get: () => ['en-ZA', 'en-GB', 'en', 'af'],
                });
                
                // Add chrome runtime
                window.chrome = {
                    runtime: {
                        onConnect: null,
                        onMessage: null,
                    },
                };
                
                // Override permissions
                const originalQuery = window.navigator.permissions.query;
                window.navigator.permissions.query = (parameters) => (
                    parameters.name === 'notifications' ?
                        Promise.resolve({ state: Notification.permission }) :
                        originalQuery(parameters)
                );
                
                // Mock device memory
                Object.defineProperty(navigator, 'deviceMemory', {
                    get: () => 8,
                });
                
                // Mock hardware concurrency
                Object.defineProperty(navigator, 'hardwareConcurrency', {
                    get: () => 4,
                });
                
                // Override getContext
                const getParameter = WebGLRenderingContext.getParameter;
                WebGLRenderingContext.prototype.getParameter = function(parameter) {
                    if (parameter === 37445) {
                        return 'Intel Inc.';
                    }
                    if (parameter === 37446) {
                        return 'Intel(R) UHD Graphics 620';
                    }
                    return getParameter(parameter);
                };
            """)
            
            # Set longer timeout for difficult sites
            page.set_default_timeout(60000)
            
            for i, url in enumerate(urls):
                try:
                    logger.info(f"Ultimate stealth capture attempt: {url}")
                    
                    # Navigate with maximum patience
                    page.goto(url, wait_until='load', timeout=60000)
                    
                    # Extensive human simulation
                    time.sleep(random.uniform(5, 10))
                    
                    # Multiple mouse movements
                    for _ in range(3):
                        page.mouse.move(
                            random.randint(100, 800), 
                            random.randint(100, 600)
                        )
                        time.sleep(random.uniform(0.5, 1.5))
                    
                    # Realistic scrolling
                    for _ in range(random.randint(2, 4)):
                        page.mouse.wheel(0, random.randint(100, 400))
                        time.sleep(random.uniform(1, 2))
                    
                    # Wait for any dynamic content
                    time.sleep(random.uniform(3, 6))
                    
                    # Try to wait for lottery-specific content
                    try:
                        page.wait_for_selector('body', timeout=10000)
                    except:
                        pass
                    
                    # Take screenshot with full page
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    lottery_type = url.split('/')[-1].replace('-', '_')
                    filename = f"{timestamp}_{lottery_type}.png"
                    filepath = os.path.join(screenshot_dir, filename)
                    
                    page.screenshot(path=filepath, full_page=True, timeout=30000)
                    
                    if os.path.exists(filepath) and os.path.getsize(filepath) > 10000:
                        logger.info(f"Ultimate capture SUCCESS: {filename}")
                        success_count += 1
                    else:
                        logger.warning(f"Screenshot file too small: {filename}")
                    
                except Exception as e:
                    logger.error(f"Ultimate capture failed for {url}: {e}")
                    continue
                
                # Extended delay between requests
                time.sleep(random.uniform(10, 20))
            
            browser.close()
            
    except Exception as e:
        logger.error(f"Ultimate stealth browser failed: {e}")
        return False, 0
    
    return success_count > 0, success_count

def capture_lottery_screenshots():
    """Main function for ultimate stealth capture"""
    logger.info("Starting ULTIMATE stealth lottery screenshot capture")
    
    success, count = capture_with_ultimate_stealth()
    
    if success:
        logger.info(f"ULTIMATE capture completed: {count} screenshots captured")
        return True, count
    else:
        logger.error("ULTIMATE capture failed - all methods exhausted")
        return False, 0

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    success, count = capture_lottery_screenshots()
    print(f"Ultimate capture result: {success}, Count: {count}")