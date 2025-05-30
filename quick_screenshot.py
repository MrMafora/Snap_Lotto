"""
Quick Screenshot Capture for Lottery Data
Optimized for speed while maintaining stealth
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
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def capture_single_lottery_screenshot(url, lottery_type):
    """Capture a single lottery screenshot with stealth"""
    driver = None
    try:
        # Stealth Chrome options
        chrome_options = Options()
        chrome_options.add_argument('--headless')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--window-size=1366,768')
        chrome_options.add_argument('--disable-blink-features=AutomationControlled')
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        chrome_options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
        
        # Initialize driver
        service = Service()
        driver = webdriver.Chrome(service=service, options=chrome_options)
        
        # Anti-detection
        driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        driver.set_page_load_timeout(20)
        
        logger.info(f"Capturing {lottery_type} from {url}")
        
        # Navigate to page
        driver.get(url)
        
        # Wait for page load
        WebDriverWait(driver, 15).until(EC.presence_of_element_located((By.TAG_NAME, "body")))
        time.sleep(3)
        
        # Take screenshot
        screenshot_dir = os.path.join(os.getcwd(), 'screenshots')
        os.makedirs(screenshot_dir, exist_ok=True)
        
        timestamp = int(datetime.now().timestamp())
        filename = f"current_{lottery_type.lower().replace(' ', '_')}_{timestamp}.png"
        output_path = os.path.join(screenshot_dir, filename)
        
        driver.save_screenshot(output_path)
        
        if os.path.exists(output_path) and os.path.getsize(output_path) > 5000:
            logger.info(f"Screenshot saved: {filename}")
            return True, output_path
        else:
            logger.warning(f"Screenshot too small: {filename}")
            return False, None
            
    except Exception as e:
        logger.error(f"Failed to capture {lottery_type}: {e}")
        return False, None
    finally:
        if driver:
            try:
                driver.quit()
            except:
                pass

def main():
    """Test single screenshot capture"""
    urls = [
        ('https://www.nationallottery.co.za/results/lotto', 'Lotto'),
        ('https://www.nationallottery.co.za/results/powerball', 'Powerball'),
    ]
    
    for url, lottery_type in urls:
        success, path = capture_single_lottery_screenshot(url, lottery_type)
        if success:
            print(f"✓ {lottery_type}: {path}")
        else:
            print(f"✗ {lottery_type}: Failed")
        
        # Delay between captures
        time.sleep(random.uniform(5, 10))

if __name__ == "__main__":
    main()