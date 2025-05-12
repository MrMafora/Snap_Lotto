"""
Puppeteer Service

This module provides services for capturing screenshots of lottery websites using Puppeteer.
It relies on the puppeteer_executor.py module to execute the JavaScript code,
which avoids embedding JavaScript in Python multiline strings.
"""

import os
import logging
import time
from datetime import datetime
from puppeteer_executor import capture_screenshot

logger = logging.getLogger(__name__)

# Define the lottery URLs - this is a fallback in case the database has no URLs configured
LOTTERY_URLS = {
    'lotto': 'https://www.nationallottery.co.za/lotto-results',
    'lotto_plus_1': 'https://www.nationallottery.co.za/lotto-plus-1-results',
    'lotto_plus_2': 'https://www.nationallottery.co.za/lotto-plus-2-results',
    'powerball': 'https://www.nationallottery.co.za/powerball-results',
    'powerball_plus': 'https://www.nationallottery.co.za/powerball-plus-results',
    'daily_lotto': 'https://www.nationallottery.co.za/daily-lotto-results'
}

def capture_single_screenshot(url, output_path, html_path, timeout=120):
    """
    Capture a single screenshot of a URL using the puppeteer_executor module.
    
    Args:
        url (str): URL to capture
        output_path (str): Path to save the screenshot
        html_path (str): Path to save the HTML content
        timeout (int): Timeout in seconds
        
    Returns:
        bool: Success status
    """
    # Ensure output directories exist
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    os.makedirs(os.path.dirname(html_path), exist_ok=True)
    
    return capture_screenshot(url, output_path, html_path, timeout)

def process_lottery_screenshots(urls, screenshot_dir):
    """
    Process multiple lottery screenshots.
    
    Args:
        urls (dict): Dictionary mapping lottery types to URLs
        screenshot_dir (str): Directory to save screenshots
        
    Returns:
        dict: Results by lottery type
    """
    # Ensure screenshot directory exists
    os.makedirs(screenshot_dir, exist_ok=True)
    
    start_time = time.time()
    logger.info(f"Starting lottery screenshot processing at {datetime.now()}")
    
    results = {}
    
    # Process each lottery type
    for lottery_type, url in urls.items():
        try:
            logger.info(f"Processing screenshots for {lottery_type} from {url}")
            
            # Define output paths
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"{lottery_type}_results_{timestamp}.png"
            html_filename = f"{lottery_type}_results_{timestamp}.html"
            output_path = os.path.join(screenshot_dir, filename)
            html_path = os.path.join(screenshot_dir, html_filename)
            
            # Capture screenshot
            success = capture_single_screenshot(url, output_path, html_path)
            
            # Record result
            results[lottery_type] = {
                'success': success,
                'url': url,
                'screenshot_path': output_path if success else None,
                'html_path': html_path if success else None,
                'timestamp': timestamp
            }
            
            if success:
                logger.info(f"Successfully processed {lottery_type} screenshot")
            else:
                logger.error(f"Failed to process {lottery_type} screenshot")
                
        except Exception as e:
            logger.exception(f"Error processing {lottery_type} screenshot: {str(e)}")
            results[lottery_type] = {
                'success': False,
                'url': url,
                'error': str(e),
                'timestamp': datetime.now().strftime('%Y%m%d_%H%M%S')
            }
    
    elapsed_time = time.time() - start_time
    logger.info(f"Completed lottery screenshot processing in {elapsed_time:.2f} seconds")
    
    return results