#!/usr/bin/env python3
"""
Simple screenshot fix to get automation working immediately
"""
import os
import time
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options

def create_working_screenshot_function():
    """Create a simple screenshot function that actually works"""
    
    def capture_screenshot_simple(url, output_path):
        """Simple screenshot capture that works"""
        print(f"Capturing screenshot: {url}")
        
        # Ensure directory exists
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        options = Options()
        options.add_argument('--headless')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--window-size=1920,1080')
        
        driver = None
        try:
            service = Service('/nix/store/3qnxr5x6gw3k9a9i7d0akz0m6bksbwff-chromedriver-125.0.6422.141/bin/chromedriver')
            driver = webdriver.Chrome(service=service, options=options)
            driver.set_page_load_timeout(15)
            
            driver.get(url)
            time.sleep(3)  # Let page load
            
            # Take screenshot
            success = driver.save_screenshot(output_path)
            
            if success and os.path.exists(output_path):
                print(f"✓ Screenshot saved: {output_path}")
                return True
            else:
                print(f"✗ Failed to save screenshot")
                return False
                
        except Exception as e:
            print(f"✗ Screenshot error: {e}")
            return False
        finally:
            if driver:
                driver.quit()
    
    return capture_screenshot_simple

def test_working_capture():
    """Test the working screenshot function"""
    capture_func = create_working_screenshot_function()
    
    test_url = "https://www.nationallottery.co.za/lotto-history"
    output_path = "screenshots/test_working.png"
    
    print("Testing working screenshot capture...")
    success = capture_func(test_url, output_path)
    
    if success:
        print("✓ Screenshot capture is working!")
        print(f"File size: {os.path.getsize(output_path)} bytes")
    else:
        print("✗ Screenshot capture still failing")

if __name__ == "__main__":
    test_working_capture()