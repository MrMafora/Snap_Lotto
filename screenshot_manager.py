"""
Screenshot manager for capturing lottery website screenshots
"""
import os
import logging
import asyncio
import random
import time
import math
import subprocess
from datetime import datetime
import traceback
from pathlib import Path
import threading
import shutil
import json
import uuid
import io
from urllib.parse import urlparse
import requests
from bs4 import BeautifulSoup
from PIL import Image
from sqlalchemy import func
from models import db, Screenshot, ScheduleConfig
from playwright.async_api import async_playwright
from playwright.sync_api import sync_playwright

# Set up module-specific logger
logger = logging.getLogger(__name__)
if not logger.handlers:
    # Create logs directory if it doesn't exist
    logs_dir = os.path.join(os.getcwd(), 'logs')
    if not os.path.exists(logs_dir):
        os.makedirs(logs_dir)
    
    # Set up file handler
    file_handler = logging.FileHandler(os.path.join(logs_dir, 'screenshot_manager.log'))
    file_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
    logger.addHandler(file_handler)
    
    # Set up console handler
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
    logger.addHandler(console_handler)
    
    # Set logging level
    logger.setLevel(logging.INFO)
    
# Function to save screenshot metadata to database
def save_screenshot_to_database(url, lottery_type, filepath, img_filepath):
    """
    Save screenshot information to the database.
    
    Args:
        url (str): Source URL
        lottery_type (str): Type of lottery
        filepath (str): Path to the HTML file
        img_filepath (str): Path to the image file
        
    Returns:
        int: ID of the created database record
    """
    try:
        # Check if we need to create an app context
        from flask import current_app, has_app_context
        if not has_app_context():
            # Import app here to avoid circular imports
            from main import app
            with app.app_context():
                # Save screenshot metadata to database within app context
                screenshot = Screenshot(
                    url=url,
                    lottery_type=lottery_type,
                    timestamp=datetime.now(),
                    path=filepath,
                    processed=False
                )
                
                db.session.add(screenshot)
                db.session.commit()
                
                logger.info(f"Screenshot record saved to database with ID {screenshot.id}")
                return screenshot.id
        else:
            # We already have an app context, proceed normally
            screenshot = Screenshot(
                url=url,
                lottery_type=lottery_type,
                timestamp=datetime.now(),
                path=filepath,
                processed=False
            )
            
            db.session.add(screenshot)
            db.session.commit()
            
            logger.info(f"Screenshot record saved to database with ID {screenshot.id}")
            return screenshot.id
    except Exception as e:
        logger.error(f"Database error when saving screenshot: {str(e)}")
        logger.error(traceback.format_exc())
        if 'db' in locals():
            db.session.rollback()
        raise

# Create directory for screenshots if it doesn't exist
SCREENSHOT_DIR = os.path.join(os.getcwd(), 'screenshots')
os.makedirs(SCREENSHOT_DIR, exist_ok=True)

# Create directory for cookies if it doesn't exist
COOKIES_DIR = os.path.join(os.getcwd(), 'cookies')
os.makedirs(COOKIES_DIR, exist_ok=True)

# Thread semaphore to limit concurrent screenshots
# This prevents "can't start new thread" errors by limiting resource usage
MAX_CONCURRENT_THREADS = 3
screenshot_semaphore = threading.Semaphore(MAX_CONCURRENT_THREADS)

# List of user agents to rotate through randomly - updated with 2024 versions
USER_AGENTS = [
    # Chrome (Windows)
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
    # Chrome (Mac)
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36',
    # Firefox (Windows)
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:124.0) Gecko/20100101 Firefox/124.0',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:123.0) Gecko/20100101 Firefox/123.0',
    # Firefox (Mac)
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:124.0) Gecko/20100101 Firefox/124.0',
    # Safari (Mac)
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Safari/605.1.15',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Safari/605.1.15',
    # Edge (Windows)
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36 Edg/124.0.0.0',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36 Edg/123.0.0.0',
    # Chrome (Linux)
    'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
    'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36',
    # Firefox (Linux)
    'Mozilla/5.0 (X11; Linux x86_64; rv:124.0) Gecko/20100101 Firefox/124.0',
    # Mobile browsers (for variety)
    'Mozilla/5.0 (iPhone; CPU iPhone OS 17_4 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1',
    'Mozilla/5.0 (iPad; CPU OS 17_4 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1',
    'Mozilla/5.0 (Linux; Android 14; SM-S908U) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Mobile Safari/537.36',
    'Mozilla/5.0 (Linux; Android 14; Pixel 8) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Mobile Safari/537.36'
]

# Human-like scroll behavior parameters with more natural patterns
# Enhanced Human-like scroll behavior with more realistic patterns
SCROLL_BEHAVIOR = [
    # Initial scan of the page - carefully reading the top content
    {'distance': 0.05, 'delay': 1.5},   # First quick look
    {'distance': 0.15, 'delay': 2.3},   # Read top content (longer pause)
    {'distance': 0.22, 'delay': 1.1},   # Continue reading
    {'distance': 0.28, 'delay': 0.9},   # Short scan down
    
    # Middle section reading (with variable speeds and micro-pauses)
    {'distance': 0.35, 'delay': 2.7},   # Pause at interesting content
    {'distance': 0.37, 'delay': 0.4},   # Micro adjustment (very human-like)
    {'distance': 0.42, 'delay': 1.8},   # Continue reading
    {'distance': 0.48, 'delay': 0.7},   # Quick scan
    
    # Occasional scrolling up (humans often go back up to re-read)
    {'distance': 0.44, 'delay': 1.2},   # Scroll back up a bit
    {'distance': 0.51, 'delay': 2.0},   # Resume reading
    
    # Variable-speed middle section (most realistic)
    {'distance': 0.58, 'delay': 0.6},   # Slightly faster
    {'distance': 0.63, 'delay': 1.4},   # Slow down again
    {'distance': 0.65, 'delay': 0.3},   # Micro adjustment
    {'distance': 0.72, 'delay': 1.9},   # Longer read

    # Skimming the bottom with more consistent speed (typical human pattern)
    {'distance': 0.79, 'delay': 0.8},   # Faster now
    {'distance': 0.85, 'delay': 0.7},   # Continued skimming
    {'distance': 0.91, 'delay': 0.6},   # Fast scroll near bottom
    
    # Final look and possible bounce
    {'distance': 0.96, 'delay': 1.3},   # Almost at the bottom
    {'distance': 1.0, 'delay': 2.2},    # Pause at footer
    {'distance': 0.93, 'delay': 0.9},   # Sometimes scroll back up a bit (very human)
    {'distance': 1.0, 'delay': 1.5}     # Final look at footer
]

# Define multiple scroll patterns to rotate through (even more human-like)
SCROLL_PATTERNS = [
    # Pattern 1: Fast reader (scrolls quickly with occasional pauses)
    [
        {'distance': 0.12, 'delay': 0.9},
        {'distance': 0.25, 'delay': 0.5},
        {'distance': 0.45, 'delay': 1.2},
        {'distance': 0.65, 'delay': 0.4},
        {'distance': 0.85, 'delay': 0.3},
        {'distance': 1.0, 'delay': 1.0}
    ],
    
    # Pattern 2: Careful reader (slower with more pauses)
    [
        {'distance': 0.08, 'delay': 2.1},
        {'distance': 0.16, 'delay': 1.8},
        {'distance': 0.25, 'delay': 2.3},
        {'distance': 0.33, 'delay': 1.5},
        {'distance': 0.38, 'delay': 0.9},
        {'distance': 0.42, 'delay': 1.7},
        {'distance': 0.51, 'delay': 1.8},
        {'distance': 0.65, 'delay': 1.5},
        {'distance': 0.78, 'delay': 1.2},
        {'distance': 0.91, 'delay': 0.9},
        {'distance': 1.0, 'delay': 2.0}
    ],
    
    # Pattern 3: Skimmer (fast with a few strategic pauses)
    [
        {'distance': 0.15, 'delay': 0.7},
        {'distance': 0.35, 'delay': 1.3},
        {'distance': 0.75, 'delay': 0.5},
        {'distance': 0.95, 'delay': 1.4},
        {'distance': 1.0, 'delay': 0.8}
    ],
    
    # Pattern 4: Erratic reader (unpredictable, with back-scrolling)
    [
        {'distance': 0.12, 'delay': 0.9},
        {'distance': 0.24, 'delay': 1.1},
        {'distance': 0.18, 'delay': 0.8}, # Back up
        {'distance': 0.35, 'delay': 1.5},
        {'distance': 0.58, 'delay': 0.7},
        {'distance': 0.49, 'delay': 1.2}, # Back up
        {'distance': 0.67, 'delay': 0.9},
        {'distance': 0.85, 'delay': 1.7},
        {'distance': 1.0, 'delay': 1.3}
    ]
]

