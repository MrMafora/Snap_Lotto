#!/usr/bin/env python3
"""
Quick test to verify screenshot capture is working
"""
import os
import sys
from screenshot_manager import capture_screenshot_from_url

def test_screenshot():
    print("Testing screenshot capture...")
    
    # Create screenshots directory if it doesn't exist
    os.makedirs('screenshots', exist_ok=True)
    
    # Test URL - use a simple website first
    test_url = "https://www.nationallottery.co.za/lotto-history"
    output_path = os.path.join('screenshots', 'test_capture.png')
    
    print(f"Attempting to capture: {test_url}")
    print(f"Output path: {output_path}")
    
    try:
        success = capture_screenshot_from_url(test_url, output_path)
        
        if success and os.path.exists(output_path):
            size = os.path.getsize(output_path)
            print(f"✓ Screenshot captured successfully!")
            print(f"  File size: {size} bytes")
            print(f"  Location: {output_path}")
            return True
        else:
            print("✗ Screenshot capture failed - no file created")
            return False
            
    except Exception as e:
        print(f"✗ Screenshot capture failed with error: {e}")
        return False

if __name__ == "__main__":
    test_screenshot()