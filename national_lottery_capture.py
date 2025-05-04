#!/usr/bin/env python3
"""
Specialized capture module for the National Lottery website (nationallottery.co.za)
with enhanced anti-bot measures specifically tailored for this site.

This module implements advanced techniques to bypass Cloudflare and other anti-bot
protections on the National Lottery website.
"""
import os
import sys
import logging
import random
import time
import json
import hashlib
import uuid
from datetime import datetime
from urllib.parse import urlparse
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# Import modules for different capture strategies
try:
    import undetected_chromedriver as uc
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    from selenium.common.exceptions import TimeoutException, WebDriverException
    HAS_UNDETECTED_CHROMEDRIVER = True
except ImportError:
    logger.warning("undetected_chromedriver not available. This strategy will be skipped.")
    HAS_UNDETECTED_CHROMEDRIVER = False

try:
    from playwright.sync_api import sync_playwright
    HAS_PLAYWRIGHT = True
except ImportError:
    logger.warning("playwright not available. This strategy will be skipped.")
    HAS_PLAYWRIGHT = False

try:
    import requests
    from bs4 import BeautifulSoup
    HAS_REQUESTS = True
except ImportError:
    logger.warning("requests not available. This strategy will be skipped.")
    HAS_REQUESTS = False

# Ensure screenshot directory exists
SCREENSHOT_DIR = os.path.join(os.getcwd(), 'screenshots')
os.makedirs(SCREENSHOT_DIR, exist_ok=True)

# Cookie file location
COOKIES_DIR = os.path.join(os.getcwd(), 'cookies')
os.makedirs(COOKIES_DIR, exist_ok=True)

# South African mobile user agents (high priority in South Africa)
SA_MOBILE_USER_AGENTS = [
    "Mozilla/5.0 (Linux; Android 12; SM-G998B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.6422.102 Mobile Safari/537.36", # Samsung Galaxy S21 Ultra
    "Mozilla/5.0 (Linux; Android 13; SM-S918B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.6422.102 Mobile Safari/537.36", # Samsung Galaxy S23 Ultra
    "Mozilla/5.0 (Linux; Android 12; Redmi Note 11) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.6422.102 Mobile Safari/537.36", # Xiaomi Redmi Note 11
    "Mozilla/5.0 (iPhone; CPU iPhone OS 16_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.0 Mobile/15E148 Safari/604.1" # iPhone
]

# South African desktop user agents
SA_DESKTOP_USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.6422.142 Safari/537.36", # Chrome latest
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.3 Safari/605.1.15", # Safari
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:125.0) Gecko/20100101 Firefox/125.0" # Firefox latest
]

# Combine with higher weight for mobile (more common in South Africa)
ALL_USER_AGENTS = SA_MOBILE_USER_AGENTS * 3 + SA_DESKTOP_USER_AGENTS * 2

def get_cookie_filename(url):
    """Generate a unique, consistent filename for storing cookies for a specific URL."""
    domain = urlparse(url).netloc
    sanitized_domain = domain.replace('.', '_')
    return os.path.join(COOKIES_DIR, f"{sanitized_domain}_cookies.json")

def save_cookies(url, cookies):
    """Save cookies to a file."""
    filename = get_cookie_filename(url)
    try:
        with open(filename, 'w') as f:
            json.dump(cookies, f)
        logger.info(f"Saved cookies to {filename}")
        return True
    except Exception as e:
        logger.error(f"Error saving cookies: {str(e)}")
        return False

def load_cookies(url):
    """Load cookies from a file if available."""
    filename = get_cookie_filename(url)
    if os.path.exists(filename):
        try:
            with open(filename, 'r') as f:
                cookies = json.load(f)
            logger.info(f"Loaded cookies from {filename}")
            return cookies
        except Exception as e:
            logger.error(f"Error loading cookies: {str(e)}")
    return None