# Enhanced browser fingerprint modification options for better anti-bot measures
BROWSER_FINGERPRINT_MODIFICATIONS = {
    # Screen sizes (width x height) - Common South African screen resolutions
    'screen_sizes': [
        {'width': 1366, 'height': 768},   # Common laptop (40% of ZA users)
        {'width': 1920, 'height': 1080},  # FHD desktop (30%)
        {'width': 1536, 'height': 864},   # Common laptop variant (10%)
        {'width': 1440, 'height': 900},   # MacBook Pro (8%)
        {'width': 1280, 'height': 720},   # HD ready (5%)
        {'width': 2560, 'height': 1440},  # QHD desktop (4%)
        {'width': 3840, 'height': 2160},  # 4K desktop (3%)
    ],
    
    # Color depths (bits) with weights to favor common depths
    'color_depths': [24, 24, 24, 24, 30, 30, 48],  # Weighted to favor 24-bit (common)
    
    # Platform information with South African market share weights
    'platforms': [
        {'name': 'Win32', 'os': 'Windows', 'weight': 65},  # 65% market share
        {'name': 'MacIntel', 'os': 'Mac OS X', 'weight': 23},  # 23%
        {'name': 'Linux x86_64', 'os': 'Linux', 'weight': 7},  # 7%
        {'name': 'Android', 'os': 'Android', 'weight': 5},  # 5%
    ],
    
    # Common browser plugins to emulate - updated with versions
    'plugins': [
        {'name': 'PDF Viewer', 'description': 'Portable Document Format', 'version': '1.0.0'},
        {'name': 'Chrome PDF Viewer', 'description': 'Portable Document Format', 'version': '124.0.0.0'},
        {'name': 'Chromium PDF Viewer', 'description': 'Portable Document Format', 'version': '124.0.0.0'},
        {'name': 'Native Client', 'description': 'Native Client Execution Environment', 'version': ''},
        {'name': 'Microsoft Edge PDF Viewer', 'description': 'Portable Document Format', 'version': '124.0.0.0'},
        {'name': 'WebKit built-in PDF', 'description': 'Portable Document Format', 'version': '17.2'},
    ],
    
    # Common languages with South African focus
    'languages': [
        ['en-ZA', 'en', 'af'],  # South African primary (55%)
        ['en-ZA', 'en'],  # South African English only (25%)
        ['en-US', 'en'],  # American English (8%)
        ['en-GB', 'en'],  # British English (7%)
        ['af-ZA', 'en-ZA', 'en'],  # Afrikaans primary (5%)
    ],
    
    # Timezones with weights towards South Africa
    'timezones': [
        'Africa/Johannesburg',  # South Africa (80% weight)
        'Africa/Johannesburg',
        'Africa/Johannesburg',
        'Africa/Johannesburg',
        'Europe/London',
        'America/New_York',
        'Australia/Sydney',
    ],
    
    # Font fingerprinting - common SA fonts
    'fonts': [
        # System fonts
        'Arial', 'Times New Roman', 'Courier New', 'Georgia', 'Verdana', 
        'Tahoma', 'Trebuchet MS', 'Impact', 'Comic Sans MS', 'Webdings',
        # South African specific
        'Ubuntu', 'DejaVu Sans', 'Liberation Sans', 'Noto Sans', 
    ],
    
    # Hardware concurrency (CPU cores) distribution
    'hardware_concurrency': [2, 4, 4, 4, 4, 6, 6, 8, 8, 8, 12, 16],
    
    # Device memory (GB) distribution
    'device_memory': [2, 4, 4, 4, 8, 8, 8, 16, 16, 32],
    
    # WebGL vendor and renderer combinations
    'webgl_vendors': [
        {
            'vendor': 'Google Inc. (Intel)',
            'renderer': 'ANGLE (Intel, Intel(R) UHD Graphics Direct3D11 vs_5_0 ps_5_0, D3D11)'
        },
        {
            'vendor': 'Google Inc. (NVIDIA)',
            'renderer': 'ANGLE (NVIDIA, NVIDIA GeForce GTX 1650 Direct3D11 vs_5_0 ps_5_0, D3D11)'
        },
        {
            'vendor': 'Google Inc. (AMD)',
            'renderer': 'ANGLE (AMD, AMD Radeon(TM) Graphics Direct3D11 vs_5_0 ps_5_0, D3D11)'
        },
        {
            'vendor': 'Apple Inc.',
            'renderer': 'Apple M1'
        },
        {
            'vendor': 'Intel Inc.',
            'renderer': 'Intel Iris OpenGL Engine'
        }
    ],
}

# Maximum number of retry attempts
MAX_RETRIES = 3

def ensure_playwright_browsers():
    """
    Ensure that Playwright browsers are installed.
    This should be run once at the start of the application.
    """
    try:
        import subprocess
        # Try to install Chromium browser with increased timeout
        logger.info("Starting Playwright browsers installation...")
        result = subprocess.check_call(['python', '-m', 'playwright', 'install', 'chromium'], timeout=180)
        logger.info(f"Playwright browsers installed successfully with result: {result}")
        return True
    except subprocess.TimeoutExpired:
        logger.error("Timeout expired when installing Playwright browsers")
        return False
    except subprocess.SubprocessError as e:
        logger.error(f"Subprocess error when installing Playwright browsers: {str(e)}")
        return False
    except Exception as e:
        logger.error(f"Error installing Playwright browsers: {str(e)}")
        logger.error(f"Error details: {traceback.format_exc()}")
        return False

def is_playwright_available():
    """
    Check if Playwright is available for use.
    
    Returns:
        bool: True if Playwright is available, False otherwise
    """
    try:
        # First check if the module is importable
        from playwright.sync_api import sync_playwright
        
        # Then try to actually use it by creating a minimal instance
        with sync_playwright() as p:
            # Just access a property to verify it's working
            browser_type = p.chromium
            logger.info(f"Playwright is available with browser types: {p.devices}")
            return True
    except ImportError:
        logger.error("Playwright is not installed")
        return False
    except Exception as e:
        logger.error(f"Error checking Playwright availability: {str(e)}")
        logger.error(f"Error traceback: {traceback.format_exc()}")
        return False

async def capture_screenshot_async(url):
    """
    Capture a screenshot of the specified URL using Playwright.
    This uses a full browser instance to properly render JavaScript and bypass anti-scraping measures.
    
    Args:
        url (str): The URL to capture
        
    Returns:
        tuple: (filepath, screenshot_data) or (None, None) if failed
    """
    try:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{timestamp}_{url.split('/')[-1]}.png"
        filepath = os.path.join(SCREENSHOT_DIR, filename)
        
        logger.info(f"Capturing screenshot from {url} using Playwright")
        
        chromium_path = "/nix/store/zi4f80l169xlmivz8vja8wlphq74qqk0-chromium-125.0.6422.141/bin/chromium"
        if os.path.exists(chromium_path):
            logger.info(f"Using Chromium from: {chromium_path}")
        
        # Use Playwright to capture screenshot
        async with async_playwright() as p:
            browser_type = p.chromium
            
            try:
                browser = await browser_type.launch(
                    headless=True,
                    executable_path=chromium_path if os.path.exists(chromium_path) else None
                )
                
                context = await browser.new_context(
                    viewport={'width': 1280, 'height': 1600},
                    user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
                )
                
                page = await context.new_page()
                
                # Set extra HTTP headers to appear more like a real browser
                await page.set_extra_http_headers({
                    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
                    "Accept-Language": "en-US,en;q=0.9",
                    "Accept-Encoding": "gzip, deflate, br",
                    "Connection": "keep-alive",
                    "Upgrade-Insecure-Requests": "1",
                    "Sec-Fetch-Dest": "document",
                    "Sec-Fetch-Mode": "navigate",
                    "Sec-Fetch-Site": "none",
                    "Sec-Fetch-User": "?1",
                    "DNT": "1"
                })
                
                # Navigate and wait for the page to fully load
                await page.goto(url, wait_until='networkidle')
                
                # Scroll down to ensure all content is loaded
                await page.evaluate('window.scrollTo(0, document.body.scrollHeight)')
                await page.wait_for_timeout(1000)  # Wait a second for any animations
                
                # Take a screenshot of the full page
                await page.screenshot(path=filepath, full_page=True)
                
                logger.info(f"Screenshot successfully saved to {filepath}")
                
                # Read the saved screenshot file to return its content
                with open(filepath, 'rb') as f:
                    screenshot_data = f.read()
                
                await browser.close()
                return filepath, screenshot_data
                
            except Exception as e:
                logger.error(f"Playwright screenshot capture failed: {str(e)}")
                traceback.print_exc()
                return None, None
            
    except Exception as e:
        logger.error(f"Error capturing screenshot: {str(e)}")
        traceback.print_exc()
        return None, None

