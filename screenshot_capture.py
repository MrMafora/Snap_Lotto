"""
Screenshot capture functionality for South African lottery websites
"""

import os
import time
import random
import logging
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.keys import Keys
from models import Screenshot, db
from flask_login import current_user

# Configure logging
logger = logging.getLogger(__name__)

# Human-like user agents for rotation
USER_AGENTS = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
    'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:121.0) Gecko/20100101 Firefox/121.0',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Edge/120.0.0.0',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Safari/605.1.15'
]

# Realistic screen resolutions
SCREEN_SIZES = [
    (1920, 1080), (1366, 768), (1536, 864), (1440, 900),
    (1280, 720), (1600, 900), (2560, 1440), (1920, 1200)
]

# EXACT URLs from database - these are the specific result pages we need
LOTTERY_URLS = {
    'LOTTO': 'https://www.nationallottery.co.za/results/lotto',
    'LOTTO PLUS 1': 'https://www.nationallottery.co.za/results/lotto-plus-1-results',
    'LOTTO PLUS 2': 'https://www.nationallottery.co.za/results/lotto-plus-2-results',
    'POWERBALL': 'https://www.nationallottery.co.za/results/powerball',
    'POWERBALL PLUS': 'https://www.nationallottery.co.za/results/powerball-plus',
    'DAILY LOTTO': 'https://www.nationallottery.co.za/results/daily-lotto'
}

# Alternative URL patterns to try if main page fails
FALLBACK_URLS = {
    'LOTTO': ['https://www.nationallottery.co.za/lotto', 'https://www.nationallottery.co.za/games/lotto'],
    'LOTTO PLUS 1': ['https://www.nationallottery.co.za/lotto-plus', 'https://www.nationallottery.co.za/games/lotto-plus'], 
    'LOTTO PLUS 2': ['https://www.nationallottery.co.za/lotto-plus-2', 'https://www.nationallottery.co.za/games/lotto-plus-2'],
    'POWERBALL': ['https://www.nationallottery.co.za/powerball', 'https://www.nationallottery.co.za/games/powerball'],
    'POWERBALL PLUS': ['https://www.nationallottery.co.za/powerball-plus', 'https://www.nationallottery.co.za/games/powerball-plus'],
    'DAILY LOTTO': ['https://www.nationallottery.co.za/daily-lotto', 'https://www.nationallottery.co.za/games/daily-lotto']
}

def setup_chrome_driver():
    """Setup Chrome driver with human-like anti-detection features"""
    chrome_options = Options()
    
    # Choose random user agent and screen size to appear human
    user_agent = random.choice(USER_AGENTS)
    screen_width, screen_height = random.choice(SCREEN_SIZES)
    
    logger.info(f"Using user agent: {user_agent[:50]}... and screen size: {screen_width}x{screen_height}")
    
    # Essential headless mode for Replit environment
    chrome_options.add_argument('--headless')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('--disable-gpu')
    chrome_options.add_argument('--remote-debugging-port=9222')
    
    # Basic window setup
    chrome_options.add_argument(f'--window-size={screen_width},{screen_height}')
    chrome_options.add_argument(f'--user-agent={user_agent}')
    
    # Performance and stealth settings
    chrome_options.add_argument('--disable-blink-features=AutomationControlled')
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option('useAutomationExtension', False)
    
    # Additional anti-detection measures
    chrome_options.add_argument('--disable-extensions')
    chrome_options.add_argument('--disable-plugins')
    chrome_options.add_argument('--disable-images')  # Faster loading
    chrome_options.add_argument('--disable-javascript')  # Prevent bot detection scripts
    
    try:
        driver = webdriver.Chrome(options=chrome_options)
        
        # Advanced anti-detection JavaScript injections
        driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        driver.execute_script("Object.defineProperty(navigator, 'plugins', {get: () => [1, 2, 3, 4, 5]})")
        driver.execute_script("Object.defineProperty(navigator, 'languages', {get: () => ['en-US', 'en']})")
        driver.execute_script("window.chrome = { runtime: {} }")
        driver.execute_script("Object.defineProperty(navigator, 'permissions', {get: () => ({ query: x => ({ state: 'granted' })})})")
        
        # Set realistic browser properties via CDP
        driver.execute_cdp_cmd('Network.setUserAgentOverride', {
            "userAgent": user_agent,
            "acceptLanguage": "en-US,en;q=0.9",
            "platform": "Win32"
        })
        
        # Set timezone to South Africa (simplified)
        driver.execute_cdp_cmd('Emulation.setTimezoneOverride', {'timezoneId': 'Africa/Johannesburg'})
        
        return driver
    except Exception as e:
        logger.error(f"Failed to setup Chrome driver: {e}")
        return None

