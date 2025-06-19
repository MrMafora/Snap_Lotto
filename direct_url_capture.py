#!/usr/bin/env python3
"""
Direct URL Screenshot Capture System
Captures screenshots from SA National Lottery URLs
"""

import os
import time
import logging
import subprocess
from datetime import datetime

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

def capture_url_screenshot_wkhtmltopdf(url, lottery_type):
    """Capture PNG screenshot from URL using wkhtmltopdf"""
    try:
        logger.info(f"Capturing screenshot for {lottery_type} from {url}")
        
        # Generate filename
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        safe_lottery_type = lottery_type.lower().replace(' ', '_').replace('+', '_plus_')
        filename = f"{timestamp}_{safe_lottery_type}_direct.png"
        
        # Ensure screenshots directory exists
        screenshot_dir = os.path.join(os.getcwd(), 'screenshots')
        os.makedirs(screenshot_dir, exist_ok=True)
        filepath = os.path.join(screenshot_dir, filename)
        
        # Use wkhtmltoimage to capture screenshot
        cmd = [
            'wkhtmltoimage',
            '--width', '1920',
            '--height', '1080',
            '--format', 'png',
            '--quality', '100',
            '--javascript-delay', '3000',
            '--load-error-handling', 'ignore',
            '--load-media-error-handling', 'ignore',
            url,
            filepath
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
        
        if result.returncode == 0 and os.path.exists(filepath):
            file_size = os.path.getsize(filepath)
            logger.info(f"Screenshot captured: {filename} ({file_size} bytes)")
            return {
                'lottery_type': lottery_type,
                'url': url,
                'filepath': filepath,
                'filename': filename,
                'status': 'success'
            }
        else:
            logger.error(f"Failed to capture screenshot for {lottery_type}: {result.stderr}")
            return {
                'lottery_type': lottery_type,
                'url': url,
                'filepath': None,
                'filename': None,
                'status': 'failed',
                'error': result.stderr
            }
            
    except Exception as e:
        logger.error(f"Error capturing screenshot for {lottery_type}: {str(e)}")
        return {
            'lottery_type': lottery_type,
            'url': url,
            'filepath': None,
            'filename': None,
            'status': 'error',
            'error': str(e)
        }

def capture_url_screenshot_curl(url, lottery_type):
    """Capture webpage content using curl and create a simple text file"""
    try:
        logger.info(f"Fetching content for {lottery_type} from {url}")
        
        # Generate filename
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        safe_lottery_type = lottery_type.lower().replace(' ', '_').replace('+', '_plus_')
        filename = f"{timestamp}_{safe_lottery_type}_content.html"
        
        # Ensure screenshots directory exists
        screenshot_dir = os.path.join(os.getcwd(), 'screenshots')
        os.makedirs(screenshot_dir, exist_ok=True)
        filepath = os.path.join(screenshot_dir, filename)
        
        # Use curl to fetch content
        cmd = [
            'curl',
            '-L',
            '--user-agent', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            '--connect-timeout', '30',
            '--max-time', '60',
            '-o', filepath,
            url
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
        
        if result.returncode == 0 and os.path.exists(filepath):
            file_size = os.path.getsize(filepath)
            logger.info(f"Content fetched: {filename} ({file_size} bytes)")
            return {
                'lottery_type': lottery_type,
                'url': url,
                'filepath': filepath,
                'filename': filename,
                'status': 'success'
            }
        else:
            logger.error(f"Failed to fetch content for {lottery_type}: {result.stderr}")
            return {
                'lottery_type': lottery_type,
                'url': url,
                'filepath': None,
                'filename': None,
                'status': 'failed',
                'error': result.stderr
            }
            
    except Exception as e:
        logger.error(f"Error fetching content for {lottery_type}: {str(e)}")
        return {
            'lottery_type': lottery_type,
            'url': url,
            'filepath': None,
            'filename': None,
            'status': 'error',
            'error': str(e)
        }

def run_url_capture():
    """Run URL capture for all lottery URLs"""
    logger.info("=== DIRECT URL CAPTURE STARTED ===")
    
    results = []
    successful_captures = 0
    
    for i, url_config in enumerate(LOTTERY_URLS):
        # Add delay between captures
        if i > 0:
            delay = 2
            logger.info(f"Waiting {delay} seconds before next capture...")
            time.sleep(delay)
        
        # Try wkhtmltopdf first, fallback to curl
        result = capture_url_screenshot_wkhtmltopdf(url_config['url'], url_config['lottery_type'])
        
        if result['status'] != 'success':
            logger.info(f"Fallback to curl for {url_config['lottery_type']}")
            result = capture_url_screenshot_curl(url_config['url'], url_config['lottery_type'])
        
        results.append(result)
        
        if result and result['status'] == 'success':
            successful_captures += 1
    
    logger.info("=== DIRECT URL CAPTURE COMPLETED ===")
    logger.info(f"Successfully captured {successful_captures}/{len(LOTTERY_URLS)} URLs")
    
    return results

if __name__ == "__main__":
    results = run_url_capture()
    print(f"Captured {len([r for r in results if r and r['status'] == 'success'])} URLs")