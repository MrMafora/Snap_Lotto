"""
Enhanced Puppeteer Service
This module provides functions to capture screenshots of websites using Puppeteer,
with comprehensive anti-detection measures to bypass website protection mechanisms.
"""

import os
import subprocess
import logging
import random
import json
from datetime import datetime

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Dictionary of lottery URLs - will be used for fallback
LOTTERY_URLS = {
    'Lotto': 'https://www.nationallottery.co.za/lotto-history',
    'Lotto Plus 1': 'https://www.nationallottery.co.za/lotto-plus-1-history',
    'Lotto Plus 2': 'https://www.nationallottery.co.za/lotto-plus-2-history',
    'Powerball': 'https://www.nationallottery.co.za/powerball-history',
    'Powerball Plus': 'https://www.nationallottery.co.za/powerball-plus-history',
    'Daily Lotto': 'https://www.nationallottery.co.za/daily-lotto-history',
    # Latest results URLs
    'Latest Lotto': 'https://www.nationallottery.co.za/results/lotto',
    'Latest Lotto Plus 1': 'https://www.nationallottery.co.za/results/lotto-plus-1-results',
    'Latest Lotto Plus 2': 'https://www.nationallottery.co.za/results/lotto-plus-2-results',
    'Latest Powerball': 'https://www.nationallottery.co.za/results/powerball',
    'Latest Powerball Plus': 'https://www.nationallottery.co.za/results/powerball-plus',
    'Latest Daily Lotto': 'https://www.nationallottery.co.za/results/daily-lotto'
}

def capture_single_screenshot(url, output_path, html_path, timeout=120):
    """
    Capture a screenshot of a webpage using Puppeteer with anti-detection measures.
    
    Args:
        url (str): URL to capture
        output_path (str): Path to save the screenshot
        html_path (str): Path to save the HTML content
        timeout (int): Timeout in seconds
        
    Returns:
        bool: Success status
    """
    logger.info(f"Capturing screenshot of {url} with Puppeteer")
    
    try:
        # Ensure directories exist
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        os.makedirs(os.path.dirname(html_path), exist_ok=True)
        
        # Run the Node.js script with arguments
        cmd = [
            'node', 'puppeteer_script.js',
            url, output_path, html_path
        ]
        
        # Run the command with a timeout
        result = subprocess.run(
            cmd, 
            stdout=subprocess.PIPE, 
            stderr=subprocess.PIPE,
            text=True,
            timeout=timeout
        )
        
        # Check if the command was successful
        if result.returncode == 0:
            logger.info(f"Successfully captured screenshot: {output_path}")
            logger.info(f"Successfully saved HTML: {html_path}")
            return True
        else:
            logger.error(f"Failed to capture screenshot. Exit code: {result.returncode}")
            logger.error(f"Stdout: {result.stdout}")
            logger.error(f"Stderr: {result.stderr}")
            return False
        
    except subprocess.TimeoutExpired:
        logger.error(f"Timeout expired while capturing screenshot of {url}")
        return False
    except Exception as e:
        logger.error(f"Error capturing screenshot: {str(e)}")
        return False

def capture_all_screenshots(output_dir='screenshots', timeout=120):
    """
    Capture screenshots for all lottery types.
    
    Args:
        output_dir (str): Directory to save screenshots
        timeout (int): Timeout for each capture in seconds
        
    Returns:
        dict: Results with success/failure for each URL
    """
    logger.info("Starting batch screenshot capture for all lottery types")
    
    results = {}
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Ensure output directories exist
    screenshots_dir = os.path.join(os.getcwd(), output_dir)
    html_dir = os.path.join(screenshots_dir, 'html')
    os.makedirs(screenshots_dir, exist_ok=True)
    os.makedirs(html_dir, exist_ok=True)
    
    # Process each URL
    for lottery_type, url in LOTTERY_URLS.items():
        try:
            logger.info(f"Processing {lottery_type}: {url}")
            
            # Generate filenames
            safe_filename = lottery_type.replace(' ', '_').replace('/', '_').lower()
            screenshot_path = os.path.join(screenshots_dir, f"{timestamp}_{safe_filename}.png")
            html_path = os.path.join(html_dir, f"{timestamp}_{safe_filename}.html")
            
            # Capture the screenshot
            success = capture_single_screenshot(url, screenshot_path, html_path, timeout)
            
            results[lottery_type] = {
                'url': url,
                'success': success,
                'screenshot_path': screenshot_path if success else None,
                'html_path': html_path if success else None,
                'timestamp': timestamp
            }
            
        except Exception as e:
            logger.error(f"Error processing {lottery_type}: {str(e)}")
            results[lottery_type] = {
                'url': url,
                'success': False,
                'error': str(e)
            }
    
    logger.info(f"Completed batch screenshot capture. Success rate: {sum(1 for r in results.values() if r.get('success', False))}/{len(results)}")
    return results

if __name__ == "__main__":
    # Test by capturing a single screenshot
    test_url = "https://www.nationallottery.co.za/lotto-history"
    output_dir = 'screenshots'
    os.makedirs(output_dir, exist_ok=True)
    os.makedirs(os.path.join(output_dir, 'html'), exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    screenshot_path = os.path.join(output_dir, f"{timestamp}_test.png")
    html_path = os.path.join(output_dir, 'html', f"{timestamp}_test.html")
    
    success = capture_single_screenshot(test_url, screenshot_path, html_path)
    print(f"Test capture success: {success}")