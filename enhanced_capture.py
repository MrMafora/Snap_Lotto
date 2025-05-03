#!/usr/bin/env python3
"""
Enhanced lottery screenshot capture script with advanced anti-bot measures.
This script uses requests with sophisticated browser fingerprinting to avoid detection.
"""
import os
import sys
import logging
import requests
import random
import time
import json
import hashlib
import uuid
from datetime import datetime
from urllib.parse import urlparse
from bs4 import BeautifulSoup
from pathlib import Path
from config import Config

# Import models if available
try:
    from models import db, Screenshot
    from flask import current_app, has_app_context
    HAS_MODELS = True
except ImportError:
    HAS_MODELS = False

# Set up logging with timestamp
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# Ensure screenshot directory exists
SCREENSHOT_DIR = os.path.join(os.getcwd(), 'screenshots')
os.makedirs(SCREENSHOT_DIR, exist_ok=True)

# South African specific browser configurations
SA_BROWSERS = [
    {
        "name": "Chrome",
        "versions": ["112.0.0.0", "113.0.0.0", "114.0.0.0", "124.0.0.0", "125.0.0.0"],
        "platforms": ["Windows NT 10.0; Win64; x64", "Macintosh; Intel Mac OS X 10_15_7"],
        "common_in_sa": True
    },
    {
        "name": "Safari",
        "versions": ["15.6", "16.0", "16.1", "17.0"],
        "platforms": ["Macintosh; Intel Mac OS X 10_15_7", "iPhone; CPU iPhone OS 16_0 like Mac OS X"],
        "common_in_sa": True
    },
    {
        "name": "Edge",
        "versions": ["112.0.1722.64", "113.0.1774.57"],
        "platforms": ["Windows NT 10.0; Win64; x64"],
        "common_in_sa": True
    },
    {
        "name": "Firefox",
        "versions": ["112.0", "113.0", "124.0"],
        "platforms": ["Windows NT 10.0; Win64; x64", "Macintosh; Intel Mac OS X 10.15"],
        "common_in_sa": True
    },
    {
        "name": "Samsung Internet",
        "versions": ["20.0", "21.0"],
        "platforms": ["Linux; Android 13; SM-G991B"],
        "common_in_sa": True
    },
    {
        "name": "Opera",
        "versions": ["97.0.4719.63", "98.0.4759.39"],
        "platforms": ["Windows NT 10.0; Win64; x64", "Linux; Android 13; SM-G998B"],
        "common_in_sa": False
    }
]

# South African ISP and network configurations
SA_NETWORK_INFO = [
    {
        "accept_language": "en-ZA,en-GB;q=0.9,en-US;q=0.8,en;q=0.7",
        "timezone": "SAST",
        "common_isps": ["Telkom", "Vodacom", "MTN", "Cell C", "Rain", "Afrihost", "RSAWEB", "Vumatel"]
    }
]

# Define various screen resolutions common in South Africa
SCREEN_RESOLUTIONS = [
    "1920x1080", "1366x768", "1536x864", "1440x900", 
    "1280x720", "1600x900", "2560x1440", "3840x2160"
]

# User behavior patterns (time intervals in seconds)
USER_BEHAVIOR_PATTERNS = [
    {"name": "typical_user", "avg_time_on_page": 45, "scroll_speed": "moderate"},
    {"name": "fast_scanner", "avg_time_on_page": 15, "scroll_speed": "fast"},
    {"name": "careful_reader", "avg_time_on_page": 120, "scroll_speed": "slow"},
    {"name": "distracted_user", "avg_time_on_page": 180, "scroll_speed": "erratic"}
]

def generate_device_id():
    """Generate a persistent device ID that looks like a real hardware identifier."""
    # Create a base string with some fixed components to ensure consistency
    base = f"SAZALOTTO-{uuid.uuid4().hex[:12]}-{random.randint(1000, 9999)}"
    return hashlib.md5(base.encode()).hexdigest()

