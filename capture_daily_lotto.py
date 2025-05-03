#!/usr/bin/env python3
"""
Script to capture the Daily Lotto screenshot.
"""
import os
import logging
import requests
from datetime import datetime
import random
import hashlib
from main import app
from models import db, Screenshot

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Ensure directory exists
SCREENSHOT_DIR = os.path.join(os.getcwd(), 'screenshots')
os.makedirs(SCREENSHOT_DIR, exist_ok=True)

def capture_daily_lotto():
    """Capture the Daily Lotto screenshot."""
    lottery_type = "Daily Lotto"
    url = "https://www.nationallottery.co.za/results/daily-lotto"
    
    logger.info(f"Starting capture for {lottery_type} from {url}")
    
    # Set up headers to mimic a browser
    user_agents = [
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36'
    ]
    
    headers = {
        'User-Agent': random.choice(user_agents),
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Accept-Encoding': 'identity',  # Explicitly request uncompressed content
        'Connection': 'keep-alive',
        'Cache-Control': 'no-cache',
        'Pragma': 'no-cache'
    }
    
    try:
        # Send the request with increased timeout
        logger.info(f"Sending request to {url}")
        response = requests.get(url, headers=headers, timeout=30, allow_redirects=True)
        
        # Check if request was successful
        if response.status_code != 200:
            logger.error(f"Failed to retrieve {url}: HTTP {response.status_code}")
            return None, False
        
        # Save to file
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_name = lottery_type.replace(' ', '_')
        hash_part = hashlib.md5(url.encode()).hexdigest()[:8]
        filename = f"{safe_name}_{timestamp}_{hash_part}.html"
        filepath = os.path.join(SCREENSHOT_DIR, filename)
        
        with open(filepath, 'wb') as f:
            f.write(response.content)
            
        logger.info(f"Saved HTML content to {filepath}")
        
        # Save to database
        with app.app_context():
            # Create database record
            screenshot = Screenshot(
                lottery_type=lottery_type,
                url=url,
                path=filepath,
                processed=False
            )
            db.session.add(screenshot)
            db.session.commit()
            logger.info(f"Successfully registered {lottery_type} with ID {screenshot.id}")
            return filepath, True
        
    except Exception as e:
        logger.error(f"Error capturing {url}: {str(e)}")
        return None, False

if __name__ == "__main__":
    logger.info("Starting Daily Lotto screenshot capture")
    filepath, success = capture_daily_lotto()
    if success:
        logger.info(f"✅ Daily Lotto screenshot capture completed successfully! Saved to {filepath}")
    else:
        logger.error("❌ Failed to capture Daily Lotto screenshot")
    logger.info("Process complete")