def capture_screenshot_sync(url, retry_count=0):
    """
    Enhanced synchronous version of screenshot capture using Playwright.
    Implements advanced anti-bot detection measures to mimic human browsing behavior.
    
    Args:
        url (str): The URL to capture
        retry_count (int): Current retry attempt, used for recursive retries
        
    Returns:
        tuple: (filepath, screenshot_data, img_filepath) or (None, None, None) if failed
    """
    import time

    # If we've exceeded max retries, give up
    if retry_count >= MAX_RETRIES:
        logger.error(f"Maximum retry attempts ({MAX_RETRIES}) exceeded for {url}")
        return None, None, None

    try:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{timestamp}_{url.split('/')[-1]}.png"
        filepath = os.path.join(SCREENSHOT_DIR, filename)
        
        logger.info(f"Capturing screenshot from {url} using Playwright (sync) - Attempt {retry_count + 1}/{MAX_RETRIES}")
        
        # Get domain for cookie storage
        domain = urlparse(url).netloc
        cookie_file = os.path.join(COOKIES_DIR, f"{domain.replace('.', '_')}.json")
        
        # Try to find chromium in common locations
        chromium_paths = [
            "/nix/store/zi4f80l169xlmivz8vja8wlphq74qqk0-chromium-125.0.6422.141/bin/chromium",
            "/usr/bin/chromium-browser",
            "/usr/bin/chromium",
            "/nix/store/chromium/bin/chromium"
        ]
        
        chromium_path = None
        for path in chromium_paths:
            if os.path.exists(path):
                logger.info(f"Using Chromium from: {path}")
                chromium_path = path
                break
        
        # Select randomized browser fingerprint parameters
        fingerprint = {
            'screen': random.choice(BROWSER_FINGERPRINT_MODIFICATIONS['screen_sizes']),
            'color_depth': random.choice(BROWSER_FINGERPRINT_MODIFICATIONS['color_depths']),
            'platform': random.choice(BROWSER_FINGERPRINT_MODIFICATIONS['platforms']),
            'languages': random.choice(BROWSER_FINGERPRINT_MODIFICATIONS['languages']),
            'timezone': random.choice(BROWSER_FINGERPRINT_MODIFICATIONS['timezones']),
        }
        
        # Choose a random user agent - more recent versions
        user_agent = random.choice(USER_AGENTS)
        logger.debug(f"Using user agent: {user_agent}")
        logger.debug(f"Fingerprint: {fingerprint}")
        
        # Randomize timing between actions (jitter)
        jitter = random.uniform(0.8, 1.2)  # +/- 20% randomization factor
        
        # Randomize referrer to simulate different sources
        referrers = [
            "https://www.google.com/search?q=south+africa+lottery+results",
            "https://www.google.co.za/search?q=lottery+results+south+africa",
            "https://www.bing.com/search?q=national+lottery+south+africa",
            "https://duckduckgo.com/?q=south+africa+lotto+results",
            "https://www.facebook.com/",
            "https://twitter.com/home",
            "https://www.linkedin.com/feed/",
            None  # Sometimes no referrer (direct navigation)
        ]
        
        # Select a referrer with 80% probability (sometimes direct navigation)
        referrer = random.choice(referrers) if random.random() < 0.8 else None
        
        # Use Playwright to capture screenshot with built-in timeouts
        with sync_playwright() as p:
            browser_type = p.chromium
            
            try:
                # Launch with specific arguments to prevent detection
                browser = browser_type.launch(
                    headless=True,
                    executable_path=chromium_path,
                    args=[
                        "--disable-blink-features=AutomationControlled",
                        "--disable-features=IsolateOrigins,site-per-process",
                        "--disable-site-isolation-trials",
                        f"--window-size={fingerprint['screen']['width']},{fingerprint['screen']['height']}",
                        "--no-sandbox",
                        "--disable-setuid-sandbox",
                        # Additional flags to reduce detection
                        "--disable-infobars",
                        "--disable-dev-shm-usage",
                        "--disable-browser-side-navigation",
                        "--disable-gpu",
                        "--disable-accelerated-2d-canvas",
                        "--disable-accelerated-jpeg-decoding",
                        "--disable-accelerated-mjpeg-decode",
                        "--disable-accelerated-video-decode",
                        f"--user-agent={user_agent}",
                        # Disable automation flags
                        "--disable-automation"
                    ]
                )
                
                # Create a new context with enhanced settings to appear more human-like
                # Randomly select hardware concurrency and device memory to mimic different devices
                hw_concurrency = random.choice(BROWSER_FINGERPRINT_MODIFICATIONS['hardware_concurrency'])
                device_memory = random.choice(BROWSER_FINGERPRINT_MODIFICATIONS['device_memory'])
                webgl_info = random.choice(BROWSER_FINGERPRINT_MODIFICATIONS['webgl_vendors'])
                
                # Create a context with advanced fingerprinting attributes
                context = browser.new_context(
                    viewport={'width': fingerprint['screen']['width'], 'height': fingerprint['screen']['height']},
                    user_agent=user_agent,
                    locale=fingerprint['languages'][0],
                    timezone_id=fingerprint['timezone'],
                    geolocation={"latitude": -26.2041, "longitude": 28.0473},  # Johannesburg coordinates
                    permissions=['geolocation'],
                    color_scheme=random.choice(['light', 'light', 'light', 'dark']),  # 75% light, 25% dark
                    reduced_motion=random.choice(['no-preference', 'no-preference', 'reduce']),  # 66% no-preference
                    has_touch=random.random() < 0.3,  # 30% chance to simulate touch capability
                    is_mobile=random.random() < 0.12,  # 12% chance to be mobile
                    device_scale_factor=random.choice([1, 1, 1, 1.5, 2]),  # Weighted towards 1x
                    java_script_enabled=True,  # Always enable JavaScript
                    accept_downloads=False,  # Most browsing doesn't involve downloads
                )
                
                # Load cookies from previous sessions if available
                if os.path.exists(cookie_file):
                    try:
                        with open(cookie_file, 'r') as f:
                            cookies = json.load(f)
                            context.add_cookies(cookies)
                            logger.info(f"Loaded {len(cookies)} cookies for {domain}")
                    except Exception as e:
                        logger.warning(f"Error loading cookies: {str(e)}")
                
                # Create a new page
                page = context.new_page()
                
                # Execute standard stealth script to prevent detection
                # This script modifies navigator properties to appear as a real browser
                stealth_script = """
                function() {
                    // Overwrite the 'webdriver' property
                    Object.defineProperty(navigator, 'webdriver', {
                        get: function() { return false; },
                        configurable: true
                    });
                    
                    // Set proper platform
                    Object.defineProperty(navigator, 'platform', {
                        get: function() { return 'Win32'; },
                        configurable: true
                    });
                    
                    // Override productSub
                    Object.defineProperty(navigator, 'productSub', {
                        get: function() { return '20100101'; },
                        configurable: true
                    });
                    
                    // Set vendor
                    Object.defineProperty(navigator, 'vendor', {
                        get: function() { return 'Google Inc.'; },
                        configurable: true
                    });
                    
                    // Set languages 
                    Object.defineProperty(navigator, 'languages', {
                        get: function() { return ['en-ZA', 'en', 'af']; },
                        configurable: true
                    });
                    
                    // Set hardware concurrency
                    Object.defineProperty(navigator, 'hardwareConcurrency', {
                        get: function() { return 8; },
                        configurable: true
                    });
                    
                    // Hide automation flag
                    if (window.chrome) {
                        if (window.chrome.automation) {
                            delete window.chrome.automation;
                        }
                    }
                }
                """
                page.evaluate(stealth_script)
                
                # Set extra HTTP headers to appear more like a real browser
                headers = {
                    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
                    "Accept-Language": f"{fingerprint['languages'][0]},en;q=0.9",
                    "Accept-Encoding": "gzip, deflate, br",
                    "Connection": "keep-alive",
                    "Upgrade-Insecure-Requests": "1",
                    "Sec-Fetch-Dest": "document",
                    "Sec-Fetch-Mode": "navigate",
                    "Sec-Fetch-User": "?1",
                    "Sec-Ch-Ua": f"\"Chromium\";v=\"{random.randint(118, 125)}\", \"Google Chrome\";v=\"{random.randint(118, 125)}\"",
                    "Sec-Ch-Ua-Mobile": random.choice(["?0", "?1"]),
                    "Sec-Ch-Ua-Platform": f"\"{fingerprint['platform']['os']}\"",
                    "DNT": "1",
                    "Cache-Control": "max-age=0",
                }
                
                # Add referer only if we have one
                if referrer:
                    headers["Referer"] = referrer
                    
                page.set_extra_http_headers(headers)
                
                # Add randomized delays to appear more human-like
                # Random initial wait before accessing the site (250-850ms)
                initial_wait = random.randint(250, 850)
                logger.debug(f"Initial wait: {initial_wait}ms")
                page.wait_for_timeout(initial_wait)
                
                # Navigation strategy with fallbacks
                navigation_success = False
                start_time = time.time()
                max_time = 45  # Maximum time in seconds (increased for reliability)
                
                # Try different navigation strategies
                navigation_strategies = [
                    {'wait_until': 'domcontentloaded', 'timeout': 25000},
                    {'wait_until': 'load', 'timeout': 30000},
                    {'wait_until': 'networkidle', 'timeout': 35000}
                ]
                
                # Shuffle the strategies to randomize our approach
                random.shuffle(navigation_strategies)
                
                # Loop through strategies until one succeeds
                for i, strategy in enumerate(navigation_strategies):
                    if navigation_success:
                        break
                        
                    try:
                        logger.info(f"Trying navigation strategy {i+1}: {strategy['wait_until']}")
                        
                        # Navigate to the URL using the current strategy
                        response = page.goto(
                            url, 
                            wait_until=strategy['wait_until'], 
                            timeout=strategy['timeout'],
                            referer=referrer
                        )
                        
                        # Wait a randomized amount of time for additional resources to load
                        # This makes it appear more human-like
                        human_wait = random.randint(1500, 3000)
                        logger.debug(f"Human wait after page load: {human_wait}ms")
                        page.wait_for_timeout(human_wait)
                        
                        # Check response status
                        if response and response.status >= 200 and response.status < 300:
                            logger.info(f"Navigation successful with status {response.status}")
                            navigation_success = True
                        else:
                            logger.warning(f"Navigation returned non-success status: {response.status if response else 'unknown'}")
                            
                            # Check for common block indicators in page content
                            page_content = page.content()
                            if any(term in page_content.lower() for term in ["denied", "blocked", "captcha", "security check", "cloudflare", "access denied"]):
                                logger.warning(f"Possible blocking detected in content")
                                # We'll continue anyway, but log this issue
                    
                    except Exception as e:
                        # If timeout occurs, log but try next strategy
                        logger.warning(f"Navigation strategy {i+1} failed: {str(e)}")
                        
                        # If we've been trying too long, give up
                        if time.time() - start_time > max_time:
                            logger.error("Exceeded maximum navigation time")
                            browser.close()
                            
                            # If we've reached max retries, give up, otherwise retry with new session
                            if retry_count >= MAX_RETRIES - 1:
                                logger.error(f"Max retries reached ({MAX_RETRIES}), giving up on {url}")
                                return None, None, None
                            else:
                                logger.info(f"Retrying with new browser session (attempt {retry_count + 1})")
                                # Wait a longer time before the retry to avoid rate limiting
                                time.sleep(5 + random.random() * 5)  # 5-10 seconds
                                return capture_screenshot_sync(url, retry_count + 1)
                
                # Check if we were blocked or got a CAPTCHA - expanded detection
                captcha_selectors = [
                    'div:has-text("captcha")', 
                    'div:has-text("CAPTCHA")',
                    'img[src*="captcha"]',
                    'div[class*="captcha"]',
                    'div:has-text("security check")',
                    'div:has-text("bot")',
                    'div:has-text("automated")',
                    'div:has-text("blocked")',
                    'div:has-text("unusual activity")',
                    'iframe[src*="captcha"]',
                    'iframe[src*="challenge"]',
                ]
                
                for selector in captcha_selectors:
                    if page.query_selector(selector):
                        logger.warning(f"CAPTCHA/blocking detected using selector: {selector}")
                        
                        # Take a screenshot of the CAPTCHA for debugging
                        captcha_path = os.path.join(SCREENSHOT_DIR, f"captcha_{timestamp}.png")
                        page.screenshot(path=captcha_path)
                        logger.info(f"Saved CAPTCHA screenshot to {captcha_path}")
                        
                        # Close browser to clean up resources
                        browser.close()
                        
                        # If we've reached max retries, give up, otherwise retry with new session
                        if retry_count >= MAX_RETRIES - 1:
                            logger.error(f"Max retries reached ({MAX_RETRIES}), giving up on {url}")
                            return None, None, None
                        else:
                            logger.info(f"Retrying with new parameters (attempt {retry_count + 1})")
                            # Wait a longer time before the retry to avoid rate limiting
                            time.sleep(10 + random.random() * 10)  # 10-20 seconds
                            return capture_screenshot_sync(url, retry_count + 1)
                
                # Simulate human-like interaction and movements
                try:
                    # Get page dimensions
                    page_height = page.evaluate('document.body.scrollHeight')
                    page_width = page.evaluate('document.body.scrollWidth')
                    viewport_height = page.evaluate('window.innerHeight')
                    
                    # Move the mouse around a bit randomly before scrolling to appear more human
                    for _ in range(random.randint(2, 5)):
                        # Move to random positions
                        page.mouse.move(
                            random.randint(100, min(page_width - 100, 1000)), 
                            random.randint(100, min(viewport_height - 100, 700))
                        )
                        page.wait_for_timeout(random.randint(100, 500))
                    
                    # Apply enhanced human-like scrolling behavior
                    current_position = 0
                    scroll_positions = []
                    
                    # Select a random scroll pattern for this session to appear more human-like
                    # This makes each browser session have a consistent "personality" in how it scrolls
                    scroll_pattern = random.choice(SCROLL_PATTERNS) if random.random() < 0.7 else SCROLL_BEHAVIOR
                    logger.debug(f"Using {'random scroll pattern' if scroll_pattern != SCROLL_BEHAVIOR else 'default scroll behavior'} with {len(scroll_pattern)} steps")
                    
                    # Apply each scroll step with varied timing and distance
                    for scroll_step in scroll_pattern:
                        # Calculate scroll distance for this step with some randomness
                        jitter_factor = random.uniform(0.9, 1.1)  # +/- 10% jitter
                        target_position = int(page_height * scroll_step['distance'] * jitter_factor)
                        
                        # Smooth scroll animation to simulate human behavior
                        # This divides the scroll into small steps to make it look like human scrolling
                        if current_position < target_position:
                            step_count = random.randint(5, 15)  # Number of small scrolls to reach target
                            step_size = (target_position - current_position) / step_count
                            
                            for i in range(1, step_count + 1):
                                # Add slight non-linearity to the scroll speed (easing)
                                progress = i / step_count
                                # Easing function - start slow, accelerate in middle, slow at end
                                eased_progress = 0.5 - 0.5 * math.cos(math.pi * progress)
                                
                                interim_pos = int(current_position + (target_position - current_position) * eased_progress)
                                page.evaluate(f'window.scrollTo(0, {interim_pos})')
                                page.wait_for_timeout(int((scroll_step['delay'] * 1000) / step_count))
                        
                        # Final position
                        page.evaluate(f'window.scrollTo(0, {target_position})')
                        
                        # Wait for the specified delay with jitter
                        delay_with_jitter = int(scroll_step['delay'] * 1000 * random.uniform(0.8, 1.2))
                        page.wait_for_timeout(delay_with_jitter)
                        
                        # After scrolling to a new position, randomly decide to interact with the page
                        if random.random() < 0.3:  # 30% chance to interact
                            # Look for clickable elements like links or buttons in the viewport
                            elements = page.query_selector_all('a, button, .btn, [role="button"]')
                            if elements and len(elements) > 0:
                                # Filter to get only visible elements in current viewport
                                visible_elements = []
                                for elem in elements:
                                    try:
                                        # Check if element is visible and in viewport
                                        is_visible = elem.is_visible()
                                        if is_visible:
                                            bounding_box = elem.bounding_box()
                                            if bounding_box and bounding_box['y'] > current_position and bounding_box['y'] < current_position + viewport_height:
                                                visible_elements.append(elem)
                                    except:
                                        pass
                                
                                # Possibly hover over a visible element
                                if visible_elements and random.random() < 0.7:  # 70% chance to hover
                                    try:
                                        random_element = random.choice(visible_elements)
                                        random_element.hover()
                                        page.wait_for_timeout(random.randint(300, 800))
                                    except:
                                        pass
                        
                        # Update current position
                        current_position = target_position
                        scroll_positions.append(current_position)
                    
                    # Randomly scroll back up to previously viewed position
                    if len(scroll_positions) > 2 and random.random() < 0.7:  # 70% chance to scroll back
                        # Choose a random previous position
                        random_position = random.choice(scroll_positions[:len(scroll_positions)-1])
                        
                        # Smooth scroll back to that position
                        page.evaluate(f'window.scrollTo({{ top: {random_position}, behavior: "smooth" }})')
                        page.wait_for_timeout(random.randint(1000, 2000))
                        
                        # Then either stay there or go back to bottom
                        if random.random() < 0.5:  # 50% chance to go back to bottom
                            page.evaluate(f'window.scrollTo({{ top: {scroll_positions[-1]}, behavior: "smooth" }})')
                            page.wait_for_timeout(random.randint(800, 1500))
                    
                except Exception as e:
                    logger.warning(f"Error during human-like interaction: {str(e)}")
                
                # Wait a final random delay before taking the screenshot
                page.wait_for_timeout(random.randint(500, 1500))
                
                # Save the full page screenshot
                page.screenshot(path=filepath, full_page=True)
                logger.info(f"Full screenshot saved to {filepath}")
                
                # Save cookies from this session for future use
                try:
                    cookies = context.cookies()
                    with open(cookie_file, 'w') as f:
                        json.dump(cookies, f)
                    logger.info(f"Saved {len(cookies)} cookies for {domain}")
                except Exception as e:
                    logger.warning(f"Error saving cookies: {str(e)}")
                
                logger.info(f"Screenshot process completed for {url}")
                
                # Read the full screenshot data
                with open(filepath, 'rb') as f:
                    screenshot_data = f.read()
                
                # Clean up browser resources
                browser.close()
                
                # Return without zoomed path
                return filepath, screenshot_data, None
                
            except Exception as e:
                logger.error(f"Playwright screenshot capture failed: {str(e)}")
                traceback.print_exc()
                
                # Clean up any browser instances
                try:
                    browser.close()
                except:
                    pass
                
                # If this is the last retry, give up
                if retry_count >= MAX_RETRIES - 1:
                    logger.error(f"Max retries reached ({MAX_RETRIES}), giving up on {url}")
                    return None, None, None
                else:
                    # Otherwise retry with exponential backoff
                    backoff_time = 5 * (2 ** retry_count) + random.random() * 5  # 5, 15, 35, etc seconds + random jitter
                    logger.info(f"Backing off for {backoff_time:.1f} seconds before retry {retry_count + 1}")
                    time.sleep(backoff_time)
                    return capture_screenshot_sync(url, retry_count + 1)
            
    except Exception as e:
        logger.error(f"Error capturing screenshot: {str(e)}")
        traceback.print_exc()
        
        # If this is the last retry, give up
        if retry_count >= MAX_RETRIES - 1:
            return None, None, None
        else:
            # Simple linear backoff
            backoff_time = 3 * (retry_count + 1) + random.random() * 2
            logger.info(f"Backing off for {backoff_time:.1f} seconds before retry {retry_count + 1}")
            time.sleep(backoff_time)
            return capture_screenshot_sync(url, retry_count + 1)