def get_sa_browser_fingerprint():
    """Generate a realistic South African browser fingerprint."""
    # Bias toward browsers that are common in South Africa
    browser_weights = [5 if b["common_in_sa"] else 1 for b in SA_BROWSERS]
    browser = random.choices(SA_BROWSERS, weights=browser_weights, k=1)[0]
    
    # Select random version and platform
    version = random.choice(browser["versions"])
    platform = random.choice(browser["platforms"])
    
    # Generate user agent
    if browser["name"] == "Chrome":
        user_agent = f"Mozilla/5.0 ({platform}) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/{version} Safari/537.36"
    elif browser["name"] == "Firefox":
        user_agent = f"Mozilla/5.0 ({platform}; rv:{version}) Gecko/20100101 Firefox/{version}"
    elif browser["name"] == "Edge":
        user_agent = f"Mozilla/5.0 ({platform}) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/{version} Safari/537.36 Edg/{version}"
    elif browser["name"] == "Safari":
        user_agent = f"Mozilla/5.0 ({platform}) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/{version} Safari/605.1.15"
    elif browser["name"] == "Samsung Internet":
        user_agent = f"Mozilla/5.0 ({platform}) AppleWebKit/537.36 (KHTML, like Gecko) SamsungBrowser/{version} Chrome/92.0.4515.166 Mobile Safari/537.36"
    elif browser["name"] == "Opera":
        user_agent = f"Mozilla/5.0 ({platform}) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/{version} Safari/537.36 OPR/{version}"
    else:
        user_agent = f"Mozilla/5.0 ({platform}) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/{version} Safari/537.36"
    
    # South African language and locale settings
    network_info = SA_NETWORK_INFO[0]
    accept_language = network_info["accept_language"]
    
    # Generate screen resolution
    resolution = random.choice(SCREEN_RESOLUTIONS)
    width, height = map(int, resolution.split('x'))
    
    # Device memory and processor info
    cores = random.choice([2, 4, 6, 8, 12, 16])
    memory = random.choice([2, 4, 8, 16, 32])
    
    # Generate persistent device ID
    device_id = generate_device_id()
    
    return {
        "user_agent": user_agent,
        "accept_language": accept_language,
        "browser_name": browser["name"],
        "browser_version": version,
        "platform": platform,
        "screen_width": width,
        "screen_height": height,
        "color_depth": random.choice([24, 32]),
        "device_memory": memory,
        "hardware_concurrency": cores,
        "timezone": random.choice(["Africa/Johannesburg"]),
        "timezone_offset": 120,  # +2 hours for South Africa
        "device_id": device_id,
        "connection": {
            "type": random.choice(["wifi", "4g", "fiber"]),
            "isp": random.choice(network_info["common_isps"])
        }
    }

def generate_cookie_data(url, fingerprint):
    """Generate realistic cookie data based on the URL and fingerprint."""
    domain = urlparse(url).netloc
    now = datetime.now()
    visit_id = hashlib.md5(f"{fingerprint['device_id']}-{now.strftime('%Y%m%d')}".encode()).hexdigest()
    
    # Basic cookies that most sites would have
    from datetime import timedelta
    
    cookies = {
        "visited": "true",
        "visitor_id": fingerprint["device_id"][:16],
        "session_id": f"sess_{int(time.time())}_{random.randint(1000, 9999)}",
        "first_visit": (now - timedelta(days=random.randint(1, 365))).strftime("%Y-%m-%d"),
        "visit_count": str(random.randint(1, 30)),
        "last_visit": now.strftime("%Y-%m-%d"),
        "screen_res": f"{fingerprint['screen_width']}x{fingerprint['screen_height']}",
        "timezone": fingerprint["timezone"],
        "sa_returning_visitor": "true",
        "za_lottery_site": "true",
        "gdpr_accepted": "true",
        "_ga": f"GA1.2.{random.randint(100000000, 999999999)}.{int(time.time())-random.randint(1000000, 9999999)}",
        "_gid": f"GA1.2.{random.randint(100000000, 999999999)}.{int(time.time())}",
        "visit_id": visit_id
    }
    
    # Add domain-specific cookies with realistic names
    if "nationallottery" in domain:
        cookies.update({
            "nl_session": f"{random.randint(10000, 99999)}{random.randint(10000, 99999)}",
            "nl_visitor": fingerprint["device_id"][:10],
            "nl_lang": "en-ZA",
            "nl_region": "ZA",
            "nl_last_draw_viewed": f"{random.randint(1000, 9999)}",
            "nl_consent": "all",
            "nl_promo_viewed": random.choice(["true", "false"])
        })
    
    return cookies

def simulate_user_behavior(url):
    """Simulate human-like user behavior patterns."""
    # Choose a behavior pattern
    pattern = random.choice(USER_BEHAVIOR_PATTERNS)
    
    # Simulate time on page (with some random variation)
    base_time = pattern["avg_time_on_page"]
    variation = base_time * 0.2  # 20% variation
    time_on_page = base_time + random.uniform(-variation, variation)
    
    # Adjust for URL-specific behavior
    parsed_url = urlparse(url)
    path = parsed_url.path.lower()
    
    # Spend more time on specific pages
    if "results" in path:
        time_on_page *= 1.5  # People spend more time on results pages
    elif "history" in path:
        time_on_page *= 2.0  # People spend even more time on history pages
    
    # Log user behavior (for debugging)
    logger.debug(f"Simulating '{pattern['name']}' behavior pattern")
    logger.debug(f"Time on page: {time_on_page:.1f} seconds")
    logger.debug(f"Scroll speed: {pattern['scroll_speed']}")
    
    return {
        "pattern": pattern["name"],
        "time_on_page": time_on_page,
        "scroll_speed": pattern["scroll_speed"]
    }

