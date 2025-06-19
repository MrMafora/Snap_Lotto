#!/usr/bin/env python3
"""
Direct URL to PNG Screenshot Capture
Captures PNG screenshots from provided SA National Lottery URLs
"""

import os
import time
import logging
from datetime import datetime
from playwright.sync_api import sync_playwright

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# SA National Lottery URLs
LOTTERY_URLS = [
    {'url': 'https://www.nationallottery.co.za/results/lotto', 'lottery_type': 'Lotto'},
    {'url': 'https://www.nationallottery.co.za/results/lotto-plus-1-results', 'lottery_type': 'Lotto Plus 1'},
    {'url': 'https://www.nationallottery.co.za/results/lotto-plus-2-results', 'lottery_type': 'Lotto Plus 2'},
    {'url': 'https://www.nationallottery.co.za/results/powerball', 'lottery_type': 'Powerball'},
    {'url': 'https://www.nationallottery.co.za/results/powerball-plus', 'lottery_type': 'Powerball Plus'},
    {'url': 'https://www.nationallottery.co.za/results/daily-lotto', 'lottery_type': 'Daily Lotto'}
]

def capture_url_screenshot(url, lottery_type):
    """Capture PNG screenshot from lottery URL using Playwright"""
    try:
        logger.info(f"Capturing PNG screenshot for {lottery_type} from {url}")
        
        # Generate filename
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        safe_lottery_type = lottery_type.lower().replace(' ', '_').replace('+', '_plus_')
        filename = f"{timestamp}_{safe_lottery_type}_url.png"
        
        # Ensure screenshots directory exists
        screenshot_dir = os.path.join(os.getcwd(), 'screenshots')
        os.makedirs(screenshot_dir, exist_ok=True)
        filepath = os.path.join(screenshot_dir, filename)
        
        with sync_playwright() as p:
            # Launch browser
            browser = p.chromium.launch(headless=True)
            context = browser.new_context(
                viewport={'width': 1920, 'height': 1080},
                user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
            )
            page = context.new_page()
            
            # Navigate to URL
            page.goto(url, wait_until='networkidle', timeout=60000)
            
            # Wait for content to load
            page.wait_for_timeout(3000)
            
            # Take screenshot
            page.screenshot(path=filepath, full_page=True)
            
            browser.close()
        
        # Check if file was created
        if os.path.exists(filepath):
            file_size = os.path.getsize(filepath)
            logger.info(f"PNG screenshot captured: {filename} ({file_size} bytes)")
            return {
                'lottery_type': lottery_type,
                'url': url,
                'filepath': filepath,
                'filename': filename,
                'status': 'success'
            }
        else:
            logger.error(f"Failed to create PNG screenshot for {lottery_type}")
            return {
                'lottery_type': lottery_type,
                'url': url,
                'filepath': None,
                'filename': None,
                'status': 'failed'
            }
            
    except Exception as e:
        logger.error(f"Error capturing PNG screenshot for {lottery_type}: {str(e)}")
        return {
            'lottery_type': lottery_type,
            'url': url,
            'filepath': None,
            'filename': None,
            'status': 'error',
            'error': str(e)
        }

def run_url_screenshot_capture():
    """Run PNG screenshot capture for all lottery URLs"""
    logger.info("=== URL PNG SCREENSHOT CAPTURE STARTED ===")
    
    results = []
    successful_captures = 0
    
    for i, url_config in enumerate(LOTTERY_URLS):
        # Add delay between captures
        if i > 0:
            delay = 5 + i  # Progressive delay
            logger.info(f"Waiting {delay} seconds before next capture...")
            time.sleep(delay)
        
        # Capture PNG screenshot from URL
        result = capture_url_screenshot(url_config['url'], url_config['lottery_type'])
        results.append(result)
        
        if result and result['status'] == 'success':
            successful_captures += 1
    
    logger.info("=== URL PNG SCREENSHOT CAPTURE COMPLETED ===")
    logger.info(f"Successfully captured {successful_captures}/{len(LOTTERY_URLS)} PNG screenshots")
    
    return results

if __name__ == "__main__":
    results = run_url_screenshot_capture()
    print(f"Captured {len([r for r in results if r and r['status'] == 'success'])} PNG screenshots")