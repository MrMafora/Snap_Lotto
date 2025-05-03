#!/usr/bin/env python3
"""
Enhanced single URL lottery screenshot capture script with advanced anti-bot measures.
This script captures a single URL with advanced anti-bot measures, allowing for faster testing.
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
from datetime import datetime, timedelta
from urllib.parse import urlparse
from bs4 import BeautifulSoup
from pathlib import Path
import argparse

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

def generate_device_id():
    """Generate a persistent device ID that looks like a real hardware identifier."""
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
    else:
        user_agent = f"Mozilla/5.0 ({platform}) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/{version} Safari/537.36"
    
    # South African language and locale settings
    network_info = SA_NETWORK_INFO[0]
    accept_language = network_info["accept_language"]
    
    return {
        "user_agent": user_agent,
        "accept_language": accept_language,
        "browser_name": browser["name"],
        "browser_version": version,
        "platform": platform,
        "device_id": generate_device_id(),
        "timezone": random.choice(["Africa/Johannesburg"]),
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
    cookies = {
        "visited": "true",
        "visitor_id": fingerprint["device_id"][:16],
        "session_id": f"sess_{int(time.time())}_{random.randint(1000, 9999)}",
        "first_visit": (now - timedelta(days=random.randint(1, 365))).strftime("%Y-%m-%d"),
        "visit_count": str(random.randint(1, 30)),
        "last_visit": now.strftime("%Y-%m-%d"),
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

def normalize_lottery_type(url):
    """Normalize the lottery type based on the URL."""
    path = urlparse(url).path.lower()
    
    # Extract the lottery type from the URL path
    parts = path.split('/')
    last_part = parts[-1] if parts and parts[-1] else ""
    
    # Handle specific cases
    if "lotto-plus-1" in path:
        return "Lottery Plus 1"
    elif "lotto-plus-2" in path:
        return "Lottery Plus 2"
    elif "lotto-history" in path or "lotto-results" in path or last_part == "lotto":
        return "Lottery"
    elif "powerball-plus" in path:
        return "Powerball Plus"
    elif "powerball" in path:
        return "Powerball"
    elif "daily-lotto" in path:
        return "Daily Lottery"
    
    # For history pages
    if "history" in path:
        base_type = normalize_lottery_type(url.replace("-history", ""))
        return f"{base_type} History"
    
    # If we couldn't determine the type, use a generic name based on the URL
    name = last_part.replace('-', ' ').title()
    # Convert "Lotto" to "Lottery" for consistency
    name = name.replace("Lotto", "Lottery")
    return name

def capture_single_url(url, lottery_type=None, retry_count=0):
    """
    Capture a single URL with enhanced anti-bot measures.
    
    Args:
        url: The URL to capture
        lottery_type: Optional lottery type, will be inferred from URL if not provided
        retry_count: Number of times this URL has been retried
    
    Returns:
        tuple: (success, filepath, content)
    """
    # Determine lottery type if not provided
    if not lottery_type:
        lottery_type = normalize_lottery_type(url)
    
    logger.info(f"Attempting to capture {lottery_type} from {url}")
    
    # Max retries check
    max_retries = 3
    if retry_count >= max_retries:
        logger.error(f"Maximum retry count ({max_retries}) reached for {lottery_type}")
        return False, None, None
    
    # Generate realistic browser fingerprint
    fingerprint = get_sa_browser_fingerprint()
    
    # Generate realistic cookies
    cookies = generate_cookie_data(url, fingerprint)
    
    # Add human-like browsing delays
    browsing_delay = random.uniform(3, 7)
    
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
        logger.info(f"Waiting {browsing_delay:.1f} seconds before visiting the target page")
        time.sleep(browsing_delay)
        
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
            
            if title and any(indicator in title.lower() for indicator in bot_indicators):
                logger.warning(f"Possible bot detection for {lottery_type}! Title: {title}, Content length: {content_length}")
                # Wait longer and retry with a different fingerprint
                time.sleep(random.uniform(10, 20))  # Shorter cooldown for this single-page version
                return capture_single_url(url, lottery_type, retry_count + 1)
            
            # Save content to file
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            safe_name = lottery_type.replace(' ', '_')
            filename = f"{safe_name}_{timestamp}.html"
            filepath = os.path.join(SCREENSHOT_DIR, filename)
            
            with open(filepath, 'wb') as f:
                f.write(response.content)
            
            logger.info(f"✅ Successfully captured {lottery_type} and saved to {filepath}")
            
            # Extract some basic info for validation
            draw_numbers = []
            number_elements = soup.select('.ball, .lottery-ball, .number, .draw-number')
            if number_elements:
                draw_numbers = [elem.text.strip() for elem in number_elements[:7]]  # Get up to 7 numbers
                logger.info(f"Extracted numbers: {', '.join(draw_numbers)}")
            
            return True, filepath, response.content
        else:
            logger.error(f"Failed to get {url}: {response.status_code}")
            
            # For specific error codes, handle differently
            if response.status_code == 403:  # Forbidden (likely bot detection)
                logger.warning("Received 403 Forbidden - this is likely bot detection")
                time.sleep(random.uniform(20, 40))  # Shorter cooldown for 403s in this version
            elif response.status_code in [429, 503]:  # Rate limiting or service unavailable
                logger.warning(f"Rate limiting or service issues ({response.status_code})")
                time.sleep(random.uniform(30, 60))  # Shorter cooldown for rate limits
            else:
                time.sleep(random.uniform(5, 15))
                
            return capture_single_url(url, lottery_type, retry_count + 1)
    except Exception as e:
        logger.error(f"Error capturing {url}: {e}")
        time.sleep(random.uniform(3, 8))
        return capture_single_url(url, lottery_type, retry_count + 1)

def main():
    """Main function to parse command line arguments and run the capture."""
    parser = argparse.ArgumentParser(description='Capture a lottery website screenshot with enhanced anti-bot measures.')
    parser.add_argument('--url', '-u', type=str, help='URL to capture')
    parser.add_argument('--type', '-t', type=str, help='Lottery type (optional, will be inferred from URL if not provided)')
    parser.add_argument('--test-all', action='store_true', help='Test all default URLs (one at a time)')
    
    args = parser.parse_args()
    
    # Define default URLs to test if --test-all is specified
    default_urls = [
        "https://www.nationallottery.co.za/results/lotto",
        "https://www.nationallottery.co.za/results/lotto-plus-1-results",
        "https://www.nationallottery.co.za/results/lotto-plus-2-results",
        "https://www.nationallottery.co.za/results/powerball",
        "https://www.nationallottery.co.za/results/powerball-plus",
        "https://www.nationallottery.co.za/results/daily-lotto",
        "https://www.nationallottery.co.za/lotto-history",
        "https://www.nationallottery.co.za/powerball-history",
        "https://www.nationallottery.co.za/daily-lotto-history"
    ]
    
    if args.test_all:
        # Test all URLs one at a time with delays between them
        success_count = 0
        for i, url in enumerate(default_urls):
            logger.info(f"Testing URL {i+1}/{len(default_urls)}: {url}")
            
            # Add longer delay between captures
            if i > 0:
                delay = random.uniform(15, 30)  # 15-30 second delay between captures
                logger.info(f"Waiting {delay:.1f} seconds before next capture...")
                time.sleep(delay)
            
            success, filepath, _ = capture_single_url(url)
            if success:
                success_count += 1
        
        logger.info(f"\nCapture test complete. Successfully captured {success_count}/{len(default_urls)} URLs.")
        return success_count == len(default_urls)
    
    elif args.url:
        # Capture a single URL
        success, filepath, _ = capture_single_url(args.url, args.type)
        return success
    
    else:
        parser.print_help()
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)