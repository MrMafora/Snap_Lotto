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

def capture_lottery_screenshots():
    """Capture live screenshots from South African National Lottery website"""
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
        # Advanced stealth Chrome options
        chrome_options = Options()
        chrome_options.add_argument('--headless')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--window-size=1920,1080')
        chrome_options.add_argument('--disable-blink-features=AutomationControlled')
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        chrome_options.add_argument('--disable-extensions')
        chrome_options.add_argument('--disable-plugins-discovery')
        chrome_options.add_argument('--disable-web-security')
        chrome_options.add_argument('--ignore-certificate-errors')
        chrome_options.add_argument('--allow-running-insecure-content')
        chrome_options.add_argument('--disable-features=VizDisplayCompositor')
        
        # Real browser user agent
        chrome_options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
        
        # Initialize Chrome driver
        service = Service()
        driver = webdriver.Chrome(service=service, options=chrome_options)
        
        # Advanced anti-detection
        driver.execute_script("""
            Object.defineProperty(navigator, 'webdriver', {get: () => undefined});
            Object.defineProperty(navigator, 'plugins', {get: () => [1, 2, 3, 4, 5]});
            Object.defineProperty(navigator, 'languages', {get: () => ['en-US', 'en']});
            Object.defineProperty(navigator, 'permissions', {get: () => ({query: x => Promise.resolve({state: 'granted'})})});
            window.chrome = {runtime: {}};
            Object.defineProperty(navigator, 'deviceMemory', {get: () => 8});
            Object.defineProperty(navigator, 'hardwareConcurrency', {get: () => 4});
        """)
        
        for i, url in enumerate(urls):
            try:
                logger.info(f"Capturing screenshot from: {url}")
                
                # Longer human-like delay between requests
                if i > 0:
                    delay = random.uniform(8, 15)
                    logger.info(f"Human-like delay: {delay:.1f}s")
                    time.sleep(delay)
                
                # First visit the main lottery homepage to appear more human
                if i == 0:
                    logger.info("Visiting homepage first...")
                    driver.get("https://www.nationallottery.co.za")
                    time.sleep(random.uniform(3, 6))
                    
                    # Human actions on homepage
                    try:
                        actions = ActionChains(driver)
                        actions.move_by_offset(random.randint(100, 300), random.randint(100, 300))
                        actions.perform()
                        time.sleep(random.uniform(1, 3))
                        driver.execute_script(f"window.scrollTo(0, {random.randint(200, 500)});")
                        time.sleep(random.uniform(2, 4))
                    except:
                        pass
                
                # Set page load timeout
                driver.set_page_load_timeout(30)
                
                # Navigate to the results page
                logger.info(f"Navigating to: {url}")
                driver.get(url)
                
                # Wait longer for page to fully load
                try:
                    WebDriverWait(driver, 20).until(
                        EC.presence_of_element_located((By.TAG_NAME, "body"))
                    )
                    time.sleep(random.uniform(2, 4))
                except:
                    logger.warning(f"Page load timeout for {url}, taking screenshot anyway")
                
                # More extensive human-like behavior
                try:
                    actions = ActionChains(driver)
                    
                    # Multiple random mouse movements
                    for _ in range(random.randint(2, 4)):
                        actions.move_by_offset(random.randint(-100, 100), random.randint(-100, 100))
                        actions.perform()
                        time.sleep(random.uniform(0.5, 1.5))
                    
                    # Random scrolling behavior
                    scroll_amount = random.randint(200, 600)
                    driver.execute_script(f"window.scrollTo(0, {scroll_amount});")
                    time.sleep(random.uniform(1, 3))
                    
                    # Scroll back up a bit
                    scroll_back = scroll_amount - random.randint(50, 150)
                    driver.execute_script(f"window.scrollTo(0, {scroll_back});")
                    time.sleep(random.uniform(1, 2))
                    
                except:
                    pass
                
                # Final wait for content to fully load
                time.sleep(random.uniform(3, 6))
                
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