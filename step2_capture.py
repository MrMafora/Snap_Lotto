"""
Step 2: Screenshot Capture System
Uses Selenium WebDriver to capture current lottery screenshots
"""
import os
import time
import random
import logging
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

logger = logging.getLogger(__name__)

# Kill any existing chrome processes to prevent conflicts
def kill_chrome_processes():
    """Kill any running Chrome processes that might interfere"""
    try:
        import subprocess
        subprocess.run(['pkill', '-f', 'chrome'], stderr=subprocess.DEVNULL)
        subprocess.run(['pkill', '-f', 'chromedriver'], stderr=subprocess.DEVNULL)
        time.sleep(2)
    except:
        pass

def capture_lottery_screenshots():
    """Capture live screenshots from South African National Lottery website"""
    # Try automated capture first, fall back to manual upload if blocked
    try:
        result = capture_lottery_screenshots_automated()
        if result[0]:  # If automated capture succeeded
            return result
        else:
            logger.info("Automated capture failed, trying fallback system...")
            from step2_fallback import capture_lottery_screenshots_fallback
            return capture_lottery_screenshots_fallback()
    except Exception as e:
        logger.error(f"Both automated and fallback capture failed: {e}")
        return False, 0

def capture_lottery_screenshots_automated():
    """Automated capture method (may be blocked by website security)"""
    urls = [
        'https://www.nationallottery.co.za/results/lotto',
        'https://www.nationallottery.co.za/results/lotto-plus-1-results', 
        'https://www.nationallottery.co.za/results/lotto-plus-2-results',
        'https://www.nationallottery.co.za/results/powerball',
        'https://www.nationallottery.co.za/results/powerball-plus',
        'https://www.nationallottery.co.za/results/daily-lotto'
    ]
    
    screenshot_dir = os.path.join(os.getcwd(), 'screenshots')
    os.makedirs(screenshot_dir, exist_ok=True)
    
    success_count = 0
    driver = None
    
    try:
        # Kill any conflicting Chrome processes first
        kill_chrome_processes()
        
        # Simplified Chrome options that work
        chrome_options = Options()
        chrome_options.add_argument('--headless')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--window-size=1366,768')
        chrome_options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
        
        # Initialize Chrome driver with basic setup
        service = Service()
        driver = webdriver.Chrome(service=service, options=chrome_options)
        driver.set_page_load_timeout(15)
        
        for i, url in enumerate(urls):
            try:
                logger.info(f"Capturing screenshot from: {url}")
                
                # Simple delay between requests
                if i > 0:
                    time.sleep(3)
                
                # Navigate directly to the page
                logger.info(f"Loading: {url}")
                driver.get(url)
                
                # Wait for page to load
                try:
                    WebDriverWait(driver, 10).until(
                        EC.presence_of_element_located((By.TAG_NAME, "body"))
                    )
                except:
                    logger.warning(f"Page load timeout for {url}")
                
                # Short wait for content
                time.sleep(2)
                
                # Generate filename
                lottery_type = url.split('/')[-1].replace('-', '_')
                timestamp = int(datetime.now().timestamp())
                filename = f"current_{lottery_type}_{timestamp}.png"
                output_path = os.path.join(screenshot_dir, filename)
                
                # Take screenshot
                driver.save_screenshot(output_path)
                
                if os.path.exists(output_path) and os.path.getsize(output_path) > 3000:
                    logger.info(f"Screenshot captured: {filename}")
                    success_count += 1
                else:
                    logger.warning(f"Screenshot file too small: {filename}")
                    
            except Exception as e:
                logger.error(f"Failed to capture screenshot for {url}: {e}")
                # Continue with next URL even if one fails
                continue
                
        if success_count > 0:
            logger.info(f"Screenshot capture completed: {success_count}/{len(urls)} successful")
            return True, success_count
        else:
            logger.error("No screenshots could be captured")
            return False, 0
            
    except Exception as e:
        logger.error(f"Screenshot system failed: {e}")
        return False, 0
        
    finally:
        if driver:
            try:
                driver.quit()
            except:
                pass