def human_like_delay(min_seconds=1, max_seconds=4):
    """Add random human-like delays"""
    delay = random.uniform(min_seconds, max_seconds)
    logger.debug(f"Human-like delay: {delay:.2f} seconds")
    time.sleep(delay)

def simulate_human_browsing(driver):
    """Simulate human-like browsing behavior"""
    try:
        # Random mouse movements
        actions = ActionChains(driver)
        
        # Move mouse to random positions (simulate reading)
        for _ in range(random.randint(2, 5)):
            x = random.randint(100, 800)
            y = random.randint(100, 600)
            actions.move_by_offset(x, y).perform()
            time.sleep(random.uniform(0.5, 1.5))
            actions.reset_actions()
        
        # Simulate scrolling behavior
        scroll_amount = random.randint(200, 800)
        driver.execute_script(f"window.scrollBy(0, {scroll_amount});")
        human_like_delay(1, 2)
        
        # Random back scroll
        if random.choice([True, False]):
            driver.execute_script(f"window.scrollBy(0, -{scroll_amount//2});")
            human_like_delay(0.5, 1)
        
        # Simulate reading time
        human_like_delay(2, 5)
        
    except Exception as e:
        logger.debug(f"Human simulation error (non-critical): {e}")

def capture_lottery_screenshot(lottery_type, url, output_dir='screenshots'):
    """
    Capture screenshot of a specific lottery results page
    
    Args:
        lottery_type (str): Type of lottery (LOTTO, POWERBALL, etc.)
        url (str): URL to capture
        output_dir (str): Directory to save screenshots
        
    Returns:
        dict: Result with success status and details
    """
    
    # Ensure output directory exists
    os.makedirs(output_dir, exist_ok=True)
    
    # Generate filename with timestamp
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = f"{timestamp}_{lottery_type.lower().replace(' ', '_')}.png"
    filepath = os.path.join(output_dir, filename)
    
    driver = setup_chrome_driver()
    if not driver:
        return {
            'success': False,
            'error': 'Failed to setup browser driver',
            'lottery_type': lottery_type
        }
    
    try:
        logger.info(f"Capturing screenshot for {lottery_type} from {url}")
        
        # Random delay before accessing each URL (like a human browsing)
        human_like_delay(2, 8)
        
        # Navigate to the lottery page (start with main page to avoid blocking)
        driver.get(url)
        
        # Wait for page to load with longer timeout for slow networks
        WebDriverWait(driver, 15).until(
            EC.presence_of_element_located((By.TAG_NAME, "body"))
        )
        
        # Check if we're on main page - homepage contains lottery information
        if url == 'https://www.nationallottery.co.za/':
            try:
                # Wait for page content to load completely
                human_like_delay(5, 8)
                
                # Check if homepage contains lottery information (which it does based on testing)
                page_content = driver.page_source.lower()
                if any(keyword in page_content for keyword in ['lotto', 'powerball', 'daily lotto', 'winning numbers']):
                    logger.info(f"Homepage contains lottery information for {lottery_type}")
                else:
                    logger.warning(f"Homepage may not contain lottery data for {lottery_type}")
                    
                # Try to scroll to lottery results section if visible
                try:
                    # Look for lottery game elements and scroll to them
                    lottery_elements = driver.find_elements(By.CSS_SELECTOR, "[class*='lotto'], [class*='powerball'], [class*='lottery']")
                    if lottery_elements:
                        driver.execute_script("arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});", lottery_elements[0])
                        human_like_delay(2, 4)
                except:
                    pass
                
            except Exception as nav_error:
                logger.warning(f"Homepage processing error: {nav_error}")
                # Continue with screenshot of current page
        
        # Simulate human browsing behavior
        simulate_human_browsing(driver)
        
        # Wait for any dynamic content to load
        human_like_delay(3, 6)
        
        # Sometimes refresh like a human would do if page seems slow
        if random.choice([True, False, False]):  # 33% chance
            logger.debug(f"Refreshing page for {lottery_type} (human-like behavior)")
            driver.refresh()
            WebDriverWait(driver, 15).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
            human_like_delay(2, 4)
        
        # Scroll to top first to ensure we capture from the beginning
        driver.execute_script("window.scrollTo(0, 0);")
        human_like_delay(1, 2)
        
        # Get accurate full page dimensions
        total_height = driver.execute_script("""
            return Math.max(
                document.body.scrollHeight,
                document.body.offsetHeight,
                document.documentElement.clientHeight,
                document.documentElement.scrollHeight,
                document.documentElement.offsetHeight
            );
        """)
        
        total_width = driver.execute_script("""
            return Math.max(
                document.body.scrollWidth,
                document.body.offsetWidth,
                document.documentElement.clientWidth,
                document.documentElement.scrollWidth,
                document.documentElement.offsetWidth
            );
        """)
        
        logger.info(f"Detected full page dimensions: {total_width}x{total_height}")
        
        # Ensure minimum dimensions for complete capture
        capture_width = max(total_width, 1400)  # Minimum width to capture full content
        capture_height = max(total_height, 1200)  # Minimum height for complete page
        
        # Set browser window size to capture entire page
        driver.set_window_size(capture_width, capture_height)
        logger.info(f"Set browser window size to: {capture_width}x{capture_height}")
        
        # Wait for page to fully adjust and load at new dimensions
        human_like_delay(3, 5)
        
        # Ensure we're at the top of the page
        driver.execute_script("window.scrollTo(0, 0);")
        human_like_delay(1, 2)
        
        # Take full-page screenshot - this should capture everything
        driver.save_screenshot(filepath)
        
        logger.info(f"FULL-PAGE screenshot captured: {filepath} (window: {capture_width}x{capture_height})")
        
        # Get file size
        file_size = os.path.getsize(filepath) if os.path.exists(filepath) else 0
        
        # Save screenshot info to database
        screenshot = Screenshot(
            lottery_type=lottery_type,
            url=url,
            filename=filename,
            file_path=filepath,
            file_size=file_size,
            capture_method='selenium',
            created_by=current_user.id if hasattr(current_user, 'id') else None
        )
        
        db.session.add(screenshot)
        db.session.commit()
        
        logger.info(f"Successfully captured screenshot for {lottery_type}: {filename}")
        
        return {
            'success': True,
            'lottery_type': lottery_type,
            'filename': filename,
            'filepath': filepath,
            'file_size': file_size,
            'screenshot_id': screenshot.id
        }
        
    except Exception as e:
        logger.error(f"Error capturing screenshot for {lottery_type}: {e}")
        return {
            'success': False,
            'error': str(e),
            'lottery_type': lottery_type
        }
        
    finally:
        if driver:
            driver.quit()

