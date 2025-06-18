#!/usr/bin/env python3
"""
Step 2: Screenshot Capture Module for Daily Automation
Captures authentic HTML content from official South African lottery websites
"""

import os
import time
import logging
import requests
from datetime import datetime
from config import Config

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def capture_lottery_content(url, lottery_type):
    """Capture authentic HTML content from lottery website with human-like behavior"""
    try:
        logger.info(f"Capturing {lottery_type} from {url}")
        
        # Generate filename for HTML content
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        safe_lottery_type = lottery_type.lower().replace(' ', '_').replace('+', '_plus_')
        filename = f"{timestamp}_{safe_lottery_type}.html"
        
        # Ensure screenshots directory exists
        screenshot_dir = os.path.join(os.getcwd(), 'screenshots')
        os.makedirs(screenshot_dir, exist_ok=True)
        filepath = os.path.join(screenshot_dir, filename)
        
        # Create session with human-like headers
        session = requests.Session()
        session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-ZA,en;q=0.9,en-US;q=0.8',
            'Accept-Encoding': 'identity',  # Disable compression
            'Connection': 'keep-alive',
            'Cache-Control': 'no-cache',
            'DNT': '1',
            'Upgrade-Insecure-Requests': '1'
        })
        
        # Make request with timeout
        logger.info(f"Requesting {url}")
        response = session.get(url, timeout=30)
        response.raise_for_status()
        
        # Save HTML content for AI processing
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(response.text)
        
        # Verify file was created
        if os.path.exists(filepath):
            file_size = os.path.getsize(filepath)
            logger.info(f"Content captured and saved: {filename} ({file_size} bytes)")
            return filepath
        else:
            logger.error(f"Content file was not created for {lottery_type}")
            return None
                
    except Exception as e:
        logger.error(f"Failed to capture content for {lottery_type}: {str(e)}")
        return None

def capture_all_lottery_content():
    """Capture content from all lottery result URLs with human-like behavior"""
    try:
        logger.info("=== STEP 2: CONTENT CAPTURE STARTED ===")
        
        results = []
        
        # Capture content from all result URLs with delays between requests
        for i, lottery_config in enumerate(Config.RESULTS_URLS):
            url = lottery_config['url']
            lottery_type = lottery_config['lottery_type']
            
            # Human-like delay between requests (2-5 seconds)
            if i > 0:
                delay = 3 + (i * 1)  # Increasing delay
                logger.info(f"Waiting {delay} seconds before next capture...")
                time.sleep(delay)
            
            # Capture content
            filepath = capture_lottery_content(url, lottery_type)
            
            if filepath:
                results.append({
                    'lottery_type': lottery_type,
                    'url': url,
                    'filepath': filepath,
                    'status': 'success'
                })
            else:
                results.append({
                    'lottery_type': lottery_type,
                    'url': url,
                    'filepath': None,
                    'status': 'failed'
                })
        
        # Log summary
        successful_captures = len([r for r in results if r['status'] == 'success'])
        total_captures = len(results)
        
        logger.info(f"=== STEP 2: CONTENT CAPTURE COMPLETED ===")
        logger.info(f"Successfully captured {successful_captures}/{total_captures} content files")
        
        return results
        
    except Exception as e:
        logger.error(f"Failed to capture lottery content: {str(e)}")
        return []

def run_capture():
    """Run the capture function"""
    try:
        return capture_all_lottery_content()
    except Exception as e:
        logger.error(f"Error running content capture: {str(e)}")
        return []

if __name__ == "__main__":
    # Run content capture when executed directly
    results = run_capture()
    
    # Print results summary
    print("\n=== CONTENT CAPTURE RESULTS ===")
    for result in results:
        status_symbol = "✓" if result['status'] == 'success' else "✗"
        print(f"{status_symbol} {result['lottery_type']}: {result['status']}")
        if result['filepath']:
            print(f"  File: {os.path.basename(result['filepath'])}")
    
    successful = len([r for r in results if r['status'] == 'success'])
    total = len(results)
    print(f"\nTotal: {successful}/{total} content files captured successfully")