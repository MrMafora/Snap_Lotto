#!/usr/bin/env python3
"""
Script to capture a single lottery screenshot with enhanced anti-detection measures.
This script focuses on capturing one lottery type at a time with improved stealth measures.
"""
import os
import sys
import time
import logging
import random
from urllib.parse import urlparse
from playwright.sync_api import sync_playwright
from config import Config

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger("capture_single_screenshot")

# Ensure directories exist
SCREENSHOT_DIR = os.path.join(os.getcwd(), 'screenshots')
os.makedirs(SCREENSHOT_DIR, exist_ok=True)
COOKIES_DIR = os.path.join(os.getcwd(), 'cookies')
os.makedirs(COOKIES_DIR, exist_ok=True)

# Configuration
MAX_WAIT_TIME = 60000  # 60 seconds
NAVIGATION_TIMEOUT = 90000  # 90 seconds
MAX_RETRIES = 3

def capture_screenshot(url, lottery_type, save_to_db=True):
    """
    Capture a screenshot of the specified URL with enhanced stealth measures.
    
    Args:
        url (str): URL to capture
        lottery_type (str): Type of lottery
        save_to_db (bool): Whether to save to database
        
    Returns:
        tuple: (html_path, img_path, success) or (None, None, False) on failure
    """
    domain = urlparse(url).netloc
    cookie_file = os.path.join(COOKIES_DIR, f"{domain.replace('.', '_')}.json")
    timestamp = time.strftime("%Y%m%d_%H%M%S")
    
    # Create safe filename from lottery type
    safe_name = lottery_type.replace(' ', '_').replace('/', '_')
    html_filename = f"{safe_name}_{timestamp}.html"
    img_filename = f"{safe_name}_{timestamp}.png"
    
    html_path = os.path.join(SCREENSHOT_DIR, html_filename)
    img_path = os.path.join(SCREENSHOT_DIR, img_filename)
    
    logger.info(f"Attempting to capture {lottery_type} from {url}")
    
    # Use playwright for improved anti-detection
    with sync_playwright() as p:
        browser_type = p.chromium
        
        # Launch browser with stealth options
        browser = browser_type.launch(
            headless=True,
            args=[
                '--no-sandbox',
                '--disable-setuid-sandbox',
                '--disable-infobars',
                '--window-position=0,0',
                '--ignore-certifcate-errors',
                '--ignore-certifcate-errors-spki-list',
                '--disable-dev-shm-usage',
                '--disable-accelerated-2d-canvas',
                '--disable-gpu',
                '--disable-notifications',
                '--disable-extensions',
                '--disable-component-extensions-with-background-pages',
                f'--window-size={random.choice([1366, 1440, 1536, 1920])},{random.choice([768, 900, 1080])}'
            ],
            chromium_sandbox=False
        )
        
        # Enhanced browser context with more realistic fingerprinting
        context = browser.new_context(
            user_agent=random.choice([
                'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
                'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
                'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:124.0) Gecko/20100101 Firefox/124.0',
            ]),
            locale=random.choice(['en-US', 'en-GB', 'en-ZA']),
            timezone_id=random.choice(['Africa/Johannesburg', 'Europe/London', 'America/New_York']),
            viewport={'width': random.choice([1280, 1366, 1440, 1536]), 'height': random.choice([720, 768, 800, 900])},
            device_scale_factor=random.choice([1, 1.25, 1.5, 2]),
            has_touch=False,
            is_mobile=False,
            color_scheme='no-preference',
            reduced_motion='no-preference',
            forced_colors='none',
            accept_downloads=False
        )
        
        # Load cookies if available
        try:
            if os.path.exists(cookie_file):
                with open(cookie_file, 'r') as f:
                    cookies = eval(f.read())
                    if cookies:
                        context.add_cookies(cookies)
                        logger.info(f"Loaded {len(cookies)} cookies for {domain}")
        except Exception as e:
            logger.warning(f"Error loading cookies: {str(e)}")
        
        try:
            # Create a new page
            page = context.new_page()
            
            # Set additional headers to appear more like a real browser
            page.set_extra_http_headers({
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.9,en-ZA;q=0.8',
                'Accept-Encoding': 'gzip, deflate, br',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1',
                'Sec-Fetch-Dest': 'document',
                'Sec-Fetch-Mode': 'navigate',
                'Sec-Fetch-Site': 'none',
                'Sec-Fetch-User': '?1',
                'sec-ch-ua': '"Chromium";v="124", "Google Chrome";v="124"',
                'sec-ch-ua-mobile': '?0',
                'sec-ch-ua-platform': '"Windows"',
                'DNT': '1',
            })
            
            # Stealth mode: inject scripts to evade detection
            page.add_init_script("""
                // Override WebGL fingerprinting
                const getParameterProxyHandler = {
                    apply: function(target, ctx, args) {
                        if (args[0] === 37445) {
                            return 'Intel Inc.'
                        }
                        if (args[0] === 37446) {
                            return 'Intel Iris OpenGL Engine'
                        }
                        return Reflect.apply(target, ctx, args)
                    }
                }
                
                // Add subtle random delays to Date
                const originalDate = Date
                Date = function(...args) {
                    if (args.length === 0) {
                        const d = new originalDate()
                        const offset = Math.floor(Math.random() * 7) // 0-6ms variance
                        d.setMilliseconds(d.getMilliseconds() + offset)
                        return d
                    }
                    return new originalDate(...args)
                }
                Date.now = function() {
                    const n = originalDate.now()
                    return n + Math.floor(Math.random() * 5)
                }
                Date.prototype = originalDate.prototype
                
                // Emulate normal browser behavior
                const originalQuerySelector = document.querySelector
                document.querySelector = function(...args) {
                    // Add a negligible delay
                    const start = Date.now()
                    while(Date.now() - start < Math.random() * 2) {}
                    return originalQuerySelector.apply(this, args)
                }
            """)
            
            # Randomize navigation timing
            pre_nav_delay = random.uniform(0.5, 2.5)
            logger.info(f"Waiting {pre_nav_delay:.2f} seconds before navigation...")
            time.sleep(pre_nav_delay)
            
            # Navigate to the URL with increased timeout
            logger.info(f"Navigating to {url} with timeout {NAVIGATION_TIMEOUT}ms")
            page.set_default_navigation_timeout(NAVIGATION_TIMEOUT)
            page.set_default_timeout(MAX_WAIT_TIME)
            
            # Try different navigation strategies
            try:
                logger.info("Trying navigation strategy 1: domcontentloaded")
                page.goto(url, wait_until='domcontentloaded', timeout=NAVIGATION_TIMEOUT)
            except Exception:
                try:
                    logger.info("Trying navigation strategy 2: load")
                    page.goto(url, wait_until='load', timeout=NAVIGATION_TIMEOUT)
                except Exception:
                    logger.info("Trying navigation strategy 3: networkidle")
                    page.goto(url, wait_until='networkidle', timeout=NAVIGATION_TIMEOUT)
            
            # Wait for content to stabilize
            time.sleep(random.uniform(2.0, 5.0))
            
            # Simulate human scrolling behavior
            logger.info("Performing natural scrolling behavior...")
            page.evaluate("""
                () => {
                    const totalHeight = document.body.scrollHeight;
                    const viewportHeight = window.innerHeight;
                    const scrollSteps = Math.ceil(totalHeight / viewportHeight) + 1;
                    
                    function smoothScroll(startY, endY, duration) {
                        const startTime = Date.now();
                        
                        function scroll() {
                            const currentTime = Date.now();
                            const elapsedTime = currentTime - startTime;
                            
                            if (elapsedTime < duration) {
                                const progress = elapsedTime / duration;
                                // Ease in-out curve
                                const easedProgress = progress < 0.5 
                                    ? 2 * progress * progress 
                                    : 1 - Math.pow(-2 * progress + 2, 2) / 2;
                                
                                const y = startY + (endY - startY) * easedProgress;
                                window.scrollTo(0, y);
                                requestAnimationFrame(scroll);
                            } else {
                                window.scrollTo(0, endY);
                            }
                        }
                        
                        requestAnimationFrame(scroll);
                        return new Promise(resolve => setTimeout(resolve, duration));
                    }
                    
                    return (async () => {
                        for (let i = 1; i < scrollSteps; i++) {
                            // Random scroll distance (75-100% of viewport)
                            const scrollDistance = viewportHeight * (0.75 + Math.random() * 0.25);
                            // Random duration (300-800ms)
                            const duration = 300 + Math.random() * 500;
                            
                            await smoothScroll(
                                window.pageYOffset, 
                                Math.min(window.pageYOffset + scrollDistance, totalHeight - viewportHeight),
                                duration
                            );
                            
                            // Pause at each position for a random time (200-1500ms)
                            await new Promise(r => setTimeout(r, 200 + Math.random() * 1300));
                            
                            // Occasionally scroll back up a bit
                            if (Math.random() < 0.3 && window.pageYOffset > viewportHeight) {
                                await smoothScroll(
                                    window.pageYOffset,
                                    window.pageYOffset - (viewportHeight * (0.2 + Math.random() * 0.3)),
                                    300 + Math.random() * 200
                                );
                                await new Promise(r => setTimeout(r, 200 + Math.random() * 300));
                            }
                        }
                        
                        // Final scroll to bottom
                        await smoothScroll(window.pageYOffset, 0, 500 + Math.random() * 300);
                        return true;
                    })();
                }
            """)
            
            # Random wait after scrolling
            time.sleep(random.uniform(1.0, 3.0))
            
            # Take screenshot
            logger.info("Taking screenshot...")
            page.screenshot(path=img_path)
            
            # Get the full HTML content
            html_content = page.content()
            with open(html_path, 'w', encoding='utf-8') as f:
                f.write(html_content)
            
            # Save the cookies for future use
            try:
                cookies = context.cookies()
                with open(cookie_file, 'w') as f:
                    f.write(str(cookies))
                    logger.info(f"Saved {len(cookies)} cookies for {domain}")
            except Exception as e:
                logger.warning(f"Error saving cookies: {str(e)}")
            
            logger.info(f"Successfully captured screenshot and HTML for {lottery_type}")
            
            # Save to database if requested
            if save_to_db:
                try:
                    from main import app
                    from screenshot_manager import save_screenshot_to_database
                    
                    with app.app_context():
                        screenshot_id = save_screenshot_to_database(url, lottery_type, html_path, img_path)
                        logger.info(f"Saved to database with ID {screenshot_id}")
                except Exception as e:
                    logger.error(f"Error saving to database: {str(e)}")
            
            return html_path, img_path, True
        
        except Exception as e:
            logger.error(f"Error capturing screenshot: {str(e)}")
            return None, None, False
        
        finally:
            browser.close()

