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
                headless=True,  # Back to headless for server environment
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
                    
                    # Multiple navigation attempts with different strategies
                    navigation_success = False
                    
                    # Strategy 1: Direct navigation
                    try:
                        page.goto(url, wait_until='domcontentloaded', timeout=30000)
                        navigation_success = True
                        logger.info(f"Navigation successful: {url}")
                    except Exception as e:
                        logger.warning(f"Direct navigation failed: {e}")
                    
                    # Strategy 2: If direct fails, try with different wait condition
                    if not navigation_success:
                        try:
                            page.goto(url, wait_until='load', timeout=20000)
                            navigation_success = True
                            logger.info(f"Secondary navigation successful: {url}")
                        except Exception as e:
                            logger.warning(f"Secondary navigation failed: {e}")
                    
                    # Strategy 3: Last resort - basic navigation
                    if not navigation_success:
                        try:
                            page.goto(url, timeout=15000)
                            navigation_success = True
                            logger.info(f"Basic navigation successful: {url}")
                        except Exception as e:
                            logger.error(f"All navigation attempts failed for {url}: {e}")
                            continue
                    
                    # Wait for page to load completely
                    time.sleep(4)
                    
                    # Scroll to load dynamic content
                    try:
                        page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                        time.sleep(1)
                        page.evaluate("window.scrollTo(0, 0)")
                        time.sleep(1)
                    except:
                        pass
                    
                    # Take screenshot with error handling
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    lottery_type = url.split('/')[-1].replace('-', '_')
                    filename = f"{timestamp}_{lottery_type}.png"
                    filepath = os.path.join(screenshot_dir, filename)
                    
                    screenshot_success = False
                    
                    # Capture full page with optimized approach
                    try:
                        logger.info(f"Taking full page screenshot: {filename}")
                        # Use shorter timeout and full_page=True for complete lottery data
                        page.screenshot(path=filepath, full_page=True, timeout=8000)
                        screenshot_success = True
                        logger.info(f"Full page screenshot completed: {filename}")
                    except Exception as e:
                        logger.warning(f"Full page failed: {e}")
                        
                        # Quick viewport fallback
                        try:
                            logger.info(f"Viewport fallback: {filename}")
                            page.screenshot(path=filepath, timeout=5000)
                            screenshot_success = True
                            logger.info(f"Viewport fallback completed: {filename}")
                        except Exception as e:
                            logger.error(f"Both screenshot methods failed: {e}")
                            continue
                    
                    # Verify screenshot quality
                    if os.path.exists(filepath) and os.path.getsize(filepath) > 5000:
                        logger.info(f"Screenshot captured successfully: {filename} ({os.path.getsize(filepath)} bytes)")
                        success_count += 1
                    else:
                        logger.warning(f"Screenshot file too small or missing: {filename}")
                    
                except Exception as e:
                    logger.error(f"Complete capture failed for {url}: {e}")
                    continue
                
                # Shorter delay now that capture is working
                time.sleep(random.uniform(3, 6))
            
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