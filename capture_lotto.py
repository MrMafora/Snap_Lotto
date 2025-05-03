#!/usr/bin/env python3
"""
Script to capture just the Lotto screenshot using requests.
"""
import os
import sys
import time
import random
import logging
from datetime import datetime
import requests
from bs4 import BeautifulSoup
import hashlib

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger("capture_lotto")

# Ensure directory exists
SCREENSHOT_DIR = os.path.join(os.getcwd(), 'screenshots')
os.makedirs(SCREENSHOT_DIR, exist_ok=True)

def capture_lotto():
    """Capture the Lotto screenshot."""
    lottery_type = "Lotto"
    url = "https://www.nationallottery.co.za/results/lotto"
    
    logger.info(f"Starting capture for {lottery_type} from {url}")
    
    # Set up headers to mimic a browser
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
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
    
    try:
        # Send the request with increased timeout but disable automatic content encoding
        logger.info(f"Sending request to {url}")
        response = requests.get(url, headers=headers, timeout=60, stream=True)
        
        # Check if request was successful
        if response.status_code != 200:
            logger.error(f"Failed to retrieve {url}: HTTP {response.status_code}")
            return False
        
        # Read the raw content
        html_content = ""
        for chunk in response.iter_content(chunk_size=8192, decode_unicode=True):
            if chunk:
                html_content += str(chunk)
        
        # Parse the HTML with BeautifulSoup to check if it's valid
        soup = BeautifulSoup(html_content, 'html.parser')
        title = soup.title.string if soup.title else "No title"
        logger.info(f"Retrieved page with title: {title}")
        
        # Create filename and save the HTML content
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{lottery_type}_{timestamp}_{hashlib.md5(url.encode()).hexdigest()[:8]}.html"
        filepath = os.path.join(SCREENSHOT_DIR, filename)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(html_content)
            
        logger.info(f"Saved HTML content to {filepath}")
        
        # Save to database
        try:
            from main import app
            from screenshot_manager import save_screenshot_to_database
            
            with app.app_context():
                screenshot_id = save_screenshot_to_database(url, lottery_type, filepath, None)
                logger.info(f"Saved to database with ID {screenshot_id}")
                return True
        except Exception as e:
            logger.error(f"Error saving to database: {str(e)}")
            return False
        
    except Exception as e:
        logger.error(f"Error capturing {url}: {str(e)}")
        return False

if __name__ == "__main__":
    logger.info("Starting Lotto screenshot capture")
    success = capture_lotto()
    if success:
        logger.info("✅ Lotto screenshot capture completed successfully!")
    else:
        logger.error("❌ Failed to capture Lotto screenshot")
    logger.info("Process complete")