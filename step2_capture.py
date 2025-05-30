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
    # Website blocking detected - use manual upload system only
    logger.info("National Lottery website has security measures blocking automated access")
    logger.info("Using manual upload system for lottery screenshots...")
    
    try:
        from step2_fallback import capture_lottery_screenshots_fallback
        return capture_lottery_screenshots_fallback()
    except Exception as e:
        logger.error(f"Manual upload system failed: {e}")
        return False, 0

def capture_lottery_screenshots_automated():
    """Automated capture method with quick timeout to prevent hanging"""
    logger.info("Attempting automated screenshot capture...")
    
    # Quick test with very short timeout
    try:
        import signal
        
        def timeout_handler(signum, frame):
            raise TimeoutError("Automated capture timed out")
        
        # Set 15-second timeout for entire automated capture attempt
        signal.signal(signal.SIGALRM, timeout_handler)
        signal.alarm(15)
        
        try:
            kill_chrome_processes()
            
            chrome_options = Options()
            chrome_options.add_argument('--headless')
            chrome_options.add_argument('--no-sandbox')
            chrome_options.add_argument('--disable-dev-shm-usage')
            chrome_options.add_argument('--disable-gpu')
            chrome_options.add_argument('--window-size=1366,768')
            
            service = Service()
            driver = webdriver.Chrome(service=service, options=chrome_options)
            driver.set_page_load_timeout(5)
            
            # Quick test with one URL
            test_url = 'https://www.nationallottery.co.za/results/lotto'
            logger.info(f"Testing connection to: {test_url}")
            driver.get(test_url)
            
            # If we get here without timeout, the site is accessible
            driver.quit()
            signal.alarm(0)  # Cancel timeout
            logger.info("Automated capture appears blocked - using fallback")
            return False, 0
            
        except Exception as e:
            logger.warning(f"Automated capture failed quickly: {e}")
            return False, 0
        finally:
            signal.alarm(0)  # Always cancel timeout
            
    except TimeoutError:
        logger.warning("Automated capture timed out - website blocking detected")
        return False, 0
    except Exception as e:
        logger.warning(f"Automated capture system unavailable: {e}")
        return False, 0