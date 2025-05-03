#!/usr/bin/env python3
"""
Script to capture lottery screenshots using requests and BeautifulSoup.
This is a fallback mechanism when Playwright is not available.
"""
import os
import sys
import time
import random
import logging
from datetime import datetime
import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse
import hashlib

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger("capture_with_requests")

# Ensure directories exist
SCREENSHOT_DIR = os.path.join(os.getcwd(), 'screenshots')
os.makedirs(SCREENSHOT_DIR, exist_ok=True)

# User agents list (modern browsers)
USER_AGENTS = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:124.0) Gecko/20100101 Firefox/124.0',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:124.0) Gecko/20100101 Firefox/124.0',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Edge/124.0.0.0 Safari/537.36',
]

def capture_screenshot(url, lottery_type, save_to_db=True):
    """
    Capture a webpage using requests and BeautifulSoup.
    
    Args:
        url (str): URL to capture
        lottery_type (str): Type of lottery
        save_to_db (bool): Whether to save to database
        
    Returns:
        tuple: (filepath, success) or (None, False) on failure
    """
    try:
        logger.info(f"Starting capture for {lottery_type} from {url}")
        
        # Create safe filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_name = lottery_type.replace(' ', '_').replace('/', '_')
        filename = f"{safe_name}_{timestamp}_{hashlib.md5(url.encode()).hexdigest()[:8]}.html"
        filepath = os.path.join(SCREENSHOT_DIR, filename)
        
        # Set up headers to mimic a browser
        user_agent = random.choice(USER_AGENTS)
        headers = {
            'User-Agent': user_agent,
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Cache-Control': 'max-age=0',
            'TE': 'Trailers',
            'Pragma': 'no-cache'
        }
        
        # Add a delay before sending the request
        delay = random.uniform(1.0, 3.0)
        logger.info(f"Waiting {delay:.2f} seconds before request...")
        time.sleep(delay)
        
        # Send the request with increased timeout
        logger.info(f"Sending request to {url} with User-Agent: {user_agent}")
        response = requests.get(url, headers=headers, timeout=60)
        
        # Check if request was successful
        if response.status_code != 200:
            logger.error(f"Failed to retrieve {url}: HTTP {response.status_code}")
            return None, False
        
        html_content = response.text
        
        # Parse the HTML with BeautifulSoup to check if it's valid
        soup = BeautifulSoup(html_content, 'html.parser')
        title = soup.title.string if soup.title else "No title"
        logger.info(f"Retrieved page with title: {title}")
        
        # Save the HTML content
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(html_content)
            
        logger.info(f"Saved HTML content to {filepath}")
        
        # Save to database if requested
        if save_to_db:
            try:
                from main import app
                from screenshot_manager import save_screenshot_to_database
                
                with app.app_context():
                    screenshot_id = save_screenshot_to_database(url, lottery_type, filepath, None)
                    logger.info(f"Saved to database with ID {screenshot_id}")
            except Exception as e:
                logger.error(f"Error saving to database: {str(e)}")
        
        return filepath, True
        
    except Exception as e:
        logger.error(f"Error capturing {url}: {str(e)}")
        return None, False

def capture_all_missing():
    """Capture all missing lottery types using requests."""
    # Define the lottery types and their URLs
    lottery_configs = [
        {"type": "Lotto", "url": "https://www.nationallottery.co.za/results/lotto"},
        {"type": "Lotto Plus 1", "url": "https://www.nationallottery.co.za/results/lotto-plus-1-results"},
        {"type": "Lotto Plus 2", "url": "https://www.nationallottery.co.za/results/lotto-plus-2-results"},
        {"type": "Powerball", "url": "https://www.nationallottery.co.za/results/powerball"},
        {"type": "Powerball Plus", "url": "https://www.nationallottery.co.za/results/powerball-plus"},
        {"type": "Daily Lotto", "url": "https://www.nationallottery.co.za/results/daily-lotto"}
    ]
    
    # Get existing screenshots
    try:
        from main import app
        from models import Screenshot
        from data_aggregator import normalize_lottery_type
        
        with app.app_context():
            existing_types_query = Screenshot.query.with_entities(Screenshot.lottery_type).distinct().all()
            existing_normalized = [normalize_lottery_type(lt[0]) for lt in existing_types_query]
            
            logger.info(f"Existing normalized lottery types: {existing_normalized}")
            
            # Filter to only missing types
            missing_configs = []
            for config in lottery_configs:
                normalized_type = config["type"]
                # Apply our own normalization to match
                if "lotto" in normalized_type.lower() and "daily" not in normalized_type.lower():
                    normalized_type = normalized_type.replace("Lotto", "Lottery")
                elif "daily lotto" in normalized_type.lower():
                    normalized_type = "Daily Lottery"
                    
                if normalized_type not in existing_normalized:
                    missing_configs.append(config)
            
            if not missing_configs:
                logger.info("No missing lottery types! All 6 required types already have screenshots.")
                return
            
            logger.info(f"Found {len(missing_configs)} missing lottery types: {[c['type'] for c in missing_configs]}")
            
            # Capture each missing type
            success_count = 0
            for config in missing_configs:
                lottery_type = config["type"]
                url = config["url"]
                
                logger.info(f"Capturing {lottery_type} from {url}")
                filepath, success = capture_screenshot(url, lottery_type)
                
                if success:
                    logger.info(f"Successfully captured {lottery_type}")
                    success_count += 1
                else:
                    logger.error(f"Failed to capture {lottery_type}")
                
                # Add a delay between captures
                if config != missing_configs[-1]:
                    delay = random.uniform(5.0, 10.0)
                    logger.info(f"Waiting {delay:.2f} seconds before next capture...")
                    time.sleep(delay)
            
            logger.info(f"Capture complete. Captured {success_count} out of {len(missing_configs)} missing types.")
            
    except Exception as e:
        logger.error(f"Error in capture_all_missing: {str(e)}")

if __name__ == "__main__":
    logger.info("Starting capture of missing lottery screenshots using requests")
    capture_all_missing()
    logger.info("Capture process finished")