#!/usr/bin/env python3
"""
Step 2: Data Capture Module for Daily Automation
Captures fresh lottery data from official South African lottery websites using requests and BeautifulSoup
"""

import os
import time
import logging
import requests
from datetime import datetime
from bs4 import BeautifulSoup
from config import Config

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def setup_session():
    """Set up requests session with proper headers"""
    try:
        session = requests.Session()
        session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'identity',  # Disable compression to avoid encoding issues
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Cache-Control': 'no-cache',
            'Pragma': 'no-cache'
        })
        
        # Configure session settings
        session.max_redirects = 5
        
        return session
    except Exception as e:
        logger.error(f"Failed to setup requests session: {str(e)}")
        return None

def capture_lottery_data(url, lottery_type, session):
    """Capture lottery data from a URL using requests"""
    try:
        logger.info(f"Capturing {lottery_type} from {url}")
        
        # Make request with retries
        max_retries = 3
        for attempt in range(max_retries):
            try:
                response = session.get(url, timeout=45, stream=False)
                response.raise_for_status()
                break
            except Exception as e:
                if attempt == max_retries - 1:
                    raise e
                logger.warning(f"Attempt {attempt + 1} failed for {lottery_type}: {str(e)}")
                time.sleep(5)
        
        # Ensure we have content
        if not response.content:
            logger.error(f"No content received for {lottery_type}")
            return None
        
        # Parse HTML content using response.text to handle encoding properly
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Generate filename for raw HTML data
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        safe_lottery_type = lottery_type.lower().replace(' ', '_').replace('+', '_plus_')
        filename = f"{timestamp}_{safe_lottery_type}_data.html"
        
        # Ensure screenshots directory exists
        screenshot_dir = os.path.join(os.getcwd(), 'screenshots')
        os.makedirs(screenshot_dir, exist_ok=True)
        
        # Save HTML data for AI processing
        filepath = os.path.join(screenshot_dir, filename)
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(soup.prettify())
        except Exception as write_error:
            logger.warning(f"Failed to write prettified HTML, saving raw content: {write_error}")
            with open(filepath, 'w', encoding='utf-8', errors='ignore') as f:
                f.write(response.text)
        
        logger.info(f"Data captured and saved: {filename}")
        
        # Try to extract lottery numbers directly
        lottery_numbers = extract_lottery_numbers(soup, lottery_type)
        if lottery_numbers:
            logger.info(f"Found {lottery_type} numbers: {lottery_numbers}")
        
        return filepath
        
    except requests.exceptions.RequestException as e:
        logger.error(f"Network error capturing {lottery_type}: {str(e)}")
        return None
    except Exception as e:
        logger.error(f"Failed to capture {lottery_type}: {str(e)}")
        return None

def extract_lottery_numbers(soup, lottery_type):
    """Extract lottery numbers from HTML content"""
    try:
        # Look for common patterns in lottery result pages
        numbers = []
        
        # Search for number patterns in various formats
        number_patterns = [
            '.number', '.ball', '.result-number', '.winning-number',
            '[class*="number"]', '[class*="ball"]', '[class*="result"]'
        ]
        
        for pattern in number_patterns:
            elements = soup.select(pattern)
            for element in elements:
                text = element.get_text(strip=True)
                if text.isdigit() and 1 <= int(text) <= 50:
                    numbers.append(int(text))
        
        # Remove duplicates and sort
        numbers = sorted(list(set(numbers)))
        
        # Basic validation based on lottery type
        expected_count = 6 if 'lotto' in lottery_type.lower() else 5
        if len(numbers) >= expected_count:
            return numbers[:expected_count]
            
        return numbers if numbers else None
        
    except Exception as e:
        logger.error(f"Error extracting numbers from {lottery_type}: {str(e)}")
        return None

def capture_all_lottery_screenshots():
    """Capture data from all lottery URLs using requests"""
    logger.info("=== STEP 2: DATA CAPTURE STARTED ===")
    
    session = setup_session()
    if not session:
        logger.error("Failed to setup requests session")
        return False
    
    captured_count = 0
    total_urls = len(Config.RESULTS_URLS)
    
    try:
        for url_config in Config.RESULTS_URLS:
            url = url_config['url']
            lottery_type = url_config['lottery_type']
            
            filepath = capture_lottery_data(url, lottery_type, session)
            if filepath:
                captured_count += 1
            
            time.sleep(2)  # Respectful delay between requests
            
    except Exception as e:
        logger.error(f"Error during data capture: {str(e)}")
    finally:
        if session:
            session.close()
    
    success = captured_count > 0
    
    if success:
        logger.info(f"=== STEP 2: CAPTURE COMPLETED - {captured_count}/{total_urls} data files captured ===")
    else:
        logger.error("=== STEP 2: CAPTURE FAILED - No data captured ===")
        
    return success

def run_capture():
    """Run the screenshot capture process"""
    return capture_all_lottery_screenshots()

if __name__ == "__main__":
    run_capture()