def capture_with_playwright(url, lottery_type, save_to_db=True):
    """
    Capture a screenshot using Playwright with enhanced anti-bot measures.
    Specific customizations for the National Lottery website.
    
    Args:
        url (str): URL to capture
        lottery_type (str): Type of lottery
        save_to_db (bool): Whether to save to database
    
    Returns:
        tuple: (html_path, img_path, success)
    """
    if not HAS_PLAYWRIGHT:
        logger.error("Playwright not available")
        return None, None, False
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    html_path = None
    img_path = None
    success = False
    
    # Create consistent but unique filename
    safe_lottery_type = lottery_type.replace(' ', '_').replace('/', '_')
    filename_base = f"{safe_lottery_type}_{timestamp}_{uuid.uuid4().hex[:8]}"
    html_filename = os.path.join(SCREENSHOT_DIR, f"{filename_base}.html")
    img_filename = os.path.join(SCREENSHOT_DIR, f"{filename_base}.png")
    
    try:
        with sync_playwright() as p:
            # Use a persistent context to maintain cookies between sessions
            user_data_dir = os.path.join(COOKIES_DIR, safe_lottery_type)
            os.makedirs(user_data_dir, exist_ok=True)
            
            # Randomize browser selection (though Chromium is preferred for this site)
            # Use 90% chance of choosing Chromium as it works better with this site
            browser_choice = random.choices(
                ["chromium", "firefox", "webkit"], 
                weights=[9, 0.5, 0.5], 
                k=1
            )[0]
            
            # Random SA-based user agent
            user_agent = random.choice(ALL_USER_AGENTS)
            
            # Set up browser with SA-specific configurations
            browser_type = getattr(p, browser_choice)
            context_options = {
                "user_agent": user_agent,
                # National Lottery site doesn't work well with viewport smaller than 1000px wide
                "viewport": {"width": random.randint(1000, 1920), "height": random.randint(720, 1080)},
                "locale": "en-ZA",  # South African English
                "timezone_id": "Africa/Johannesburg",
                "geolocation": {"longitude": 28.0473, "latitude": -26.2041, "accuracy": 100},  # Johannesburg
                "permissions": ["geolocation"],
                "color_scheme": random.choice(["dark", "light", "no-preference"]),
                "device_scale_factor": random.choice([1, 1.5, 2]),
                "is_mobile": random.random() < 0.6,  # 60% chance of mobile (common in SA)
                "has_touch": random.random() < 0.7,  # 70% chance of touch (common in SA)
                "accept_downloads": False
            }
            
            # Launch browser with the above options
            browser = browser_type.launch(
                headless=True,
                slow_mo=random.randint(20, 50),  # Slow down actions
                args=[
                    "--disable-blink-features=AutomationControlled",
                    "--disable-features=IsolateOrigins,site-per-process", 
                    "--no-sandbox",
                    "--disable-dev-shm-usage",
                    "--disable-infobars",
                    "--ignore-certificate-errors"
                ]
            )
            
            # Create context with specified options
            context = browser.new_context(**context_options)
            
            # Add custom JavaScript to mask automation
            context.add_init_script("""
                // Hide automation flags
                Object.defineProperty(navigator, 'webdriver', {get: () => false});
                Object.defineProperty(navigator, 'languages', {get: () => ['en-ZA', 'en', 'af']});
                
                // Modify plugins to look more authentic
                Object.defineProperty(navigator, 'plugins', {
                    get: () => [
                        {name: 'PDF Viewer', filename: 'internal-pdf-viewer'}, 
                        {name: 'Chrome PDF Viewer', filename: 'pdf'},
                        {name: 'Google Docs', filename: 'docs'}
                    ]
                });
            """)
            
            # Create a new page
            page = context.new_page()
            
            # Set extra HTTP headers for South African appearance
            page.set_extra_http_headers({
                "Accept-Language": "en-ZA,en;q=0.9,af;q=0.8",
                "Sec-CH-UA-Platform": "Windows",
                "DNT": "1",
                "Upgrade-Insecure-Requests": "1",
                "Sec-Fetch-Dest": "document",
                "Sec-Fetch-Mode": "navigate",
                "Sec-Fetch-Site": "none",
                "Sec-Fetch-User": "?1",
                "Sec-CH-UA-Mobile": "?0"
            })
            
            # First navigate to the main domain to establish cookies
            main_domain = f"{urlparse(url).scheme}://{urlparse(url).netloc}"
            logger.info(f"First navigating to main domain: {main_domain}")
            
            try:
                # Use a safer navigation approach with multiple fallback strategies
                page.goto(main_domain, timeout=30000, wait_until="domcontentloaded")
                
                # Wait for the page to stabilize
                page.wait_for_timeout(random.randint(3000, 5000))
                
                # Check for cookie consent and accept if present (common on South African sites)
                for cookie_button_selector in [
                    "button:has-text('Accept')", 
                    "button:has-text('Accept All')",
                    "button:has-text('I Accept')",
                    "button:has-text('Allow')",
                    "#consent button",
                    "[id*='cookie'] button", 
                    "[class*='cookie'] button"
                ]:
                    try:
                        if page.query_selector(cookie_button_selector):
                            page.click(cookie_button_selector)
                            logger.info(f"Clicked cookie consent button: {cookie_button_selector}")
                            page.wait_for_timeout(random.randint(1000, 2000))
                            break
                    except Exception as e:
                        logger.debug(f"No cookie consent found with selector {cookie_button_selector}: {str(e)}")
                
                # Now perform natural scrolling behavior
                scroll_multiple_times(page)
                
                # Now navigate to the actual target URL
                logger.info(f"Now navigating to target URL: {url}")
                page.goto(url, wait_until="networkidle", timeout=60000)
                
                # Add more realistic user behavior - random scrolling and pauses
                scroll_multiple_times(page)
                
                # Check if we hit a CAPTCHA or blocking page
                if detect_blocking(page):
                    logger.warning(f"Detected CAPTCHA or blocking page for {url}")
                    # Save the CAPTCHA page for debugging
                    captcha_path = os.path.join(SCREENSHOT_DIR, f"captcha_{timestamp}.png")
                    page.screenshot(path=captcha_path)
                    return None, captcha_path, False
                
                # Extract and save HTML content
                html_content = page.content()
                with open(html_filename, 'w', encoding='utf-8') as f:
                    f.write(html_content)
                html_path = html_filename
                
                # Take screenshot
                page.screenshot(path=img_filename)
                img_path = img_filename
                
                # Save cookies for future sessions
                cookies = context.cookies()
                save_cookies(url, cookies)
                
                success = True
                logger.info(f"Successfully captured {lottery_type} from {url}")
                
            except Exception as e:
                logger.error(f"Error navigating to {url}: {str(e)}")
                # Try to take a screenshot of the error state for debugging
                try:
                    error_path = os.path.join(SCREENSHOT_DIR, f"error_{timestamp}.png")
                    page.screenshot(path=error_path)
                    logger.info(f"Saved error screenshot to {error_path}")
                except:
                    pass
            
            # Close resources
            page.close()
            context.close()
            browser.close()
    
    except Exception as e:
        logger.error(f"Error in Playwright capture: {str(e)}")
    
    # Save to database if requested and successful
    if save_to_db and success and html_path:
        try:
            from models import db, Screenshot
            from flask import current_app
            
            # Check if we're in a Flask context
            if not hasattr(current_app, 'app_context'):
                from main import app
                with app.app_context():
                    save_screenshot_to_database(url, lottery_type, html_path, img_path)
            else:
                save_screenshot_to_database(url, lottery_type, html_path, img_path)
        except Exception as e:
            logger.error(f"Error saving to database: {str(e)}")
    
    return html_path, img_path, success

