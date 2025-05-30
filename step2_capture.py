"""
Step 2: Capture Screenshots
Simple browser automation for lottery websites
"""
import os
import time
import logging
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service

logger = logging.getLogger(__name__)

def capture_lottery_screenshots():
    """Capture screenshots from South African lottery websites"""
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
    
    for url in urls:
        try:
            logger.info(f"Capturing screenshot for: {url}")
            
            # Simple Chrome setup
            options = Options()
            options.add_argument('--headless')
            options.add_argument('--no-sandbox')
            options.add_argument('--disable-dev-shm-usage')
            options.add_argument('--window-size=1920,1080')
            
            service = Service('/nix/store/3qnxr5x6gw3k9a9i7d0akz0m6bksbwff-chromedriver-125.0.6422.141/bin/chromedriver')
            driver = webdriver.Chrome(service=service, options=options)
            
            driver.set_page_load_timeout(20)
            driver.get(url)
            time.sleep(3)
            
            # Generate filename
            lottery_type = url.split('/')[-1].replace('-', '_')
            filename = f"{lottery_type}_{int(time.time())}.png"
            output_path = os.path.join(screenshot_dir, filename)
            
            driver.save_screenshot(output_path)
            driver.quit()
            
            if os.path.exists(output_path) and os.path.getsize(output_path) > 5000:
                logger.info(f"Screenshot saved: {filename}")
                success_count += 1
            else:
                logger.warning(f"Screenshot failed: {filename}")
                
        except Exception as e:
            logger.error(f"Error capturing {url}: {e}")
            try:
                driver.quit()
            except:
                pass
    
    logger.info(f"Screenshot capture completed: {success_count}/{len(urls)} successful")
    return success_count > 0, success_count