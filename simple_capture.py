#!/usr/bin/env python3
"""
Simple screenshot capture using requests and wkhtmltoimage
"""

import os
import requests
import subprocess
from datetime import datetime
from config import Config

def capture_page_as_image(url, lottery_type):
    """Capture webpage as PNG image using wkhtmltoimage"""
    try:
        print(f"Capturing {lottery_type} from {url}")
        
        # Generate filename
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        safe_lottery_type = lottery_type.lower().replace(' ', '_').replace('+', '_plus_')
        filename = f"{timestamp}_{safe_lottery_type}_screenshot.png"
        
        # Ensure screenshots directory exists
        screenshot_dir = os.path.join(os.getcwd(), 'screenshots')
        os.makedirs(screenshot_dir, exist_ok=True)
        filepath = os.path.join(screenshot_dir, filename)
        
        # Use wkhtmltoimage to capture page
        cmd = [
            'wkhtmltoimage',
            '--width', '1200',
            '--height', '800',
            '--quality', '85',
            '--format', 'png',
            url,
            filepath
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
        
        if result.returncode == 0 and os.path.exists(filepath):
            file_size = os.path.getsize(filepath)
            print(f"✓ Screenshot saved: {filename} ({file_size} bytes)")
            return filepath
        else:
            print(f"✗ Failed to capture {lottery_type}: {result.stderr}")
            return None
            
    except Exception as e:
        print(f"✗ Error capturing {lottery_type}: {str(e)}")
        return None

def test_single_capture():
    """Test capturing one lottery page"""
    url = "https://www.nationallottery.co.za/results/lotto"
    lottery_type = "Lotto"
    
    result = capture_page_as_image(url, lottery_type)
    
    if result:
        print(f"\n✓ Success: {os.path.basename(result)}")
        # Check if it's a valid PNG
        with open(result, 'rb') as f:
            header = f.read(8)
            if header.startswith(b'\x89PNG'):
                print("✓ Valid PNG format confirmed")
            else:
                print("✗ Invalid PNG format")
    else:
        print("\n✗ Failed to capture screenshot")

if __name__ == "__main__":
    test_single_capture()