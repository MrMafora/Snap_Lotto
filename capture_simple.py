#!/usr/bin/env python3
"""
Very simple script to capture a lottery screenshot using requests.
"""
import os
import logging
import requests
from datetime import datetime
import random

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Ensure directory exists
SCREENSHOT_DIR = os.path.join(os.getcwd(), 'screenshots')
os.makedirs(SCREENSHOT_DIR, exist_ok=True)

# Target URLs
urls = [
    {"type": "Lotto", "url": "https://www.nationallottery.co.za/results/lotto"},
    {"type": "Powerball", "url": "https://www.nationallottery.co.za/results/powerball"},
    {"type": "Powerball Plus", "url": "https://www.nationallottery.co.za/results/powerball-plus"},
    {"type": "Daily Lotto", "url": "https://www.nationallottery.co.za/results/daily-lotto"}
]

def capture(lottery_type, url):
    """Very simple capture function."""
    user_agents = [
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36'
    ]
    
    headers = {
        'User-Agent': random.choice(user_agents),
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Accept-Encoding': 'identity',  # Explicitly request uncompressed content
        'Connection': 'keep-alive'
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=30, allow_redirects=True)
        
        if response.status_code == 200:
            # Save to file
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            safe_name = lottery_type.replace(' ', '_')
            filename = f"{safe_name}_{timestamp}.html"
            filepath = os.path.join(SCREENSHOT_DIR, filename)
            
            with open(filepath, 'wb') as f:
                f.write(response.content)
            
            logger.info(f"Saved {lottery_type} to {filepath}")
            return True
        else:
            logger.error(f"Failed to get {url}: {response.status_code}")
            return False
    except Exception as e:
        logger.error(f"Error capturing {url}: {e}")
        return False

# Capture each lottery type
for lottery in urls:
    logger.info(f"Attempting to capture {lottery['type']} from {lottery['url']}")
    success = capture(lottery['type'], lottery['url'])
    
    if success:
        logger.info(f"✅ Successfully captured {lottery['type']}")
    else:
        logger.error(f"❌ Failed to capture {lottery['type']}")