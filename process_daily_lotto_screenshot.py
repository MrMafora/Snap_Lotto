#!/usr/bin/env python3
"""
Process the Daily Lotto screenshot to extract correct lottery data
"""

import os
import sys
import json
import base64
from datetime import datetime

# Add the project root to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from automated_data_extractor import LotteryDataExtractor

def main():
    """Process the Daily Lotto screenshot"""
    print("Processing Daily Lotto screenshot...")
    
    # Initialize the extractor
    extractor = LotteryDataExtractor()
    
    # Process the Daily Lotto screenshot
    screenshot_path = "attached_assets/20250530_030546_daily_lotto.png"
    
    if not os.path.exists(screenshot_path):
        print(f"Error: Screenshot not found at {screenshot_path}")
        return False
        
    try:
        print(f"Extracting data from: {screenshot_path}")
        result = extractor.process_single_image_safe(screenshot_path)
        
        if result and result.get('success'):
            print("✓ Successfully extracted Daily Lotto data")
            print(f"Draw Number: {result.get('draw_number')}")
            print(f"Lottery Type: {result.get('lottery_type')}")
            print(f"Numbers: {result.get('numbers')}")
            print(f"Date: {result.get('draw_date')}")
            return True
        else:
            print("✗ Failed to extract Daily Lotto data")
            print(f"Error: {result.get('error', 'Unknown error')}")
            return False
            
    except Exception as e:
        print(f"✗ Error processing screenshot: {str(e)}")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)