def save_screenshot_data(url, lottery_type, html_content):
    """Save captured screenshot data to disk and database."""
    # Generate unique filenames
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    safe_name = lottery_type.replace(' ', '_')
    filename = f"{safe_name}_{timestamp}.html"
    filepath = os.path.join(SCREENSHOT_DIR, filename)
    
    # Save HTML content to file
    with open(filepath, 'wb') as f:
        f.write(html_content)
    
    logger.info(f"Saved {lottery_type} HTML to {filepath}")
    
    # Save to database if models are available
    if HAS_MODELS:
        try:
            # Check if we need to create an app context
            if not has_app_context():
                # Import app here to avoid circular imports
                from main import app
                with app.app_context():
                    return save_to_db(url, lottery_type, filepath)
            else:
                return save_to_db(url, lottery_type, filepath)
        except Exception as e:
            logger.error(f"Database error: {str(e)}")
    
    return filepath, None

def save_to_db(url, lottery_type, filepath):
    """Save the screenshot to the database."""
    try:
        # Import models inside the function to avoid circular imports
        from models import db, Screenshot
        
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
        return filepath, screenshot.id
    except Exception as e:
        logger.error(f"Database error when saving screenshot: {str(e)}")
        return filepath, None

def capture(lottery_type, url, retry_count=0):
    """
    Enhanced capture function with advanced anti-bot measures.
    
    Args:
        lottery_type (str): The type of lottery
        url (str): The URL to capture
        retry_count (int): Number of retry attempts
        
    Returns:
        bool: Success or failure
    """
    # Max retries
    max_retries = 3
    if retry_count >= max_retries:
        logger.error(f"Maximum retry count ({max_retries}) reached for {lottery_type}")
        return False
    
    # Generate realistic browser fingerprint
    fingerprint = get_sa_browser_fingerprint()
    
    # Generate realistic cookies
    cookies = generate_cookie_data(url, fingerprint)
    
    # Simulate user behavior
    behavior = simulate_user_behavior(url)
    
    # Prepare headers with fingerprint data
    headers = {
        'User-Agent': fingerprint["user_agent"],
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
        'Accept-Language': fingerprint["accept_language"],
        'Accept-Encoding': 'gzip, deflate, br',
        'Referer': 'https://www.google.co.za/',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
        'Sec-Fetch-Dest': 'document',
        'Sec-Fetch-Mode': 'navigate',
        'Sec-Fetch-Site': 'cross-site',
        'Sec-Fetch-User': '?1',
        'DNT': '1',
        'Sec-CH-UA': f'"{fingerprint["browser_name"]}";v="{fingerprint["browser_version"]}", "Not-A.Brand";v="24"',
        'Sec-CH-UA-Mobile': '?0',
        'Sec-CH-UA-Platform': f'"{fingerprint["platform"].split(";")[0]}"',
        'Cache-Control': 'max-age=0',
        'Priority': 'high'
    }
    
    # Set up a session to handle cookies properly
    session = requests.Session()
    
    # Add cookies to the session
    for key, value in cookies.items():
        session.cookies.set(key, value)
    
    try:
        # Before the main request, visit the homepage first (more natural)
        domain = urlparse(url).scheme + "://" + urlparse(url).netloc
        logger.info(f"First visiting the homepage at {domain}")
        
        # Add a small delay before the first request to mimic human behavior
        time.sleep(random.uniform(1, 3))
        
        home_headers = headers.copy()
        home_headers['Referer'] = 'https://www.google.co.za/search?q=south+africa+lottery+results'
        
        home_response = session.get(domain, headers=home_headers, timeout=30)
        if home_response.status_code != 200:
            logger.warning(f"Homepage visit returned status code {home_response.status_code}")
        
        # Add realistic delay between requests (as if human is navigating)
        logger.info(f"Waiting {behavior['time_on_page']:.1f} seconds before visiting the target page")
        time.sleep(random.uniform(3, 7))
        
        # Update referer to the homepage
        headers['Referer'] = domain
        
        # Make the main request to the target URL
        logger.info(f"Requesting target URL: {url}")
        response = session.get(url, headers=headers, timeout=30, allow_redirects=True)
        
        if response.status_code == 200:
            # Check if we got actual content and not a bot detection page
            content_length = len(response.content)
            soup = BeautifulSoup(response.content, 'html.parser')
            title = soup.title.string if soup.title else "No title"
            
            # Help identify bot detection
            bot_indicators = [
                "captcha", "bot", "automated", "security check", "challenge",
                "suspicious", "verify", "blocked", "access denied"
            ]
            
            has_bot_indicators = any(indicator in title.lower() for indicator in bot_indicators)
            
            if has_bot_indicators or content_length < 5000:  # Very small responses are likely blocking pages
                logger.warning(f"Possible bot detection for {lottery_type}! Title: {title}, Content length: {content_length}")
                
                # Wait longer and retry with a different fingerprint
                time.sleep(random.uniform(30, 60))  # Longer cooldown period
                return capture(lottery_type, url, retry_count + 1)
            
            # Save the content
            filepath, screenshot_id = save_screenshot_data(url, lottery_type, response.content)
            
            # Extract some basic info for validation
            draw_numbers = []
            number_elements = soup.select('.ball, .lottery-ball, .number, .draw-number')
            if number_elements:
                draw_numbers = [elem.text.strip() for elem in number_elements[:7]]  # Get up to 7 numbers
            
            logger.info(f"Successfully captured {lottery_type}")
            if draw_numbers:
                logger.info(f"Extracted numbers: {', '.join(draw_numbers)}")
            return True
        else:
            logger.error(f"Failed to get {url}: {response.status_code}")
            
            # For specific error codes, handle differently
            if response.status_code == 403:  # Forbidden (likely bot detection)
                logger.warning("Received 403 Forbidden - this is likely bot detection")
                time.sleep(random.uniform(60, 120))  # Longer cooldown for 403s
            elif response.status_code in [429, 503]:  # Rate limiting or service unavailable
                logger.warning(f"Rate limiting or service issues ({response.status_code})")
                time.sleep(random.uniform(120, 180))  # Even longer cooldown for rate limits
            else:
                time.sleep(random.uniform(10, 30))
                
            return capture(lottery_type, url, retry_count + 1)
    except Exception as e:
        logger.error(f"Error capturing {url}: {e}")
        time.sleep(random.uniform(5, 15))
        return capture(lottery_type, url, retry_count + 1)

