#!/usr/bin/env python3
"""
Test script to capture a single screenshot and verify PNG output
"""

import os
import time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from datetime import datetime

def test_single_screenshot():
    """Test capturing a single screenshot"""
    driver = None
    try:
        print("Setting up Chrome driver...")
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--window-size=1200,800")
        
        driver = webdriver.Chrome(options=chrome_options)
        
        # Test URL
        url = "https://www.nationallottery.co.za/results/lotto"
        print(f"Navigating to: {url}")
        
        driver.get(url)
        time.sleep(5)
        
        # Generate filename
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"test_{timestamp}_lotto_screenshot.png"
        filepath = os.path.join("screenshots", filename)
        
        # Ensure directory exists
        os.makedirs("screenshots", exist_ok=True)
        
        # Take screenshot
        print(f"Taking screenshot: {filename}")
        driver.save_screenshot(filepath)
        
        # Check if file was created and get size
        if os.path.exists(filepath):
            file_size = os.path.getsize(filepath)
            print(f"✓ Screenshot saved successfully: {filename}")
            print(f"✓ File size: {file_size} bytes")
            return filepath
        else:
            print("✗ Screenshot file was not created")
            return None
            
    except Exception as e:
        print(f"✗ Error: {str(e)}")
        return None
    finally:
        if driver:
            driver.quit()

if __name__ == "__main__":
    result = test_single_screenshot()
    if result:
        print(f"\nSuccess! Screenshot saved to: {result}")
    else:
        print("\nFailed to capture screenshot")