def scroll_multiple_times(page):
    """Perform realistic scrolling behavior."""
    # Get page height
    page_height = page.evaluate('() => document.body.scrollHeight')
    viewport_height = page.viewport_size['height']
    
    # Number of scrolls needed
    scrolls_needed = max(1, page_height // viewport_height)
    
    # Perform scrolling with natural randomized behavior
    current_position = 0
    for i in range(scrolls_needed):
        # Random scroll amount (with some overlap)
        scroll_amount = random.randint(
            int(viewport_height * 0.7),
            int(viewport_height * 0.9)
        )
        
        # Update position
        current_position += scroll_amount
        if current_position > page_height:
            current_position = page_height
        
        # Scroll to position with smooth behavior
        page.evaluate(f'window.scrollTo({{top: {current_position}, behavior: "smooth"}})')
        
        # Random pause between scrolls to appear natural
        page.wait_for_timeout(random.randint(500, 2000))
        
        # Sometimes make small adjustments (like a human would)
        if random.random() < 0.3:  # 30% chance
            small_adjustment = random.randint(-100, 100)
            page.evaluate(f'window.scrollBy({{top: {small_adjustment}, behavior: "smooth"}})')
            page.wait_for_timeout(random.randint(300, 800))
    
    # Scroll back to top occasionally
    if random.random() < 0.4:  # 40% chance
        page.evaluate('window.scrollTo({top: 0, behavior: "smooth"})')
        page.wait_for_timeout(random.randint(1000, 2000))

def detect_blocking(page):
    """
    Detect if we've been blocked or shown a CAPTCHA.
    Returns True if blocking is detected.
    """
    # Check for common Cloudflare challenge elements
    cloudflare_selectors = [
        "#challenge-running",
        "#challenge-form",
        "title:has-text('Attention Required')",
        "title:has-text('Please Wait')"
    ]
    
    # Check for National Lottery specific error messages
    nl_error_selectors = [
        "div:has-text('Oops! Something went wrong')",
        "div[class*='captcha']",
        "div[class*='error']",
        "img[src*='error']"
    ]
    
    # Combine all selectors
    all_selectors = cloudflare_selectors + nl_error_selectors
    
    # Check each selector
    for selector in all_selectors:
        try:
            if page.query_selector(selector):
                logger.warning(f"Blocking detected: found selector '{selector}'")
                return True
        except:
            pass
    
    # Also check page title for error indicators
    try:
        title = page.title().lower()
        error_title_keywords = ["error", "captcha", "security check", "attention", "challenge"]
        if any(keyword in title for keyword in error_title_keywords):
            logger.warning(f"Blocking detected: error in page title '{title}'")
            return True
    except:
        pass
    
    # Also check URL for redirects to error pages
    try:
        current_url = page.url.lower()
        error_url_keywords = ["captcha", "challenge", "attention", "error", "security", "cloudflare"]
        if any(keyword in current_url for keyword in error_url_keywords):
            logger.warning(f"Blocking detected: error in URL '{current_url}'")
            return True
    except:
        pass
    
    # Check for very small page content which might indicate an error
    try:
        content_length = len(page.content())
        if content_length < 5000:  # Suspiciously small content
            logger.warning(f"Possibly blocked: very small page content (length: {content_length})")
            return True
    except:
        pass
    
    return False

def save_screenshot_to_database(url, lottery_type, html_path, img_path=None):
    """Save screenshot information to the database."""
    try:
        from models import db, Screenshot
        
        # Check if a record already exists for this URL
        existing = Screenshot.query.filter_by(url=url).first()
        
        if existing:
            # Update existing record
            existing.path = html_path
            existing.image_path = img_path
            existing.timestamp = datetime.now()
            logger.info(f"Updated existing screenshot record for {lottery_type}")
        else:
            # Create new record
            screenshot = Screenshot(
                url=url,
                lottery_type=lottery_type,
                path=html_path,
                image_path=img_path,
                timestamp=datetime.now()
            )
            db.session.add(screenshot)
        
        db.session.commit()
        logger.info(f"Saved screenshot to database: {lottery_type}")
        return True
    except Exception as e:
        logger.error(f"Error saving screenshot to database: {str(e)}")
        return False

def capture_with_undetected_chromedriver(url, lottery_type, save_to_db=True):
    """
    Capture a screenshot using undetected_chromedriver with enhanced anti-bot measures.
    
    Args:
        url (str): URL to capture
        lottery_type (str): Type of lottery
        save_to_db (bool): Whether to save to database
        
    Returns:
        tuple: (html_path, img_path, success)
    """
    if not HAS_UNDETECTED_CHROMEDRIVER:
        logger.error("undetected_chromedriver not available")
        return None, None, False
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    html_path = None
    img_path = None
    success = False
    
    # Create consistent but unique filename
    safe_lottery_type = lottery_type.replace(' ', '_').replace('/', '_')
    filename_base = f"{safe_lottery_type}_{timestamp}_{uuid.uuid4().hex[:8]}"
    html_filename = os.path.join(SCREENSHOT_DIR, f"{filename_base}.html")
    img_filename = os.path.join(SCREENSHOT_DIR, f"{filename_base}.png")
    
    # Random SA user agent
    user_agent = random.choice(ALL_USER_AGENTS)
    
    driver = None
    try:
        # Use undetected_chromedriver to bypass detection
        options = uc.ChromeOptions()
        
        # Add general anti-detection measures
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_argument("--disable-features=IsolateOrigins,site-per-process")
        options.add_argument("--disable-gpu")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-infobars")
        options.add_argument("--ignore-certificate-errors")
        
        # Set window size (optimal for this website)
        options.add_argument(f"--window-size={random.randint(1000, 1920)},{random.randint(720, 1080)}")
        
        # Set user agent
        options.add_argument(f"--user-agent={user_agent}")
        
        # Set South African language and locale
        options.add_argument("--lang=en-ZA")
        options.add_argument("--accept-lang=en-ZA,en;q=0.9,af;q=0.8")
        
        # Create user data directory for cookies
        user_data_dir = os.path.join(COOKIES_DIR, f"chrome_{safe_lottery_type}")
        os.makedirs(user_data_dir, exist_ok=True)
        options.add_argument(f"--user-data-dir={user_data_dir}")
        
        # Attempt to find Chrome on the system
        chrome_binary = None
        possible_paths = [
            "/usr/bin/google-chrome",
            "/usr/bin/google-chrome-stable",
            "/usr/bin/chromium",
            "/usr/bin/chromium-browser",
            "/nix/store/chromium",  # Common Replit location
        ]
        
        # Try to find Chrome in standard locations
        for path in possible_paths:
            if os.path.exists(path):
                chrome_binary = path
                logger.info(f"Found Chrome binary at {path}")
                break
            
            # Also try with wildcard matching for nix store paths
            if path.startswith("/nix/store"):
                import glob
                matches = glob.glob("/nix/store/*chromium*/bin/chromium")
                if matches:
                    chrome_binary = matches[0]
                    logger.info(f"Found Chrome binary at {chrome_binary}")
                    break
        
        # Try to find Chrome/Chromium in the PATH
        if not chrome_binary:
            try:
                import subprocess
                chrome_path = subprocess.check_output("which chromium || which google-chrome || which chromium-browser", shell=True).decode().strip()
                if chrome_path:
                    chrome_binary = chrome_path
                    logger.info(f"Found Chrome binary in PATH: {chrome_binary}")
            except:
                pass
        
        # If Chrome binary was found, set it in options
        if chrome_binary:
            options.binary_location = chrome_binary
        
        # Initialize driver with enhanced stealth measures
        driver = uc.Chrome(options=options, use_subprocess=True)
        driver.set_page_load_timeout(60)
        
        # First navigate to the main domain to establish cookies
        main_domain = f"{urlparse(url).scheme}://{urlparse(url).netloc}"
        logger.info(f"First navigating to main domain: {main_domain}")
        driver.get(main_domain)
        
        # Wait for the page to load and handle any cookie consent
        time.sleep(random.uniform(3, 5))
        
        # Try different selectors for cookie consent buttons
        try:
            # First try clicking by regular CSS selectors
            consent_selectors = [
                "#onetrust-accept-btn-handler",  # Common OneTrust button
                ".accept-cookies-button",
                ".cookie-consent-accept",
                ".js-accept-cookies",
                "#cookie-accept",
                "#consent-accept",
                ".consent-agree",
                "button.accept",
                "[id*='cookie'] button", 
                "[class*='cookie'] button",
                "[id*='consent'] button", 
                "[class*='consent'] button"
            ]
            
            for selector in consent_selectors:
                try:
                    elements = driver.find_elements(By.CSS_SELECTOR, selector)
                    if elements and len(elements) > 0:
                        elements[0].click()
                        logger.info(f"Clicked cookie consent button with CSS selector: {selector}")
                        time.sleep(random.uniform(1, 2))
                        break
                except Exception as e:
                    logger.debug(f"Error with CSS selector {selector}: {str(e)}")
            
            # Then try XPath selectors which can search by text
            xpath_selectors = [
                "//button[contains(text(), 'Accept')]",
                "//button[contains(text(), 'Accept All')]",
                "//button[contains(text(), 'I Accept')]",
                "//button[contains(text(), 'Agree')]",
                "//button[contains(text(), 'Allow')]",
                "//button[contains(text(), 'OK')]"
            ]
            
            for xpath in xpath_selectors:
                try:
                    elements = driver.find_elements(By.XPATH, xpath)
                    if elements and len(elements) > 0:
                        elements[0].click()
                        logger.info(f"Clicked cookie consent button with XPath: {xpath}")
                        time.sleep(random.uniform(1, 2))
                        break
                except Exception as e:
                    logger.debug(f"Error with XPath {xpath}: {str(e)}")
                    
        except Exception as e:
            logger.debug(f"Error handling cookies: {str(e)}")
        
        # Perform natural scrolling behavior
        natural_scroll_behavior(driver)
        
        # Now navigate to the actual target URL
        logger.info(f"Now navigating to target URL: {url}")
        driver.get(url)
        
        # Wait for the page to load
        time.sleep(random.uniform(5, 8))
        
        # Add more realistic user behavior - random scrolling and pauses
        natural_scroll_behavior(driver)
        
        # Check for CAPTCHA or blocking
        if detect_blocking_selenium(driver):
            logger.warning(f"Detected CAPTCHA or blocking page for {url}")
            # Save the CAPTCHA page for debugging
            captcha_path = os.path.join(SCREENSHOT_DIR, f"captcha_{timestamp}.png")
            driver.save_screenshot(captcha_path)
            return None, captcha_path, False
        
        # Extract and save HTML content
        html_content = driver.page_source
        with open(html_filename, 'w', encoding='utf-8') as f:
            f.write(html_content)
        html_path = html_filename
        
        # Take screenshot
        driver.save_screenshot(img_filename)
        img_path = img_filename
        
        # Save cookies for future sessions
        cookies = driver.get_cookies()
        save_cookies(url, cookies)
        
        success = True
        logger.info(f"Successfully captured {lottery_type} from {url}")
        
    except Exception as e:
        logger.error(f"Error in undetected_chromedriver capture: {str(e)}")
        # Try to take a screenshot of the error state for debugging
        if driver:
            try:
                error_path = os.path.join(SCREENSHOT_DIR, f"error_{timestamp}.png")
                driver.save_screenshot(error_path)
                logger.info(f"Saved error screenshot to {error_path}")
            except:
                pass
    
    finally:
        # Close the driver
        if driver:
            try:
                driver.quit()
            except:
                pass
    
    # Save to database if requested and successful
    if save_to_db and success and html_path:
        try:
            from models import db, Screenshot
            from flask import current_app
            
            # Check if we're in a Flask context
            if not hasattr(current_app, 'app_context'):
                from main import app
                with app.app_context():
                    save_screenshot_to_database(url, lottery_type, html_path, img_path)
            else:
                save_screenshot_to_database(url, lottery_type, html_path, img_path)
        except Exception as e:
            logger.error(f"Error saving to database: {str(e)}")
    
    return html_path, img_path, success

def natural_scroll_behavior(driver):
    """Implement natural scrolling behavior for Selenium."""
    try:
        # Get page height
        total_height = driver.execute_script("return document.body.scrollHeight")
        viewport_height = driver.execute_script("return window.innerHeight")
        
        # Number of scrolls needed
        scrolls_needed = max(1, total_height // viewport_height)
        
        # Perform scrolling with natural randomized behavior
        current_position = 0
        for i in range(scrolls_needed):
            # Random scroll amount (with some overlap)
            scroll_amount = random.randint(
                int(viewport_height * 0.7),
                int(viewport_height * 0.9)
            )
            
            # Update position
            current_position += scroll_amount
            if current_position > total_height:
                current_position = total_height
            
            # Scroll to position with smooth behavior
            driver.execute_script(f"window.scrollTo({{top: {current_position}, behavior: 'smooth'}})")
            
            # Random pause between scrolls to appear natural
            time.sleep(random.uniform(0.5, 2.0))
            
            # Sometimes make small adjustments (like a human would)
            if random.random() < 0.3:  # 30% chance
                small_adjustment = random.randint(-100, 100)
                driver.execute_script(f"window.scrollBy({{top: {small_adjustment}, behavior: 'smooth'}})")
                time.sleep(random.uniform(0.3, 0.8))
        
        # Scroll back to top occasionally
        if random.random() < 0.4:  # 40% chance
            driver.execute_script("window.scrollTo({top: 0, behavior: 'smooth'})")
            time.sleep(random.uniform(1.0, 2.0))
            
    except Exception as e:
        logger.error(f"Error in natural scroll behavior: {str(e)}")

def detect_blocking_selenium(driver):
    """
    Detect if we've been blocked or shown a CAPTCHA using Selenium.
    Returns True if blocking is detected.
    """
    try:
        # Check for common Cloudflare challenge elements
        cloudflare_selectors = [
            "#challenge-running",
            "#challenge-form",
        ]
        
        # Check for National Lottery specific error messages
        nl_error_selectors = [
            "//div[contains(text(), 'Oops! Something went wrong')]",
            "//div[contains(@class, 'captcha')]",
            "//div[contains(@class, 'error')]",
            "//img[contains(@src, 'error')]"
        ]
        
        # Check each CSS selector
        for selector in cloudflare_selectors:
            try:
                if driver.find_elements(By.CSS_SELECTOR, selector):
                    logger.warning(f"Blocking detected: found CSS selector '{selector}'")
                    return True
            except:
                pass
                
        # Check each XPath selector
        for selector in nl_error_selectors:
            try:
                if driver.find_elements(By.XPATH, selector):
                    logger.warning(f"Blocking detected: found XPath selector '{selector}'")
                    return True
            except:
                pass
        
        # Also check page title for error indicators
        try:
            title = driver.title.lower()
            error_title_keywords = ["error", "captcha", "security check", "attention", "challenge"]
            if any(keyword in title for keyword in error_title_keywords):
                logger.warning(f"Blocking detected: error in page title '{title}'")
                return True
        except:
            pass
        
        # Also check URL for redirects to error pages
        try:
            current_url = driver.current_url.lower()
            error_url_keywords = ["captcha", "challenge", "attention", "error", "security", "cloudflare"]
            if any(keyword in current_url for keyword in error_url_keywords):
                logger.warning(f"Blocking detected: error in URL '{current_url}'")
                return True
        except:
            pass
        
        # Check for very small page content which might indicate an error
        try:
            content_length = len(driver.page_source)
            if content_length < 5000:  # Suspiciously small content
                logger.warning(f"Possibly blocked: very small page content (length: {content_length})")
                return True
        except:
            pass
        
        return False
    except Exception as e:
        logger.error(f"Error in detect_blocking_selenium: {str(e)}")
        return False

def capture_national_lottery_url(url, lottery_type, save_to_db=True, method_index=None):
    """
    Main capture function with multiple fallback strategies.
    
    Args:
        url (str): URL to capture
        lottery_type (str): Type of lottery
        save_to_db (bool): Whether to save to database
        method_index (int, optional): If provided, use a specific method:
                                      0 = undetected_chromedriver
                                      1 = playwright
                                      2 = requests
        
    Returns:
        tuple: (success, html_path, img_path)
    """
    logger.info(f"Attempting to capture {lottery_type} from {url}")
    
    # If a specific method is requested, use only that method
    if method_index is not None:
        if method_index == 0 and HAS_UNDETECTED_CHROMEDRIVER:
            logger.info(f"Using undetected_chromedriver method (index 0)")
            html_path, img_path, success = capture_with_undetected_chromedriver(url, lottery_type, save_to_db=False)
            if success and save_to_db:
                save_screenshot_to_database(url, lottery_type, html_path, img_path)
            return success, html_path, img_path
        elif method_index == 1 and HAS_PLAYWRIGHT:
            logger.info(f"Using playwright method (index 1)")
            html_path, img_path, success = capture_with_playwright(url, lottery_type, save_to_db=False)
            if success and save_to_db:
                save_screenshot_to_database(url, lottery_type, html_path, img_path)
            return success, html_path, img_path
        elif method_index == 2 and HAS_REQUESTS:
            logger.info(f"Using requests method (index 2)")
            try:
                # Generate a realistic user agent
                user_agent = random.choice(ALL_USER_AGENTS)
                
                # Set up headers with South African fingerprints
                headers = {
                    'User-Agent': user_agent,
                    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
                    'Accept-Language': 'en-ZA,en-GB;q=0.9,en-US;q=0.8,en;q=0.7',
                    'Accept-Encoding': 'gzip, deflate, br',
                    'Referer': 'https://www.google.co.za/',
                    'Connection': 'keep-alive',
                    'Upgrade-Insecure-Requests': '1',
                    'Sec-Fetch-Dest': 'document',
                    'Sec-Fetch-Mode': 'navigate',
                    'Sec-Fetch-Site': 'cross-site',
                    'Sec-Fetch-User': '?1',
                    'DNT': '1',
                }
                
                # Load cookies if available
                cookies = load_cookies(url)
                
                # Make the request with a timeout
                response = requests.get(url, headers=headers, cookies=cookies, timeout=30)
                
                if response.status_code == 200:
                    # Save the HTML content
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    safe_lottery_type = lottery_type.replace(' ', '_').replace('/', '_')
                    filename_base = f"{safe_lottery_type}_{timestamp}_{uuid.uuid4().hex[:8]}"
                    html_path = os.path.join(SCREENSHOT_DIR, f"{filename_base}.html")
                    
                    with open(html_path, 'w', encoding='utf-8') as f:
                        f.write(response.text)
                    
                    # Save to database if requested
                    if save_to_db:
                        save_screenshot_to_database(url, lottery_type, html_path)
                    
                    logger.info(f"Successfully captured with requests")
                    return True, html_path, None
                else:
                    logger.error(f"Request failed with status code {response.status_code}")
                    return False, None, None
            except Exception as e:
                logger.error(f"Error in requests capture: {str(e)}")
                return False, None, None
    
    # Otherwise, try undetected_chromedriver first (we know it's installed)
    if HAS_UNDETECTED_CHROMEDRIVER:
        logger.info(f"Trying capture with undetected_chromedriver")
        html_path, img_path, success = capture_with_undetected_chromedriver(url, lottery_type, save_to_db=False)
        if success:
            logger.info(f"Successfully captured with undetected_chromedriver")
            if save_to_db:
                save_screenshot_to_database(url, lottery_type, html_path, img_path)
            return True, html_path, img_path
    
    # If undetected_chromedriver fails and Playwright is available, try it
    if HAS_PLAYWRIGHT:
        logger.info(f"Trying capture with Playwright")
        html_path, img_path, success = capture_with_playwright(url, lottery_type, save_to_db=False)
        if success:
            logger.info(f"Successfully captured with Playwright")
            if save_to_db:
                save_screenshot_to_database(url, lottery_type, html_path, img_path)
            return True, html_path, img_path
    
    # If all browser strategies fail, try with requests as a final fallback
    if HAS_REQUESTS:
        try:
            logger.info(f"Trying capture with requests as final fallback")
            
            # Generate a realistic user agent
            user_agent = random.choice(ALL_USER_AGENTS)
            
            # Set up headers with South African fingerprints
            headers = {
                'User-Agent': user_agent,
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
                'Accept-Language': 'en-ZA,en-GB;q=0.9,en-US;q=0.8,en;q=0.7',
                'Accept-Encoding': 'gzip, deflate, br',
                'Referer': 'https://www.google.co.za/',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1',
                'Sec-Fetch-Dest': 'document',
                'Sec-Fetch-Mode': 'navigate',
                'Sec-Fetch-Site': 'cross-site',
                'Sec-Fetch-User': '?1',
                'DNT': '1',
            }
            
            # Load cookies if available
            cookies = load_cookies(url)
            
            # Make the request with a timeout
            response = requests.get(url, headers=headers, cookies=cookies, timeout=30)
            
            if response.status_code == 200:
                # Save the HTML content
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                safe_lottery_type = lottery_type.replace(' ', '_').replace('/', '_')
                filename_base = f"{safe_lottery_type}_{timestamp}_{uuid.uuid4().hex[:8]}"
                html_path = os.path.join(SCREENSHOT_DIR, f"{filename_base}.html")
                
                with open(html_path, 'w', encoding='utf-8') as f:
                    f.write(response.text)
                
                # Save to database if requested
                if save_to_db:
                    save_screenshot_to_database(url, lottery_type, html_path)
                
                logger.info(f"Successfully captured with requests")
                return True, html_path, None
            else:
                logger.error(f"Request failed with status code {response.status_code}")
        except Exception as e:
            logger.error(f"Error in requests capture: {str(e)}")
    
    # All strategies failed
    logger.error(f"Failed to capture {lottery_type} from {url} with all available strategies")
    return False, None, None

# Usage example:
# success, html_path, img_path = capture_national_lottery_url(
#    "https://www.nationallottery.co.za/results/lotto", "Lotto Results")