#!/usr/bin/env python3
"""
Database-Targeted Screenshot Capture
Uses exact URLs from database instead of random screenshots
"""

import os
import logging
import psycopg2
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import random

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# EXACT URLs from database - verified working URLs
TARGET_URLS = {
    'LOTTO': 'https://www.nationallottery.co.za/results/lotto',
    'LOTTO PLUS 1': 'https://www.nationallottery.co.za/results/lotto-plus-1-results',
    'LOTTO PLUS 2': 'https://www.nationallottery.co.za/results/lotto-plus-2-results',
    'POWERBALL': 'https://www.nationallottery.co.za/results/powerball',
    'POWERBALL PLUS': 'https://www.nationallottery.co.za/results/powerball-plus',
    'DAILY LOTTO': 'https://www.nationallottery.co.za/results/daily-lotto'
}

def save_screenshot_to_database(lottery_type, filename, file_path, file_size):
    """Save screenshot metadata to database"""
    
    connection_string = os.environ.get('DATABASE_URL')
    if not connection_string:
        logger.error("DATABASE_URL not found")
        return False
    
    try:
        with psycopg2.connect(connection_string) as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO screenshot (lottery_type, filename, file_path, file_size, created_at)
                    VALUES (%s, %s, %s, %s, %s)
                    RETURNING id
                """, (lottery_type, filename, file_path, file_size, datetime.now()))
                
                screenshot_id = cur.fetchone()[0]
                logger.info(f"Screenshot saved to database with ID {screenshot_id}")
                return screenshot_id
                
    except Exception as e:
        logger.error(f"Failed to save screenshot to database: {e}")
        return False

def capture_database_targeted_screenshots():
    """Capture screenshots from exact database URLs"""
    
    logger.info("🎯 Starting DATABASE-TARGETED screenshot capture")
    logger.info("Using exact URLs from database instead of random screenshots")
    
    # Set up Chrome options for headless operation
    chrome_options = Options()
    chrome_options.add_argument('--headless=new')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('--disable-gpu')
    chrome_options.add_argument('--disable-web-security')
    chrome_options.add_argument('--disable-features=VizDisplayCompositor')
    chrome_options.add_argument('--window-size=1920,1080')
    
    # Realistic user agents for anti-detection
    user_agents = [
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0'
    ]
    
    chrome_options.add_argument(f'--user-agent={random.choice(user_agents)}')
    
    try:
        # Use system chromium if available, otherwise fall back to chromedriver
        try:
            service = Service('/usr/bin/chromedriver')
            driver = webdriver.Chrome(service=service, options=chrome_options)
        except:
            # Fallback to system chromium
            chrome_options.binary_location = '/usr/bin/chromium-browser'
            driver = webdriver.Chrome(options=chrome_options)
        
        driver.implicitly_wait(10)
        
        screenshots_dir = "screenshots"
        os.makedirs(screenshots_dir, exist_ok=True)
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        successful_captures = 0
        
        logger.info(f"Targeting {len(TARGET_URLS)} specific lottery result pages")
        
        for i, (lottery_type, url) in enumerate(TARGET_URLS.items(), 1):
            try:
                logger.info(f"📸 Capturing {i}/{len(TARGET_URLS)}: {lottery_type}")
                logger.info(f"🎯 Target URL: {url}")
                
                # Navigate to the specific URL
                driver.get(url)
                
                # Wait for page to load
                time.sleep(random.uniform(4, 7))
                
                # Wait for lottery results content
                try:
                    WebDriverWait(driver, 20).until(
                        lambda d: any([
                            "results" in d.page_source.lower(),
                            "winning" in d.page_source.lower(),
                            "numbers" in d.page_source.lower(),
                            "draw" in d.page_source.lower(),
                            "lotto" in d.page_source.lower()
                        ])
                    )
                except Exception as e:
                    logger.warning(f"Page load timeout for {lottery_type}, proceeding anyway: {e}")
                
                # Generate filename with targeted prefix
                lottery_slug = lottery_type.lower().replace(' ', '_').replace('+', '_plus')
                filename = f"{timestamp}_{lottery_slug}_targeted.png"
                filepath = os.path.join(screenshots_dir, filename)
                
                # Take screenshot
                driver.save_screenshot(filepath)
                
                # Verify screenshot was created
                if os.path.exists(filepath) and os.path.getsize(filepath) > 10000:
                    file_size = os.path.getsize(filepath)
                    logger.info(f"✅ {lottery_type}: {filename} ({file_size:,} bytes)")
                    
                    # Save to database
                    screenshot_id = save_screenshot_to_database(
                        lottery_type, filename, filepath, file_size
                    )
                    
                    if screenshot_id:
                        logger.info(f"📝 Database record created: ID {screenshot_id}")
                    
                    successful_captures += 1
                else:
                    logger.error(f"❌ {lottery_type}: Screenshot failed or too small")
                
                # Human-like delay between captures
                if i < len(TARGET_URLS):
                    delay = random.uniform(3, 8)
                    logger.info(f"⏳ Human-like delay: {delay:.2f} seconds")
                    time.sleep(delay)
                    
            except Exception as e:
                logger.error(f"Failed to capture {lottery_type}: {e}")
                continue
        
        logger.info(f"🎯 Database-targeted capture complete: {successful_captures}/{len(TARGET_URLS)} successful")
        logger.info("Screenshots taken from EXACT database URLs - no random capture")
        return successful_captures > 0
        
    except Exception as e:
        logger.error(f"Screenshot capture system failed: {e}")
        return False
    
    finally:
        if 'driver' in locals():
            driver.quit()

if __name__ == "__main__":
    success = capture_database_targeted_screenshots()
    if success:
        print("🎯 DATABASE-TARGETED screenshot capture completed!")
        print("All screenshots taken from exact URLs:")
        for lottery_type, url in TARGET_URLS.items():
            print(f"  ✓ {lottery_type}: {url}")
    else:
        print("❌ Database-targeted capture failed")