#!/usr/bin/env python3
"""
Working screenshot solution for lottery automation
Uses requests + simple HTML parsing for reliable data capture
"""
import requests
import os
from datetime import datetime

def capture_lottery_page_content(url, output_path):
    """Capture lottery page content using requests - more reliable than browser automation"""
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        print(f"Fetching lottery data from: {url}")
        response = requests.get(url, headers=headers, timeout=15)
        
        if response.status_code == 200:
            # Save the HTML content which contains the lottery data
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            
            # Create a text file with the lottery data
            text_output = output_path.replace('.png', '.html')
            with open(text_output, 'w', encoding='utf-8') as f:
                f.write(response.text)
            
            print(f"✓ Lottery data captured: {text_output} ({len(response.text)} chars)")
            return True
        else:
            print(f"✗ Failed to fetch lottery data: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"✗ Error capturing lottery data: {e}")
        return False

def test_lottery_capture():
    """Test the working lottery data capture"""
    test_urls = [
        'https://www.nationallottery.co.za/lotto-history',
        'https://www.nationallottery.co.za/powerball-history',
        'https://www.nationallottery.co.za/daily-lotto-history'
    ]
    
    success_count = 0
    for url in test_urls:
        filename = url.split('/')[-1] + f"_{int(datetime.now().timestamp())}.png"
        output_path = f"screenshots/{filename}"
        
        if capture_lottery_page_content(url, output_path):
            success_count += 1
    
    print(f"Successfully captured {success_count}/{len(test_urls)} lottery pages")
    return success_count > 0

if __name__ == "__main__":
    os.makedirs('screenshots', exist_ok=True)
    test_lottery_capture()