def main():
    """Main function to run the capture process."""
    # Target URLs from Config
    urls = Config.RESULTS_URLS + [
        {'url': url, 'lottery_type': url.split('/')[-1].replace('-history', '').replace('-', ' ').title() + ' History'}
        for url in Config.DEFAULT_LOTTERY_URLS
    ]
    
    # Or use a default set if Config is not available
    if not urls:
        urls = [
            {"url": "https://www.nationallottery.co.za/results/lotto", "lottery_type": "Lotto"},
            {"url": "https://www.nationallottery.co.za/results/lotto-plus-1-results", "lottery_type": "Lotto Plus 1"},
            {"url": "https://www.nationallottery.co.za/results/lotto-plus-2-results", "lottery_type": "Lotto Plus 2"},
            {"url": "https://www.nationallottery.co.za/results/powerball", "lottery_type": "Powerball"},
            {"url": "https://www.nationallottery.co.za/results/powerball-plus", "lottery_type": "Powerball Plus"},
            {"url": "https://www.nationallottery.co.za/results/daily-lotto", "lottery_type": "Daily Lotto"},
            {"url": "https://www.nationallottery.co.za/lotto-history", "lottery_type": "Lotto History"},
            {"url": "https://www.nationallottery.co.za/powerball-history", "lottery_type": "Powerball History"},
            {"url": "https://www.nationallottery.co.za/daily-lotto-history", "lottery_type": "Daily Lotto History"}
        ]
    
    # Add some randomness to the order (more human-like)
    random.shuffle(urls)
    
    # Track successes and failures
    results = {"success": [], "failure": []}
    
    # Process each URL
    for item in urls:
        lottery_type = item["lottery_type"]
        url = item["url"]
        
        logger.info(f"Attempting to capture {lottery_type} from {url}")
        
        # Add random delay between captures (very important for avoiding detection)
        if results["success"] or results["failure"]:  # Not the first request
            delay = random.uniform(30, 90)  # 30-90 second delay between captures
            logger.info(f"Waiting {delay:.1f} seconds before next capture")
            time.sleep(delay)
        
        # Attempt capture
        success = capture(lottery_type, url)
        
        if success:
            logger.info(f"✅ Successfully captured {lottery_type}")
            results["success"].append(lottery_type)
        else:
            logger.error(f"❌ Failed to capture {lottery_type}")
            results["failure"].append(lottery_type)
    
    # Report final results
    logger.info("\n" + "="*50)
    logger.info("FINAL CAPTURE RESULTS:")
    logger.info(f"Successful captures: {len(results['success'])}/{len(urls)}")
    for success in results["success"]:
        logger.info(f" ✅ {success}")
    if results["failure"]:
        logger.info(f"Failed captures: {len(results['failure'])}/{len(urls)}")
        for failure in results["failure"]:
            logger.info(f" ❌ {failure}")
    logger.info("="*50)
    
    return len(results["failure"]) == 0

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)