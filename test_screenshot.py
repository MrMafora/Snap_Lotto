#!/usr/bin/env python3
"""
Test Screenshot Capture for South African National Lottery
Simple approach using requests and saving HTML for AI processing
"""

import os
import time
import requests
from datetime import datetime
from config import Config

def capture_lottery_html(url, lottery_type):
    """Capture HTML content from lottery URL"""
    try:
        print(f"Capturing {lottery_type} from {url}")
        
        # Create session with realistic headers
        session = requests.Session()
        session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-ZA,en;q=0.9',
            'Accept-Encoding': 'identity',  # Disable compression to avoid issues
            'Connection': 'keep-alive'
        })
        
        # Make request with timeout
        response = session.get(url, timeout=15)
        response.raise_for_status()
        
        # Generate filename
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        safe_type = lottery_type.lower().replace(' ', '_').replace('+', '_plus_')
        filename = f"{timestamp}_{safe_type}.html"
        
        # Save HTML content
        os.makedirs('screenshots', exist_ok=True)
        filepath = os.path.join('screenshots', filename)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(response.text)
        
        file_size = os.path.getsize(filepath)
        print(f"✓ Saved {filename} ({file_size} bytes)")
        
        return True
        
    except Exception as e:
        print(f"✗ Error capturing {lottery_type}: {str(e)}")
        return False

def main():
    """Test capturing all 6 lottery URLs"""
    print("=== TESTING LOTTERY URL CAPTURE ===\n")
    
    results = []
    
    for i, config in enumerate(Config.RESULTS_URLS):
        url = config['url']
        lottery_type = config['lottery_type']
        
        # Human-like delay between requests
        if i > 0:
            delay = 2 + i
            print(f"Waiting {delay} seconds...")
            time.sleep(delay)
        
        success = capture_lottery_html(url, lottery_type)
        results.append(success)
        print()
    
    # Summary
    successful = sum(results)
    total = len(results)
    print(f"=== RESULTS: {successful}/{total} URLs captured successfully ===")
    
    return successful == total

if __name__ == "__main__":
    main()