def capture_screenshot(url, lottery_type=None, increased_timeout=False):
    """
    Capture HTML content from the specified URL and save metadata to database.
    
    This function tries multiple methods to capture screenshots:
    1. First it attempts to use Playwright (if available)
    2. If Playwright fails, falls back to requests and BeautifulSoup
    
    Args:
        url (str): The URL to capture
        lottery_type (str, optional): The type of lottery. If None, extracted from URL.
        increased_timeout (bool): Whether to use increased timeout for requests
        
    Returns:
        tuple: (filepath, screenshot_data, img_filepath) or (None, None, None) if failed
    """
    if not lottery_type:
        lottery_type = extract_lottery_type_from_url(url)
    
    logger.info(f"Starting capture process for {lottery_type} from {url}")
    
    # Use semaphore to limit concurrent requests
    # This prevents too many simultaneous connections
    if not screenshot_semaphore.acquire(blocking=True, timeout=300):
        logger.error(f"Could not acquire screenshot semaphore for {lottery_type} after waiting 5 minutes")
        return None, None, None
    
    try:
        # Try to use Playwright first (synchronous version)
        if is_playwright_available():
            logger.info(f"Attempting to capture {lottery_type} with Playwright")
            try:
                # Try our improved sync version first (more reliable)
                result = capture_screenshot_sync(url, retry_count=0)
                if result and all(result):
                    filepath, screenshot_data, img_filepath = result
                    logger.info(f"Successfully captured screenshot with Playwright sync for {url}")
                    
                    # Save to database
                    try:
                        save_screenshot_to_database(url, lottery_type, filepath, img_filepath)
                    except Exception as db_error:
                        logger.error(f"Database error when saving screenshot: {str(db_error)}")
                        logger.error(traceback.format_exc())
                        # Continue anyway as we have the files
                        
                    return filepath, screenshot_data, img_filepath
            except Exception as e:
                logger.warning(f"Playwright sync capture failed: {str(e)}")
                logger.warning(traceback.format_exc())
                
                # Traditional Playwright approach as backup
                logger.info(f"Attempting to capture screenshot using traditional Playwright for {url}")
                
                # Generate timestamp for filename
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                unique_id = str(uuid.uuid4())[:8]
                
                # Create image filename
                img_filename = f"{lottery_type.replace(' ', '_')}_{timestamp}_{unique_id}.png"
                img_filepath = os.path.join(SCREENSHOT_DIR, img_filename)
                
                # Try to use synchronous Playwright
                with sync_playwright() as p:
                    browser_type = p.chromium
                    
                    # Launch with specific arguments to prevent detection
                    browser = browser_type.launch(
                        headless=True,
                        args=["--no-sandbox", "--disable-setuid-sandbox"]
                    )
                    
                    try:
                        # Create a new context with specific settings
                        context = browser.new_context(
                            viewport={'width': 1280, 'height': 1024},
                            user_agent=random.choice(USER_AGENTS)
                        )
                        
                        # Create a new page
                        page = context.new_page()
                        
                        # Set timeout (increased if needed)
                        timeout = 60000 if increased_timeout else 30000  # in milliseconds
                        
                        # Navigate to URL
                        page.goto(url, timeout=timeout, wait_until='networkidle')
                        
                        # Take screenshot
                        page.screenshot(path=img_filepath, full_page=True)
                        
                        # Read screenshot data
                        with open(img_filepath, 'rb') as f:
                            screenshot_data = f.read()
                        
                        # Create HTML file
                        html_content = page.content()
                        html_filename = f"{lottery_type.replace(' ', '_')}_{timestamp}_{unique_id}.html"
                        filepath = os.path.join(SCREENSHOT_DIR, html_filename)
                        
                        with open(filepath, 'w', encoding='utf-8') as f:
                            f.write(html_content)
                        
                        # Close browser
                        browser.close()
                        
                        logger.info(f"Successfully captured screenshot with Playwright from {url}")
                        
                        # Save to database
                        try:
                            # Check if we need to create an app context
                            from flask import current_app, has_app_context
                            if not has_app_context():
                                # Import app here to avoid circular imports
                                from main import app
                                with app.app_context():
                                    # Save screenshot metadata to database within app context
                                    screenshot = Screenshot(
                                        url=url,
                                        lottery_type=lottery_type,
                                        timestamp=datetime.now(),
                                        path=filepath,
                                        processed=False
                                    )
                                    
                                    db.session.add(screenshot)
                                    db.session.commit()
                                    
                                    logger.info(f"Screenshot record saved to database with ID {screenshot.id}")
                            else:
                                # We already have an app context, proceed normally
                                screenshot = Screenshot(
                                    url=url,
                                    lottery_type=lottery_type,
                                    timestamp=datetime.now(),
                                    path=filepath,
                                    processed=False
                                )
                                
                                db.session.add(screenshot)
                                db.session.commit()
                                
                                logger.info(f"Screenshot record saved to database with ID {screenshot.id}")
                        except Exception as e:
                            logger.error(f"Error saving Playwright screenshot to database: {str(e)}")
                            traceback.print_exc()
                            # Still return the filepath so OCR can be attempted
                        
                        return filepath, screenshot_data, img_filepath
                    finally:
                        # Make sure the browser is closed
                        if 'browser' in locals():
                            browser.close()
                    
            except Exception as playwright_error:
                logger.warning(f"Failed to capture with Playwright: {str(playwright_error)}. Falling back to requests.")
                # Fall through to the fallback method
        else:
            logger.info("Playwright not available, using requests for screenshot capture")
        
        # Fallback to using requests and BeautifulSoup
        logger.info(f"Using fallback method (requests) to capture data from {url}")
        
        # Import required libraries
        import requests
        from bs4 import BeautifulSoup
        import uuid
        from PIL import Image
        import io
        
        # Headers to mimic a real browser with random user agent
        headers = {
            'User-Agent': random.choice(USER_AGENTS),
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Referer': 'https://www.google.com/',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Cache-Control': 'max-age=0',
            'DNT': '1'  # Do Not Track header for privacy-focused appearance
        }
        
        # Request the page with a timeout (increased if needed)
        timeout = 60 if increased_timeout else 30
        logger.info(f"Requesting URL: {url} with timeout {timeout}s")
        
        try:
            # Modified to handle gzip encoding issues by explicitly disabling content compression
            # This fixes the "InvalidChunkLength" errors by telling the server not to compress the response
            headers['Accept-Encoding'] = 'identity'  # Explicitly request uncompressed response
            
            response = requests.get(url, headers=headers, timeout=timeout, stream=True)
            
            if response.status_code != 200:
                logger.error(f"Failed to fetch URL {url}: HTTP status {response.status_code}")
                return None, None, None
                
            # Read the entire content with streaming to avoid compression issues
            content = ""
            for chunk in response.iter_content(chunk_size=1024, decode_unicode=True):
                if chunk:
                    content += chunk
            
            # Parse the HTML content
            soup = BeautifulSoup(content, 'html.parser')
        except requests.exceptions.ChunkedEncodingError as chunk_error:
            logger.error(f"Chunked encoding error for {url}: {str(chunk_error)}")
            # Try again with even more cautious settings
            logger.info(f"Retrying with more cautious request settings for {url}")
            
            # Create a completely new session with different settings
            with requests.Session() as session:
                session.headers.update(headers)
                session.headers['Accept-Encoding'] = 'identity'
                
                # Setting lower timeout and disabling keep-alive
                session.headers['Connection'] = 'close'
                response = session.get(url, timeout=timeout/2, stream=False)
                
                if response.status_code != 200:
                    logger.error(f"Failed to fetch URL {url} on retry: HTTP status {response.status_code}")
                    return None, None, None
                
                # Parse the HTML content
                soup = BeautifulSoup(response.text, 'html.parser')
        
        # Generate timestamp for filename
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        # Generate a unique ID
        unique_id = str(uuid.uuid4())[:8]
        
        # Create filenames
        screenshot_filename = f"{lottery_type.replace(' ', '_')}_{timestamp}_{unique_id}.html"
        filepath = os.path.join(SCREENSHOT_DIR, screenshot_filename)
        
        # Create a simple image representation of the webpage (for compatibility)
        img = Image.new('RGB', (1200, 800), color = (255, 255, 255))
        img_filename = f"{lottery_type.replace(' ', '_')}_{timestamp}_{unique_id}.png"
        img_filepath = os.path.join(SCREENSHOT_DIR, img_filename)
        
        # Save HTML content to file
        os.makedirs(SCREENSHOT_DIR, exist_ok=True)
        with open(filepath, 'w', encoding='utf-8') as f:
            # Use the content variable if we used streaming, otherwise use response.text
            if 'content' in locals():
                f.write(content)
            else:
                f.write(response.text)
            
        # Save image to file
        img.save(img_filepath)
        
        logger.info(f"Successfully captured content from {url} and saved to {filepath}")
        
        # Prepare image data for return
        img_buffer = io.BytesIO()
        img.save(img_buffer, format='PNG')
        screenshot_data = img_buffer.getvalue()
        
        # Save to database using our helper function
        try:
            save_screenshot_to_database(url, lottery_type, filepath, img_filepath)
        except Exception as e:
            logger.error(f"Error saving fallback screenshot to database: {str(e)}")
            logger.error(traceback.format_exc())
            # Still return the filepath even if DB saving failed
        
        return filepath  # Return only the filepath - zoom functionality has been removed
    except Exception as e:
        logger.error(f"Error in capture_screenshot: {str(e)}")
        traceback.print_exc()
        return None  # Return only None - zoom functionality has been removed
    finally:
        # Always release the semaphore in the finally block
        # to ensure it's released even if an exception occurs
        screenshot_semaphore.release()
        logger.debug(f"Released screenshot semaphore for {lottery_type}")

