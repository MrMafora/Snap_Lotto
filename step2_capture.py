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
        # Setup Chrome options for human-like behavior
        chrome_options = Options()
        chrome_options.add_argument('--headless')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--window-size=1366,768')  # Common screen size
        chrome_options.add_argument('--disable-blink-features=AutomationControlled')
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        
        # Rotate user agents like a real user
        user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        ]
        chrome_options.add_argument(f'--user-agent={random.choice(user_agents)}')
        
        # Initialize Chrome driver
        service = Service()
        driver = webdriver.Chrome(service=service, options=chrome_options)
        
        # Remove automation indicators
        driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        driver.execute_script("Object.defineProperty(navigator, 'plugins', {get: () => [1, 2, 3, 4, 5]})")
        driver.execute_script("Object.defineProperty(navigator, 'languages', {get: () => ['en-US', 'en']})")
        
        for i, url in enumerate(urls):
            try:
                logger.info(f"Capturing screenshot from: {url}")
                
                # Human-like delay between requests
                if i > 0:
                    delay = random.uniform(3, 8)
                    logger.info(f"Human-like delay: {delay:.1f}s")
                    time.sleep(delay)
                
                # Set page load timeout
                driver.set_page_load_timeout(25)
                
                # Navigate to the page
                driver.get(url)
                
                # Wait for page to load
                try:
                    WebDriverWait(driver, 12).until(
                        EC.presence_of_element_located((By.TAG_NAME, "body"))
                    )
                except:
                    logger.warning(f"Page load timeout for {url}, taking screenshot anyway")
                
                # Human-like behavior: scroll a bit
                try:
                    actions = ActionChains(driver)
                    # Random small scroll to mimic human behavior
                    scroll_amount = random.randint(100, 300)
                    driver.execute_script(f"window.scrollTo(0, {scroll_amount});")
                    time.sleep(random.uniform(1, 2))
                    
                    # Move mouse to random position
                    actions.move_by_offset(random.randint(50, 200), random.randint(50, 200))
                    actions.perform()
                except:
                    pass
                
                # Wait for content to load
                time.sleep(random.uniform(2, 4))
                
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