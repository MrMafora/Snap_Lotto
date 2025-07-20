#!/usr/bin/env python3
"""
Targeted Screenshot Capture using exact URLs from database
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
from webdriver_manager.chrome import ChromeDriverManager
import time
import random

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def get_target_urls_from_database():
    """Get the exact 6 lottery URLs from the database"""
    
    connection_string = os.environ.get('DATABASE_URL')
    if not connection_string:
        logger.error("DATABASE_URL not found")
        return {}
    
    target_urls = {}
    
    try:
        with psycopg2.connect(connection_string) as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT DISTINCT lottery_type, source_url 
                    FROM lottery_result 
                    WHERE source_url IS NOT NULL AND source_url != '' 
                    ORDER BY lottery_type
                """)
                
                for row in cur.fetchall():
                    lottery_type = row[0]
                    source_url = row[1]
                    target_urls[lottery_type] = source_url
                    logger.info(f"Found target URL: {lottery_type} -> {source_url}")
        
        logger.info(f"Retrieved {len(target_urls)} target URLs from database")
        return target_urls
        
    except Exception as e:
        logger.error(f"Failed to get target URLs from database: {e}")
        return {}

def capture_targeted_screenshots():
    """Capture screenshots from the exact URLs stored in database"""
    
    # Get target URLs from database
    target_urls = get_target_urls_from_database()
    
    if not target_urls:
        logger.error("No target URLs found in database")
        return False
    
    # Set up Chrome options for headless operation
    chrome_options = Options()
    chrome_options.add_argument('--headless=new')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('--disable-gpu')
    chrome_options.add_argument('--disable-web-security')
    chrome_options.add_argument('--disable-features=VizDisplayCompositor')
    chrome_options.add_argument('--window-size=1920,1080')
    chrome_options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
    
    service = Service(ChromeDriverManager().install())
    driver = None
    
    try:
        driver = webdriver.Chrome(service=service, options=chrome_options)
        driver.implicitly_wait(10)
        
        screenshots_dir = "screenshots"
        os.makedirs(screenshots_dir, exist_ok=True)
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        successful_captures = 0
        
        logger.info(f"Starting targeted screenshot capture for {len(target_urls)} lottery types")
        
        for i, (lottery_type, url) in enumerate(target_urls.items(), 1):
            try:
                logger.info(f"Capturing {i}/{len(target_urls)}: {lottery_type}")
                logger.info(f"URL: {url}")
                
                # Navigate to the specific URL
                driver.get(url)
                
                # Wait for page to load
                time.sleep(random.uniform(3, 6))
                
                # Wait for results to be visible
                try:
                    WebDriverWait(driver, 15).until(
                        lambda d: any([
                            "results" in d.page_source.lower(),
                            "winning" in d.page_source.lower(),
                            "numbers" in d.page_source.lower(),
                            "draw" in d.page_source.lower()
                        ])
                    )
                except Exception as e:
                    logger.warning(f"Page load timeout for {lottery_type}, proceeding anyway: {e}")
                
                # Generate filename
                lottery_slug = lottery_type.lower().replace(' ', '_').replace('+', '_plus')
                filename = f"{timestamp}_{lottery_slug}_targeted.png"
                filepath = os.path.join(screenshots_dir, filename)
                
                # Take screenshot
                driver.save_screenshot(filepath)
                
                # Verify screenshot was created
                if os.path.exists(filepath) and os.path.getsize(filepath) > 1000:
                    logger.info(f"✅ {lottery_type}: {filename} ({os.path.getsize(filepath):,} bytes)")
                    successful_captures += 1
                else:
                    logger.error(f"❌ {lottery_type}: Screenshot failed or too small")
                
                # Human-like delay between captures
                if i < len(target_urls):
                    delay = random.uniform(2, 5)
                    logger.info(f"Delay before next capture: {delay:.2f} seconds")
                    time.sleep(delay)
                    
            except Exception as e:
                logger.error(f"Failed to capture {lottery_type}: {e}")
                continue
        
        logger.info(f"Targeted screenshot capture complete: {successful_captures}/{len(target_urls)} successful")
        return successful_captures > 0
        
    except Exception as e:
        logger.error(f"Screenshot capture failed: {e}")
        return False
    
    finally:
        if driver:
            driver.quit()

if __name__ == "__main__":
    success = capture_targeted_screenshots()
    if success:
        print("🎯 Targeted screenshot capture completed successfully!")
        print("Screenshots taken from exact database URLs:")
        
        target_urls = get_target_urls_from_database()
        for lottery_type, url in target_urls.items():
            print(f"  {lottery_type}: {url}")
    else:
        print("❌ Targeted screenshot capture failed")