def list_missing_types():
    """List all missing lottery types and their indices."""
    try:
        from main import app
        from models import Screenshot
        from data_aggregator import normalize_lottery_type
        
        with app.app_context():
            # Get existing normalized types
            existing_types_query = Screenshot.query.with_entities(Screenshot.lottery_type).distinct().all()
            existing_normalized = [normalize_lottery_type(lt[0]) for lt in existing_types_query]
            
            # All required types with their config mapping
            all_types = {
                "Lottery": "Lotto",
                "Lottery Plus 1": "Lotto Plus 1",
                "Lottery Plus 2": "Lotto Plus 2",
                "Powerball": "Powerball",
                "Powerball Plus": "Powerball Plus",
                "Daily Lottery": "Daily Lotto"
            }
            
            # List missing types
            missing = {norm_type: config_type for norm_type, config_type in all_types.items() 
                      if norm_type not in existing_normalized}
            
            if not missing:
                print("All lottery types are captured!")
                return {}
            
            print(f"Found {len(missing)} missing lottery types:")
            for i, (norm_type, config_type) in enumerate(missing.items(), 1):
                url = None
                for url_info in Config.RESULTS_URLS:
                    if url_info['lottery_type'] == config_type:
                        url = url_info['url']
                        break
                
                print(f"[{i}] {norm_type} (Config: {config_type})")
                print(f"    URL: {url}")
            
            return missing
    except Exception as e:
        logger.error(f"Error listing missing types: {str(e)}")
        return {}

