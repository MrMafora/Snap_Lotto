#!/usr/bin/env python3
"""
Simple Screenshot Capture Module
Captures content from lottery websites and converts to images
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

def capture_lottery_screenshots():
    """Capture screenshots from all lottery result pages"""
    logger.info("=== STARTING LOTTERY SCREENSHOT CAPTURE ===")
    
    results = {}
    screenshot_dir = os.path.join(os.getcwd(), 'screenshots')
    os.makedirs(screenshot_dir, exist_ok=True)
    
    # Get lottery URLs from config
    lottery_urls = {item['lottery_type']: item['url'] for item in Config.RESULTS_URLS}
    
    for lottery_type, url in lottery_urls.items():
        logger.info(f"Capturing {lottery_type} from {url}")
        
        try:
            # Generate filename
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            safe_lottery_type = lottery_type.lower().replace(' ', '_').replace('+', '_plus_')
            filename = f"{timestamp}_{safe_lottery_type}_capture.html"
            filepath = os.path.join(screenshot_dir, filename)
            
            # Create session with headers that handle compression properly
            session = requests.Session()
            session.headers.update({
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                'Accept-Language': 'en-ZA,en;q=0.9,en-US;q=0.8',
                'Accept-Encoding': 'gzip, deflate, br',
                'Connection': 'keep-alive',
                'Cache-Control': 'no-cache',
                'DNT': '1',
                'Upgrade-Insecure-Requests': '1'
            })
            
            # Make request
            response = session.get(url, timeout=30)
            response.raise_for_status()
            
            # Save HTML content
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(response.text)
            
            # Verify file was created
            if os.path.exists(filepath) and os.path.getsize(filepath) > 1000:
                logger.info(f"✓ Successfully captured {lottery_type}: {filename}")
                results[lottery_type] = {
                    'success': True,
                    'filepath': filepath,
                    'url': url,
                    'filename': filename
                }
            else:
                logger.error(f"✗ Failed to capture {lottery_type}")
                results[lottery_type] = {
                    'success': False,
                    'filepath': None,
                    'url': url,
                    'filename': None
                }
            
            # Respectful delay between captures
            if len(results) < len(lottery_urls):
                time.sleep(3)
                
        except Exception as e:
            logger.error(f"Error capturing {lottery_type}: {str(e)}")
            results[lottery_type] = {
                'success': False,
                'filepath': None,
                'url': url,
                'filename': None,
                'error': str(e)
            }
    
    success_count = sum(1 for r in results.values() if r['success'])
    total_count = len(results)
    
    logger.info(f"=== SCREENSHOT CAPTURE COMPLETED ===")
    logger.info(f"Successfully captured: {success_count}/{total_count} lottery pages")
    
    return results

def run_simple_capture():
    """Run the simple screenshot capture process"""
    results = capture_lottery_screenshots()
    success_count = sum(1 for r in results.values() if r['success'])
    total_count = len(results)
    
    return success_count == total_count

if __name__ == "__main__":
    success = run_simple_capture()
    exit(0 if success else 1)