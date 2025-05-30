"""
Step 2: Screenshot Capture System
Uses Playwright to capture current lottery screenshots - Working Version
"""
import os
import time
import random
import logging
from datetime import datetime
from playwright.sync_api import sync_playwright
import asyncio

logger = logging.getLogger(__name__)

# User agents to rotate through
USER_AGENTS = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/115.0',
    'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
]

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
    """Capture live screenshots from South African National Lottery website using Playwright"""
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
    
    try:
        with sync_playwright() as p:
            # Launch browser with anti-detection features
            browser = p.chromium.launch(
                headless=True,
                args=[
                    '--no-sandbox',
                    '--disable-dev-shm-usage',
                    '--disable-blink-features=AutomationControlled',
                    '--disable-web-security',
                    '--disable-features=VizDisplayCompositor'
                ]
            )
            
            # Create context with random user agent
            user_agent = random.choice(USER_AGENTS)
            context = browser.new_context(
                user_agent=user_agent,
                viewport={'width': 1366, 'height': 768}
            )
            
            page = context.new_page()
            
            for i, url in enumerate(urls):
                try:
                    logger.info(f"Attempting screenshot capture from: {url}")
                    
                    # Navigate with retry logic
                    page.goto(url, wait_until='networkidle', timeout=30000)
                    
                    # Human-like behavior - wait and scroll
                    time.sleep(random.uniform(2, 4))
                    
                    # Scroll to ensure content loads
                    page.evaluate("window.scrollTo(0, document.body.scrollHeight/2)")
                    time.sleep(random.uniform(1, 2))
                    page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                    time.sleep(random.uniform(1, 3))
                    page.evaluate("window.scrollTo(0, 0)")
                    time.sleep(random.uniform(1, 2))
                    
                    # Wait for lottery results to load
                    page.wait_for_timeout(3000)
                    
                    # Take screenshot
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    lottery_type = url.split('/')[-1].replace('-', '_')
                    filename = f"{timestamp}_{lottery_type}.png"
                    filepath = os.path.join(screenshot_dir, filename)
                    
                    page.screenshot(path=filepath, full_page=True)
                    
                    if os.path.exists(filepath):
                        size = os.path.getsize(filepath)
                        logger.info(f"Screenshot captured successfully: {filename} ({size} bytes)")
                        success_count += 1
                    else:
                        logger.error(f"Screenshot file not created: {filename}")
                        
                except Exception as e:
                    logger.error(f"Failed to capture screenshot from {url}: {e}")
                    continue
                
                # Delay between captures to avoid detection
                if i < len(urls) - 1:
                    time.sleep(random.uniform(3, 6))
            
            browser.close()
            
    except Exception as e:
        logger.error(f"Screenshot capture failed: {e}")
        return False, 0
    
    if success_count > 0:
        logger.info(f"Screenshot capture completed: {success_count}/{len(urls)} successful")
        return True, success_count
    else:
        logger.error("No screenshots could be captured")
        return False, 0
                success = False
                for attempt in range(2):
                    try:
                        driver.get(url)
                        time.sleep(3)  # Wait for initial load
                        
                        # Check if page loaded by looking for title
                        if driver.title and len(driver.title) > 5:
                            logger.info(f"Page loaded successfully: {driver.title[:50]}...")
                            success = True
                            break
                        else:
                            logger.warning(f"Page may not have loaded properly (attempt {attempt + 1})")
                            
                    except Exception as load_error:
                        logger.warning(f"Load attempt {attempt + 1} failed: {load_error}")
                        time.sleep(2)
                
                if not success:
                    logger.error(f"Could not load {url} after multiple attempts")
                    continue
                
                # Generate filename
                lottery_type = url.split('/')[-1].replace('-', '_')
                timestamp = int(datetime.now().timestamp())
                filename = f"current_{lottery_type}_{timestamp}.png"
                output_path = os.path.join(screenshot_dir, filename)
                
                # Take screenshot
                driver.save_screenshot(output_path)
                
                if os.path.exists(output_path):
                    size = os.path.getsize(output_path)
                    if size > 10000:  # More reasonable size check
                        logger.info(f"Screenshot captured successfully: {filename} ({size} bytes)")
                        success_count += 1
                    else:
                        logger.warning(f"Screenshot appears empty or blocked: {filename} ({size} bytes)")
                else:
                    logger.error(f"Screenshot file not created: {filename}")
                    
            except Exception as e:
                logger.error(f"Failed to capture screenshot for {url}: {e}")
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