def capture_all_lottery_screenshots():
    """
    Capture screenshots for all South African lottery types with human-like behavior
    
    Returns:
        dict: Summary of capture results
    """
    
    results = {
        'success': [],
        'failed': [],
        'total_processed': 0,
        'total_success': 0,
        'total_failed': 0
    }
    
    logger.info("Starting capture of all lottery screenshots with anti-detection measures")
    
    # Randomize the order to appear more human
    lottery_items = list(LOTTERY_URLS.items())
    random.shuffle(lottery_items)
    logger.info(f"Processing lotteries in randomized order: {[item[0] for item in lottery_items]}")
    
    driver = None
    
    try:
        # Use single driver session to appear more human (like browsing in tabs)
        driver = setup_chrome_driver()
        if not driver:
            logger.error("Failed to setup Chrome driver")
            return {
                'success': [],
                'failed': [{'lottery_type': 'ALL', 'error': 'Failed to setup browser driver'}],
                'total_processed': 0,
                'total_success': 0,
                'total_failed': 1
            }
        
        for i, (lottery_type, url) in enumerate(lottery_items):
            results['total_processed'] += 1
            
            try:
                logger.info(f"Processing {i+1}/{len(lottery_items)}: {lottery_type}")
                
                # Random delay between lottery types (like browsing different pages)
                if i > 0:  # Skip delay for first lottery
                    long_delay = random.uniform(8, 20)  # Longer delays between different lottery pages
                    logger.info(f"Human-like delay between pages: {long_delay:.2f} seconds")
                    time.sleep(long_delay)
                
                result = capture_single_lottery_with_driver(driver, lottery_type, url)
                
                if result['success']:
                    results['success'].append(result)
                    results['total_success'] += 1
                    logger.info(f"✅ {lottery_type}: {result['filename']}")
                else:
                    results['failed'].append(result)
                    results['total_failed'] += 1
                    logger.error(f"❌ {lottery_type}: {result.get('error', 'Unknown error')}")
                    
            except Exception as e:
                results['failed'].append({
                    'lottery_type': lottery_type,
                    'error': str(e),
                    'success': False
                })
                results['total_failed'] += 1
                logger.error(f"❌ {lottery_type}: {e}")
        
    finally:
        if driver:
            # Add human-like delay before closing browser
            human_like_delay(2, 5)
            driver.quit()
    
    logger.info(f"Screenshot capture completed: {results['total_success']}/{results['total_processed']} successful")
    
    return results

