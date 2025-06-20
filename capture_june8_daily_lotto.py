#!/usr/bin/env python3
"""
Capture June 8th Daily Lotto results from official lottery website
"""
import os
import sys
import logging
import time
from datetime import datetime
from playwright.sync_api import sync_playwright

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def capture_daily_lotto_screenshot():
    """Capture fresh Daily Lotto screenshot from official website using Playwright"""
    
    try:
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(headless=True)
            context = browser.new_context(
                viewport={'width': 1920, 'height': 1080},
                user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            )
            page = context.new_page()
            
            url = 'https://www.nationallottery.co.za/results/daily-lotto'
            logger.info(f"Accessing official Daily Lotto results: {url}")
            
            page.goto(url, wait_until='networkidle')
            page.wait_for_timeout(5000)  # Additional wait for dynamic content
            
            # Create timestamp for filename
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f'{timestamp}_daily_lotto.png'
            
            # Ensure screenshots directory exists
            screenshots_dir = 'screenshots'
            os.makedirs(screenshots_dir, exist_ok=True)
            
            filepath = os.path.join(screenshots_dir, filename)
            
            # Capture screenshot
            page.screenshot(path=filepath, full_page=True)
            logger.info(f"Fresh Daily Lotto screenshot captured: {filepath}")
            
            browser.close()
            return filepath
        
    except Exception as e:
        logger.error(f"Screenshot capture failed: {e}")
        return None

if __name__ == "__main__":
    result = capture_daily_lotto_screenshot()
    if result:
        print(f"SUCCESS: {result}")
    else:
        print("FAILED: Could not capture screenshot")
        sys.exit(1)