def main():
    """Main function to capture a single screenshot."""
    missing = list_missing_types()
    
    if not missing:
        return
    
    try:
        choice = input("\nEnter the number of the lottery type to capture (or 'a' for all): ")
        
        if choice.lower() == 'a':
            # Capture all missing types
            print("Capturing all missing lottery types...")
            
            for i, (norm_type, config_type) in enumerate(missing.items(), 1):
                url = None
                for url_info in Config.RESULTS_URLS:
                    if url_info['lottery_type'] == config_type:
                        url = url_info['url']
                        break
                
                if url:
                    print(f"\nCapturing {norm_type} ({i}/{len(missing)})...")
                    capture_screenshot(url, config_type)
                    # Add delay between captures
                    if i < len(missing):
                        sleep_time = random.uniform(8.0, 15.0)
                        print(f"Waiting {sleep_time:.1f} seconds before next capture...")
                        time.sleep(sleep_time)
        else:
            try:
                index = int(choice) - 1
                if index < 0 or index >= len(missing):
                    print("Invalid choice!")
                    return
                
                norm_type = list(missing.keys())[index]
                config_type = missing[norm_type]
                
                url = None
                for url_info in Config.RESULTS_URLS:
                    if url_info['lottery_type'] == config_type:
                        url = url_info['url']
                        break
                
                if url:
                    capture_screenshot(url, config_type)
            except ValueError:
                print("Invalid input! Please enter a number or 'a'.")
    
    except KeyboardInterrupt:
        print("\nOperation cancelled by user.")

if __name__ == "__main__":
    main()