def capture_single_lottery_with_driver(driver, lottery_type, url):
    """
    Capture screenshot for a single lottery type using existing driver session with human behavior
    
    Args:
        driver: Existing Chrome driver instance
        lottery_type (str): Type of lottery
        url (str): URL to capture
        
    Returns:
        dict: Result with success status and details
    """
    
    # Generate filename with timestamp
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = f"{timestamp}_{lottery_type.lower().replace(' ', '_')}.png"
    filepath = os.path.join('screenshots', filename)
    
    # Ensure output directory exists
    os.makedirs('screenshots', exist_ok=True)
    
    try:
        logger.info(f"Capturing screenshot for {lottery_type} from {url}")
        
        # Random delay before accessing each URL (like a human browsing)
        human_like_delay(2, 8)
        
        # First visit the main site to establish session (like a real user)
        base_url = "https://www.nationallottery.co.za"
        logger.debug(f"Establishing session by visiting main site: {base_url}")
        driver.get(base_url)
        
        # Wait and simulate looking around the main site
        WebDriverWait(driver, 15).until(
            EC.presence_of_element_located((By.TAG_NAME, "body"))
        )
        human_like_delay(3, 6)
        
        # Now navigate to the specific lottery results page
        logger.debug(f"Now navigating to specific lottery page: {url}")
        driver.get(url)
        
        # Wait for page to load with longer timeout for slow networks
        WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.TAG_NAME, "body"))
        )
        
        # Simulate human browsing behavior
        simulate_human_browsing(driver)
        
        # Wait for any dynamic content to load
        human_like_delay(3, 6)
        
        # Sometimes refresh like a human would do if page seems slow
        if random.choice([True, False, False]):  # 33% chance
            logger.debug(f"Refreshing page for {lottery_type} (human-like behavior)")
            driver.refresh()
            WebDriverWait(driver, 15).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
            human_like_delay(2, 4)
        
        # Take screenshot
        success = driver.save_screenshot(filepath)
        
        if not success:
            return {
                'success': False,
                'error': 'Failed to save screenshot file',
                'lottery_type': lottery_type
            }
        
        # Get file size
        file_size = os.path.getsize(filepath) if os.path.exists(filepath) else 0
        
        # Save screenshot info to database
        try:
            screenshot = Screenshot(
                lottery_type=lottery_type,
                url=url,
                filename=filename,
                file_path=filepath,
                file_size=file_size,
                capture_method='selenium',
                created_by=current_user.id if hasattr(current_user, 'id') else None
            )
            
            db.session.add(screenshot)
            db.session.commit()
            
            logger.info(f"Successfully captured screenshot for {lottery_type}: {filename}")
            
            return {
                'success': True,
                'lottery_type': lottery_type,
                'filename': filename,
                'filepath': filepath,
                'file_size': file_size,
                'screenshot_id': screenshot.id
            }
        
        except Exception as db_error:
            logger.error(f"Database error for {lottery_type}: {db_error}")
            db.session.rollback()
            return {
                'success': False,
                'error': f'Database error: {str(db_error)}',
                'lottery_type': lottery_type
            }
        
    except Exception as e:
        logger.error(f"Error capturing screenshot for {lottery_type}: {e}")
        return {
            'success': False,
            'error': str(e),
            'lottery_type': lottery_type
        }

