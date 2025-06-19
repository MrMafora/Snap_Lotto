#!/usr/bin/env python3
"""
Test single URL full page PNG capture
"""

import os
import time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from datetime import datetime

def test_single_full_page_capture():
    """Test full page PNG capture for a single URL"""
    
    url = "https://www.nationallottery.co.za/results/lotto"
    lottery_type = "Lotto"
    
    # Generate filename
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = f"{timestamp}_{lottery_type.lower().replace(' ', '_')}_full_page.png"
    
    # Create screenshots directory
    screenshot_dir = os.path.join(os.getcwd(), 'screenshots')
    os.makedirs(screenshot_dir, exist_ok=True)
    filepath = os.path.join(screenshot_dir, filename)
    
    print(f"Testing full page capture for: {lottery_type}")
    print(f"URL: {url}")
    print(f"Output file: {filename}")
    
    # Configure Chrome options for full page capture
    chrome_options = Options()
    chrome_options.add_argument('--headless')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('--disable-gpu')
    chrome_options.add_argument('--window-size=1920,1080')
    chrome_options.add_argument('--start-maximized')
    chrome_options.add_argument('--disable-web-security')
    chrome_options.add_argument('--disable-features=VizDisplayCompositor')
    chrome_options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
    
    # Create driver
    driver = webdriver.Chrome(options=chrome_options)
    
    try:
        # Set window size for full page capture
        driver.set_window_size(1920, 1080)
        
        print("Loading page...")
        # Navigate to URL
        driver.get(url)
        
        # Wait for page to load
        WebDriverWait(driver, 15).until(
            EC.presence_of_element_located((By.TAG_NAME, 'body'))
        )
        
        # Additional wait for dynamic content and page rendering
        time.sleep(5)
        
        print("Getting page dimensions...")
        # Get page dimensions for full page screenshot
        total_height = driver.execute_script("return Math.max( document.body.scrollHeight, document.body.offsetHeight, document.documentElement.clientHeight, document.documentElement.scrollHeight, document.documentElement.offsetHeight );")
        
        print(f"Page height: {total_height}px")
        
        # Set window size to capture full page height
        driver.set_window_size(1920, total_height + 100)
        
        # Wait a moment for resize
        time.sleep(2)
        
        print("Taking full page screenshot...")
        # Take full page PNG screenshot
        driver.save_screenshot(filepath)
        
        # Check file size
        if os.path.exists(filepath):
            file_size = os.path.getsize(filepath)
            print(f"✓ SUCCESS: Screenshot saved as {filename}")
            print(f"File size: {file_size} bytes")
            print(f"Full path: {filepath}")
            return True
        else:
            print("✗ FAILED: Screenshot file was not created")
            return False
            
    except Exception as e:
        print(f"✗ ERROR: {str(e)}")
        return False
        
    finally:
        driver.quit()

if __name__ == "__main__":
    test_single_full_page_capture()