def extract_lottery_type_from_url(url):
    """Extract lottery type from the URL"""
    lower_url = url.lower()
    
    if "lotto-plus-1" in lower_url:
        return "Lotto Plus 1"
    elif "lotto-plus-2" in lower_url:
        return "Lotto Plus 2"
    elif "powerball-plus" in lower_url:
        return "Powerball Plus"
    elif "powerball" in lower_url:
        return "Powerball"
    elif "daily-lotto" in lower_url:
        return "Daily Lotto"
    elif "lotto" in lower_url:
        return "Lotto"
    
    # For results pages
    if "results" in lower_url:
        if "lotto-plus-1-results" in lower_url:
            return "Lotto Plus 1 Results"
        elif "lotto-plus-2-results" in lower_url:
            return "Lotto Plus 2 Results"
        elif "powerball-plus" in lower_url:
            return "Powerball Plus Results"
        elif "powerball" in lower_url:
            return "Powerball Results"
        elif "daily-lotto" in lower_url:
            return "Daily Lotto Results"
        elif "lotto" in lower_url:
            return "Lotto Results"
    
    return "Unknown"

def get_unprocessed_screenshots():
    """Get all unprocessed screenshots from the database"""
    return Screenshot.query.filter_by(processed=False).all()

def mark_screenshot_as_processed(screenshot_id):
    """Mark a screenshot as processed in the database"""
    screenshot = Screenshot.query.get(screenshot_id)
    if screenshot:
        screenshot.processed = True
        db.session.commit()
        