def cleanup_old_screenshots(days_old=7):
    """
    Clean up old screenshot files and database records
    
    Args:
        days_old (int): Delete screenshots older than this many days
        
    Returns:
        dict: Cleanup results
    """
    
    from datetime import timedelta
    
    cutoff_date = datetime.utcnow() - timedelta(days=days_old)
    
    try:
        # Find old screenshots in database
        old_screenshots = Screenshot.query.filter(Screenshot.timestamp < cutoff_date).all()
        
        deleted_files = 0
        deleted_records = 0
        
        for screenshot in old_screenshots:
            # Delete file if it exists
            if os.path.exists(screenshot.file_path):
                try:
                    os.remove(screenshot.file_path)
                    deleted_files += 1
                    logger.info(f"Deleted old screenshot file: {screenshot.filename}")
                except Exception as e:
                    logger.warning(f"Failed to delete file {screenshot.file_path}: {e}")
            
            # Delete database record
            db.session.delete(screenshot)
            deleted_records += 1
        
        db.session.commit()
        
        logger.info(f"Cleanup completed: {deleted_files} files, {deleted_records} records")
        
        return {
            'success': True,
            'deleted_files': deleted_files,
            'deleted_records': deleted_records,
            'cutoff_date': cutoff_date
        }
        
    except Exception as e:
        logger.error(f"Error during screenshot cleanup: {e}")
        db.session.rollback()
        return {
            'success': False,
            'error': str(e)
        }

def get_latest_screenshots():
    """
    Get the latest screenshots for each lottery type
    
    Returns:
        list: Latest screenshots grouped by lottery type
    """
    
    try:
        # Get latest screenshot for each lottery type
        screenshots = db.session.query(Screenshot)\
            .filter(Screenshot.status == 'active')\
            .order_by(Screenshot.lottery_type, Screenshot.timestamp.desc())\
            .all()
        
        # Group by lottery type and keep only the latest
        latest_screenshots = {}
        for screenshot in screenshots:
            if screenshot.lottery_type not in latest_screenshots:
                latest_screenshots[screenshot.lottery_type] = screenshot
        
        return list(latest_screenshots.values())
        
    except Exception as e:
        logger.error(f"Error retrieving latest screenshots: {e}")
        return []