"""
Puppeteer Service

This module provides services for capturing screenshots of lottery websites using Puppeteer.
It relies on the puppeteer_executor.py module to execute the JavaScript code,
which avoids embedding JavaScript in Python multiline strings.
"""

import os
import logging
import time
import re
from datetime import datetime
from puppeteer_executor import capture_screenshot

logger = logging.getLogger(__name__)

def standardize_lottery_type(lottery_type):
    """
    Standardize lottery type names to ensure consistency across the application.
    This helps reduce duplicate entries in the screenshot gallery.
    
    Args:
        lottery_type (str): Original lottery type name
        
    Returns:
        str: Standardized lottery type name
    """
    if not lottery_type:
        return "unknown"
        
    # Convert to lowercase for case-insensitive matching
    ltype = lottery_type.lower()
    
    # Standardize naming for lottery types using regex patterns
    if re.search(r'daily.*lott', ltype):
        return "Daily Lotto"
    elif re.search(r'powerball.*plus', ltype) or re.search(r'power.*ball.*\+', ltype):
        return "Powerball Plus"
    elif re.search(r'powerball|power.*ball', ltype):
        return "Powerball"
    elif re.search(r'lott[oe].*plus.*2|lott[oe].*\+.*2', ltype):
        return "Lotto Plus 2"
    elif re.search(r'lott[oe].*plus.*1|lott[oe].*\+.*1', ltype):
        return "Lotto Plus 1"
    elif re.search(r'lott[oe]', ltype) and not re.search(r'plus|results|\+', ltype):
        return "Lotto"
    
    # If none of the patterns match, clean up the original name
    return lottery_type.replace('_', ' ').title()

# Define the lottery URLs - this is a fallback in case the database has no URLs configured
LOTTERY_URLS = {
    'lotto': 'https://www.nationallottery.co.za/lotto-results',
    'lotto_plus_1': 'https://www.nationallottery.co.za/lotto-plus-1-results',
    'lotto_plus_2': 'https://www.nationallottery.co.za/lotto-plus-2-results',
    'powerball': 'https://www.nationallottery.co.za/powerball-results',
    'powerball_plus': 'https://www.nationallottery.co.za/powerball-plus-results',
    'daily_lotto': 'https://www.nationallottery.co.za/daily-lotto-results'
}

# Create standardized versions of the lottery URLs
STANDARDIZED_LOTTERY_URLS = {}
for key, url in LOTTERY_URLS.items():
    # Get standardized name
    standard_name = standardize_lottery_type(key.replace('_', ' '))
    # Create key in standardized format
    standardized_key = standard_name.lower().replace(' ', '_')
    # Add to standardized dictionary
    STANDARDIZED_LOTTERY_URLS[standardized_key] = url

def capture_single_screenshot(lottery_type, url, timeout=120):
    """
    Capture a single screenshot of a lottery URL using the puppeteer_executor module.
    
    Args:
        lottery_type (str): Type of lottery (used for filename)
        url (str): URL to capture
        timeout (int): Timeout in seconds
        
    Returns:
        dict: Result with status, paths and any errors
    """
    try:
        # Standardize lottery type naming and formatting
        normalized_type = lottery_type.lower().replace(' ', '_')
        
        # Create timestamp for unique filenames
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        # Define output paths
        screenshot_dir = os.path.join(os.getcwd(), 'screenshots')
        html_dir = os.path.join(screenshot_dir, 'html')
        
        # Ensure directories exist
        os.makedirs(screenshot_dir, exist_ok=True)
        os.makedirs(html_dir, exist_ok=True)
        
        # Define output filenames
        screenshot_path = os.path.join(screenshot_dir, f"{normalized_type}_{timestamp}.png")
        html_path = os.path.join(html_dir, f"{normalized_type}_{timestamp}.html")
        
        logger.info(f"Capturing screenshot for {lottery_type} from {url}")
        logger.info(f"Saving to: {screenshot_path}")
        logger.info(f"Saving HTML to: {html_path}")
        
        # Call the executor function
        success = capture_screenshot(url, screenshot_path, html_path, timeout)
        
        if success:
            logger.info(f"Successfully captured {lottery_type} from {url}")
            return {
                'status': 'success',
                'path': screenshot_path,
                'html_path': html_path,
                'message': f"Successfully captured {lottery_type} screenshot"
            }
        else:
            logger.error(f"Failed to capture {lottery_type} from {url}")
            return {
                'status': 'error',
                'error': f"Failed to capture {lottery_type} screenshot",
                'message': f"Failed to capture {lottery_type} screenshot"
            }
    except Exception as e:
        logger.error(f"Error capturing {lottery_type} screenshot: {str(e)}")
        return {
            'status': 'error',
            'error': str(e),
            'message': f"Error: {str(e)}"
        }

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