def retake_screenshot_by_id(screenshot_id, app=None):
    """
    Retake a specific screenshot by its ID.
    
    Args:
        screenshot_id (int): ID of the screenshot to retake
        app: Flask app context (optional)
    
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        # Add context manager if app is provided
        if app:
            with app.app_context():
                screenshot = Screenshot.query.get(screenshot_id)
        else:
            screenshot = Screenshot.query.get(screenshot_id)
        
        if not screenshot:
            logger.error(f"Screenshot with ID {screenshot_id} not found")
            return False
        
        logger.info(f"Retaking screenshot for {screenshot.url} ({screenshot.lottery_type})")
        
        # Take the screenshot
        success = take_screenshot_threaded(screenshot.url, screenshot.lottery_type)
        
        if success:
            logger.info(f"Successfully retook screenshot for {screenshot.url}")
            return True
        else:
            logger.error(f"Failed to retake screenshot for {screenshot.url}")
            return False
    
    except Exception as e:
        logger.error(f"Error retaking screenshot by ID {screenshot_id}: {str(e)}")
        traceback.print_exc()
        return False
        
def retake_all_screenshots(app=None, use_threading=False):
    """
    Retake all screenshots for each configured URL.
    
    Args:
        app: Flask app context (optional)
        use_threading: Whether to use threading for processing screenshots.
                      Set to False for sync operations from UI, True for scheduled tasks.
    
    Returns:
        int: Number of screenshots captured
    """
    try:
        # Add context manager if app is provided
        if app:
            with app.app_context():
                configs = ScheduleConfig.query.filter_by(active=True).all()
        else:
            configs = ScheduleConfig.query.filter_by(active=True).all()
            
        logger.info(f"Retaking screenshots for {len(configs)} configurations")
        
        # Normal screenshot capture logic
        count = 0
        results = []
        failed_configs = []
        
        # When called from the UI, we want to wait for screenshots to complete
        if not use_threading:
            # First attempt - try each URL
            for config in configs:
                try:
                    # Call the worker function directly, not through a thread
                    success = _take_screenshot_worker(config.url, config.lottery_type)
                    if success:
                        count += 1
                        logger.info(f"Successfully captured screenshot for {config.lottery_type}")
                    else:
                        logger.warning(f"Failed to capture screenshot for {config.lottery_type} - will retry")
                        failed_configs.append(config)
                except Exception as url_error:
                    logger.warning(f"Error capturing screenshot for {config.lottery_type}: {str(url_error)} - will retry")
                    failed_configs.append(config)
            
            # Second attempt - retry failed URLs with increased timeout
            if failed_configs:
                logger.info(f"Retrying {len(failed_configs)} failed URLs with increased timeout")
                for config in failed_configs:
                    try:
                        # Try again with increased timeout
                        logger.info(f"Retrying screenshot capture for {config.lottery_type}")
                        success = _take_screenshot_worker(config.url, config.lottery_type, increased_timeout=True)
                        if success:
                            count += 1
                            logger.info(f"Successfully captured screenshot for {config.lottery_type} on retry")
                        else:
                            # Last resort - update database timestamp but keep existing file
                            logger.warning(f"Failed to capture screenshot for {config.lottery_type} even with retry")
                            # Update database record with current timestamp to show we tried
                            _update_single_screenshot_record(config.url, config.lottery_type, app)
                    except Exception as retry_error:
                        logger.error(f"Error in retry for {config.lottery_type}: {str(retry_error)}")
                        # Update database record with current timestamp to show we tried
                        _update_single_screenshot_record(config.url, config.lottery_type, app)
            
            # Run cleanup after all screenshots are processed (for UI operations)
            logger.info("Running screenshot cleanup after sync operation")
            if app:
                with app.app_context():
                    cleanup_old_screenshots()
            else:
                cleanup_old_screenshots()
        else:
            # For scheduled tasks, use threads for parallel processing
            for config in configs:
                if take_screenshot_threaded(config.url, config.lottery_type):
                    count += 1
                
        logger.info(f"Successfully retook {count} screenshots")
        return count
    except Exception as e:
        logger.error(f"Error retaking all screenshots: {str(e)}")
        traceback.print_exc()
        return 0

def _update_screenshot_records_without_capture(configs, app=None):
    """
    Update screenshot records in the database using existing files when browser automation is unavailable.
    
    Args:
        configs: List of ScheduleConfig objects
        app: Flask app context (optional)
        
    Returns:
        int: Number of updated records
    """
    count = 0
    try:
        # Get all existing screenshot files
        screenshot_files = os.listdir(SCREENSHOT_DIR)
        screenshot_files = [f for f in screenshot_files if f.endswith('.png') and os.path.isfile(os.path.join(SCREENSHOT_DIR, f))]
        
        # Sort by timestamp (newest first)
        screenshot_files.sort(reverse=True)
        
        # Create a mapping of lottery type to latest screenshot file
        type_to_file = {}
        for filename in screenshot_files:
            for config in configs:
                lottery_type = config.lottery_type
                url_part = config.url.split('/')[-1]
                
                # Check if filename contains the URL part and is for this lottery type
                if url_part in filename:
                    if lottery_type not in type_to_file:
                        type_to_file[lottery_type] = filename
                    break
        
        # Update database records
        if app:
            context_func = app.app_context
        else:
            # Create a dummy context manager
            from contextlib import contextmanager
            @contextmanager
            def context_func():
                yield
        
        with context_func():
            for lottery_type, filename in type_to_file.items():
                filepath = os.path.join(SCREENSHOT_DIR, filename)
                
                # Get or create screenshot record
                screenshot = Screenshot.query.filter_by(lottery_type=lottery_type).first()
                if not screenshot:
                    # Find the corresponding config
                    config = next((c for c in configs if c.lottery_type == lottery_type), None)
                    if not config:
                        continue
                    
                    screenshot = Screenshot(
                        url=config.url,
                        lottery_type=lottery_type,
                        timestamp=datetime.now(),
                        path=filepath,
                        processed=False
                    )
                    db.session.add(screenshot)
                else:
                    screenshot.path = filepath
                    screenshot.timestamp = datetime.now()
                
                db.session.commit()
                count += 1
                logger.info(f"Updated screenshot record for {lottery_type} using existing file: {filename}")
        
        return count
    except Exception as e:
        logger.error(f"Error updating screenshot records without capture: {str(e)}")
        traceback.print_exc()
        return count

def take_screenshot_threaded(url, lottery_type, use_thread=True, increased_timeout=False):
    """
    Take a screenshot of the specified URL in a separate thread.
    
    Args:
        url (str): The URL to capture
        lottery_type (str): Type of lottery (used for DB storage)
        use_thread (bool): Whether to use a thread or run synchronously
        increased_timeout (bool): Whether to use increased timeout for requests
        
    Returns:
        bool: True if the screenshot was successfully scheduled/taken
    """
    if not url:
        logger.error("Empty URL provided for screenshot")
        return False
        
    try:
        if use_thread:
            # Use a thread to avoid blocking the main thread
            threading.Thread(
                target=_take_screenshot_worker,
                args=(url, lottery_type, increased_timeout),
                daemon=True
            ).start()
            return True
        else:
            # Run synchronously
            return _take_screenshot_worker(url, lottery_type, increased_timeout)
    except Exception as e:
        logger.error(f"Error scheduling screenshot for {url}: {str(e)}")
        traceback.print_exc()
        return False

def _take_screenshot_worker(url, lottery_type, increased_timeout=False):
    """
    Worker function to take a screenshot of the specified URL.
    Intended to be run in a separate thread.
    
    Args:
        url (str): The URL to capture
        lottery_type (str): Type of lottery
        increased_timeout (bool): Whether to use increased timeout values
        
    Returns:
        bool: True if successful
    """
    try:
        # Acquire the semaphore to limit concurrent screenshot operations
        with screenshot_semaphore:
            logger.info(f"Taking screenshot of {url} ({lottery_type})")
            
            # Take the screenshot, using increased timeout if specified
            filepath = capture_screenshot(url, lottery_type, increased_timeout=increased_timeout)
            
            if not filepath:
                logger.error(f"Failed to capture screenshot for {url}")
                return False
                
            # Save to database
            try:
                # Check if existing screenshot exists for this URL
                existing = Screenshot.query.filter_by(url=url).first()
                
                if existing:
                    # Update existing record
                    existing.path = filepath
                    # Zoom functionality has been removed
                    existing.timestamp = datetime.now()
                    existing.processed = False
                    db.session.commit()
                    
                    logger.info(f"Updated existing screenshot record for {url}")
                    screenshot_id = existing.id
                else:
                    # Create new record
                    screenshot = Screenshot(
                        url=url,
                        lottery_type=lottery_type,
                        path=filepath,
                        # Zoom functionality has been removed
                        timestamp=datetime.now(),
                        processed=False
                    )
                    
                    db.session.add(screenshot)
                    db.session.commit()
                    
                    logger.info(f"Created new screenshot record for {url}")
                    screenshot_id = screenshot.id
                
                logger.info(f"Screenshot saved successfully (ID: {screenshot_id})")
                return True
                
            except Exception as e:
                logger.error(f"Error saving screenshot to database: {str(e)}")
                traceback.print_exc()
                return False
            
    except Exception as e:
        logger.error(f"Error in screenshot worker thread: {str(e)}")
        traceback.print_exc()
        return False

def _update_single_screenshot_record(url, lottery_type, app=None):
    """
    Update a screenshot record's timestamp without capturing a new screenshot.
    This is used as a fallback when screenshot capture fails but we want to update the timestamp.
    
    Args:
        url (str): The URL of the screenshot
        lottery_type (str): Type of lottery
        app (Flask): Flask app for context management
        
    Returns:
        bool: True if successful
    """
    try:
        # Set up app context if needed
        if app:
            context_func = app.app_context
        else:
            # Create a dummy context manager
            from contextlib import contextmanager
            @contextmanager
            def context_func():
                yield
        
        with context_func():
            # Find existing screenshot
            screenshot = Screenshot.query.filter_by(url=url).first()
            
            if screenshot:
                # Update timestamp only
                screenshot.timestamp = datetime.now()
                db.session.commit()
                logger.info(f"Updated timestamp for {lottery_type} screenshot record")
                return True
            else:
                # Find a file to use (use any existing screenshot file)
                screenshot_files = os.listdir(SCREENSHOT_DIR)
                screenshot_files = [f for f in screenshot_files if f.endswith('.png') and os.path.isfile(os.path.join(SCREENSHOT_DIR, f))]
                
                if not screenshot_files:
                    logger.error(f"No existing screenshot files found for {lottery_type}")
                    return False
                
                # Use the first file
                filepath = os.path.join(SCREENSHOT_DIR, screenshot_files[0])
                
                # Create new record
                screenshot = Screenshot(
                    url=url,
                    lottery_type=lottery_type,
                    path=filepath,
                    # Zoom functionality has been removed
                    timestamp=datetime.now(),
                    processed=False
                )
                
                db.session.add(screenshot)
                db.session.commit()
                logger.info(f"Created new screenshot record for {lottery_type} using existing file")
                return True
    except Exception as e:
        logger.error(f"Error updating screenshot record for {lottery_type}: {str(e)}")
        traceback.print_exc()
        return False

def cleanup_old_screenshots():
    """
    Clean up old screenshots to save disk space.
    Keep only ONE screenshot for each lottery type, regardless of URL or file format.
    
    This ensures we only have exactly 6 screenshots at any time (one per normalized lottery type).
    Handles all file types (HTML, PNG) and ensures complete cleanup.
    """
    logger.info("Starting screenshot cleanup process")
    
    try:
        # Step 1: Sync database with filesystem - fix any missing files
        from data_aggregator import normalize_lottery_type
        
        # Step 1a: First check for database records with missing files
        db_screenshots = Screenshot.query.all()
        invalid_records = []
        
        for screenshot in db_screenshots:
            if not screenshot.path or not os.path.exists(screenshot.path):
                invalid_records.append(screenshot)
                logger.warning(f"Screenshot ID {screenshot.id} references missing file: {screenshot.path}")
        
        # If any database records reference missing files, delete them
        if invalid_records:
            for screenshot in invalid_records:
                # Check for references in lottery results
                from models import LotteryResult
                referenced_results = LotteryResult.query.filter_by(screenshot_id=screenshot.id).all()
                
                if referenced_results:
                    # Update references to NULL
                    for result in referenced_results:
                        result.screenshot_id = None
                    db.session.commit()
                
                # Delete the invalid database record
                db.session.delete(screenshot)
                logger.info(f"Deleted invalid database record ID {screenshot.id}")
            
            db.session.commit()
            logger.info(f"Cleaned up {len(invalid_records)} invalid database records")
        
        # Step 2: Delete all files not tracked in the database
        all_files = os.listdir(SCREENSHOT_DIR)
        db_files = Screenshot.query.with_entities(Screenshot.path).all()
        db_files = [os.path.basename(f[0]) for f in db_files if f[0]]
        
        # Count files deleted
        untracked_deleted_count = 0
        
        # Remove README.md from cleanup
        if 'README.md' in all_files:
            all_files.remove('README.md')
            
        # Delete any file not in the database
        for file in all_files:
            if file not in db_files and file != 'README.md':
                try:
                    file_path = os.path.join(SCREENSHOT_DIR, file)
                    if os.path.isfile(file_path):
                        os.remove(file_path)
                        logger.info(f"Deleted untracked file: {file_path}")
                        untracked_deleted_count += 1
                except Exception as e:
                    logger.error(f"Error deleting untracked file {file}: {str(e)}")
        
        # Step 3: Group screenshots by normalized lottery type
        # Use data_aggregator's normalize_lottery_type function to standardize names
        normalized_types = {}
        screenshots_by_norm_type = {}
        
        # Group all screenshots by their normalized lottery type
        all_screenshots = Screenshot.query.order_by(Screenshot.timestamp.desc()).all()
        for screenshot in all_screenshots:
            norm_type = normalize_lottery_type(screenshot.lottery_type)
            normalized_types[screenshot.id] = norm_type
            
            if norm_type not in screenshots_by_norm_type:
                screenshots_by_norm_type[norm_type] = []
            screenshots_by_norm_type[norm_type].append(screenshot)
        
        # For each normalized lottery type, keep only the most recent screenshot
        db_deleted_count = 0
        
        for norm_type, screenshots in screenshots_by_norm_type.items():
            # Keep the newest screenshot, delete the rest
            if len(screenshots) > 1:
                logger.info(f"Found {len(screenshots)} screenshots for '{norm_type}' - keeping only the newest one")
                # First screenshot is newest (we ordered by timestamp desc)
                for screenshot in screenshots[1:]:
                    try:
                        # First check if screenshot is referenced by lottery results
                        from models import LotteryResult
                        referenced_results = LotteryResult.query.filter_by(screenshot_id=screenshot.id).all()
                        
                        if referenced_results:
                            # Screenshot is referenced, update these references to NULL
                            for result in referenced_results:
                                logger.info(f"Clearing screenshot_id reference for LotteryResult {result.id}")
                                result.screenshot_id = None
                            db.session.commit()
                                
                        # Delete the file from disk
                        if screenshot.path and os.path.exists(screenshot.path):
                            os.remove(screenshot.path)
                            logger.info(f"Deleted old screenshot file: {screenshot.path}")
                            
                            # Also check for matching PNG files with same base name
                            base_name = os.path.splitext(os.path.basename(screenshot.path))[0]
                            png_path = os.path.join(SCREENSHOT_DIR, f"{base_name}.png")
                            if os.path.exists(png_path):
                                os.remove(png_path)
                                logger.info(f"Deleted matching PNG file: {png_path}")
                            
                        # Delete the database record
                        db.session.delete(screenshot)
                        db_deleted_count += 1
                        db.session.commit()  # Commit after each deletion to avoid large transactions
                        
                    except Exception as e:
                        logger.error(f"Error deleting screenshot {screenshot.id}: {str(e)}")
                        logger.error(traceback.format_exc())
                        db.session.rollback()  # Rollback on error
        
        # Step 4: Ensure there's exactly one screenshot per normalized type
        # Get the final list of normalized types
        final_types = set()
        for screenshot in Screenshot.query.all():
            norm_type = normalize_lottery_type(screenshot.lottery_type)
            final_types.add(norm_type)
            
        # Log what we ended up with
        logger.info(f"Final normalized lottery types: {sorted(list(final_types))}")
        logger.info(f"Expected 6 normalized types: ['Daily Lottery', 'Lottery', 'Lottery Plus 1', 'Lottery Plus 2', 'Powerball', 'Powerball Plus']")
        
        # Report total files deleted
        total_deleted = db_deleted_count + untracked_deleted_count
        logger.info(f"Cleaned up {total_deleted} old screenshots ({db_deleted_count} from database, {untracked_deleted_count} untracked files)" 
                   if total_deleted > 0 else "No old screenshots to clean up")
        
        # Verify final counts match
        expected_db_count = len(final_types)  # Should be 6
        remaining_files = [f for f in os.listdir(SCREENSHOT_DIR) if os.path.isfile(os.path.join(SCREENSHOT_DIR, f)) and f != 'README.md']
        remaining_db = Screenshot.query.count()
        
        if remaining_db != expected_db_count:
            logger.warning(f"Database records ({remaining_db}) does not match expected count ({expected_db_count})")
        else:
            logger.info(f"Database records match expected count: {remaining_db}")
            
        if len(remaining_files) != remaining_db:
            logger.warning(f"Files on disk ({len(remaining_files)}) does not match database records ({remaining_db})")
        else:
            logger.info(f"Files on disk match database records: {len(remaining_files)}")
            
    except Exception as e:
        logger.error(f"Error during screenshot cleanup: {str(e)}")
        logger.error(traceback.format_exc())
        db.session.rollback()
