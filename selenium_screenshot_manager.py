"""
Selenium Screenshot Manager

A pure Python solution for capturing screenshots using Selenium, which is more
reliable in the Replit environment without requiring separate browser installations.
"""
import os
import logging
import time
import traceback
import threading
import random
import queue
from datetime import datetime
import urllib.request
from models import db, Screenshot, ScheduleConfig
from logger import setup_logger
import screenshot_diagnostics as diag

# Set up module-specific logger
logger = setup_logger(__name__, level=logging.DEBUG)  # Increase to DEBUG for more details

# Create directory for screenshots if it doesn't exist
SCREENSHOT_DIR = os.path.join(os.getcwd(), 'screenshots')
os.makedirs(SCREENSHOT_DIR, exist_ok=True)

# Thread semaphore to limit concurrent screenshots
# This prevents "can't start new thread" errors by limiting resource usage
# Increased from 2 to 6 to handle all 12 lottery types (6 history, 6 results pages)
MAX_CONCURRENT_THREADS = 6
screenshot_semaphore = threading.Semaphore(MAX_CONCURRENT_THREADS)

# Queue system for processing screenshots
# This ensures all screenshots get processed even if we hit thread limits
screenshot_queue = queue.Queue()

# Screenshot capture settings
MAX_RETRIES = 3  # Number of retry attempts for failed screenshots
NAVIGATION_TIMEOUT = 60  # 60 seconds timeout for page navigation

@diag.track_sync
def capture_screenshot(url, retry_count=0, lottery_type=None):
    """
    Enhanced function to capture a screenshot using urllib with detailed diagnostics.
    This is a fallback approach that doesn't provide full-page screenshots
    but is more reliable when Playwright is not available.
    
    Args:
        url (str): The URL to capture
        retry_count (int): Current retry attempt
        lottery_type (str): Type of lottery for diagnostic logging
        
    Returns:
        tuple: (filepath, screenshot_data, None) or (None, None, None) if failed
    """
    # Get lottery type from database if not provided
    if not lottery_type and url:
        try:
            screenshot = Screenshot.query.filter_by(url=url).first()
            if screenshot:
                lottery_type = screenshot.lottery_type
        except Exception:
            pass  # Continue even if we can't get the lottery type
    
    lottery_name = lottery_type or "Unknown"
    
    # If we've exceeded max retries, give up
    if retry_count >= MAX_RETRIES:
        error_msg = f"Maximum retry attempts ({MAX_RETRIES}) exceeded"
        logger.error(f"{error_msg} for {lottery_name}: {url}")
        diag.log_sync_attempt(lottery_name, url, False, error_msg)
        return None, None, None
        
    # Prepare the file path for the screenshot
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    url_filename = url.split('/')[-1] or 'index'
    filename = f"{timestamp}_{url_filename}.png"  # Changed to .png for image files
    filepath = os.path.join(SCREENSHOT_DIR, filename)
    
    logger.debug(f"[{lottery_name}] Capturing screenshot from {url} - Attempt {retry_count + 1}/{MAX_RETRIES}")
    
    # Add jitter to avoid synchronized anti-bot detection
    jitter_delay = random.uniform(0.5, 2.0)
    if retry_count > 0:
        logger.debug(f"[{lottery_name}] Adding jitter delay of {jitter_delay:.2f}s")
        time.sleep(jitter_delay)
    
    # Main try block for capturing the screenshot
    try:
        # First attempt to use playwright for proper screenshots
        try:
            # Try to import playwright here
            from playwright.sync_api import sync_playwright
            
            # Use a custom User-Agent to avoid being blocked
            # Rotate between different user agents for variety
            user_agents = [
                'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.0 Safari/605.1.15',
                'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/119.0'
            ]
            user_agent = random.choice(user_agents)
            
            logger.debug(f"[{lottery_name}] Launching playwright with User-Agent: {user_agent}")
            
            # Try to find chromium in common locations
            chromium_paths = [
                "/nix/store/zi4f80l169xlmivz8vja8wlphq74qqk0-chromium-125.0.6422.141/bin/chromium",
                "/usr/bin/chromium-browser",
                "/usr/bin/chromium",
                "/nix/store/chromium/bin/chromium"
            ]
            
            chromium_path = None
            for path in chromium_paths:
                if os.path.exists(path):
                    logger.debug(f"Using Chromium from: {path}")
                    chromium_path = path
                    break
            
            # Use sync playwright to capture screenshot
            with sync_playwright() as p:
                browser_type = p.chromium
                browser = browser_type.launch(
                    headless=True,
                    executable_path=chromium_path if chromium_path else None
                )
                
                # Create browser context with custom viewport and user agent
                context = browser.new_context(
                    viewport={'width': 1280, 'height': 1600},
                    user_agent=user_agent
                )
                
                # Create a new page and navigate to the URL
                page = context.new_page()
                page.goto(url, timeout=NAVIGATION_TIMEOUT * 1000)  # Playwright uses ms
                
                # Wait for page content to stabilize
                page.wait_for_load_state('networkidle')
                
                # Take screenshot and save it to file
                screenshot_data = page.screenshot(path=filepath, full_page=True)
                
                # Close resources
                page.close()
                context.close()
                browser.close()
                
                logger.info(f"[{lottery_name}] Screenshot successfully saved to {filepath}")
                
                # Log the successful attempt
                diag.log_sync_attempt(lottery_name, url, True)
                
                # Return the result
                return filepath, screenshot_data, None
                
        except ImportError:
            logger.warning(f"[{lottery_name}] Playwright not available, falling back to HTML capture")
            # Fallback to HTML method below
        
        # Fallback: Use urllib to get the HTML content and generate an image with HTML
        # Choose a user agent for the fallback method
        user_agent = random.choice([
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.0 Safari/605.1.15',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/119.0'
        ])
        
        headers = {
            'User-Agent': user_agent,
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Cache-Control': 'max-age=0'
        }
        
        logger.debug(f"[{lottery_name}] Sending request with headers: {headers['User-Agent']}")
        req = urllib.request.Request(url, headers=headers)
        
        with urllib.request.urlopen(req, timeout=NAVIGATION_TIMEOUT) as response:
            html_content = response.read()
            
            # Try using a different method to generate an image from HTML (Pillow)
            try:
                from PIL import Image, ImageDraw, ImageFont
                import tempfile
                import hashlib
                
                # Create a simplistic "screenshot" image with some basic info
                # This is a fallback method when we can't get a real screenshot
                img_width = 1200
                img_height = 800
                
                # Create a simple image with text info about the lottery
                img = Image.new('RGB', (img_width, img_height), color=(240, 240, 240))
                draw = ImageDraw.Draw(img)
                
                # Use default font
                try:
                    font = ImageFont.truetype("arial.ttf", 16)
                except IOError:
                    font = ImageFont.load_default()
                
                # Draw header
                draw.rectangle(((0, 0), (img_width, 60)), fill=(0, 102, 204))
                draw.text((20, 20), f"Lottery Data: {lottery_name}", 
                          fill=(255, 255, 255), font=font)
                
                # Draw URL and timestamp
                draw.text((20, 80), f"Source URL: {url}", fill=(0, 0, 0), font=font)
                draw.text((20, 110), f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", 
                          fill=(0, 0, 0), font=font)
                
                # Generate a hash of the HTML content
                content_hash = hashlib.md5(html_content).hexdigest()
                draw.text((20, 140), f"Content Hash: {content_hash}", fill=(0, 0, 0), font=font)
                
                # Draw border
                draw.rectangle(((0, 0), (img_width-1, img_height-1)), outline=(200, 200, 200))
                
                # Save image
                img.save(filepath)
                
                with open(filepath, 'rb') as f:
                    screenshot_data = f.read()
                
                logger.info(f"[{lottery_name}] Created synthetic image with lottery data at {filepath}")
                
                # Log the successful attempt but note this is a generated image
                diag.log_sync_attempt(lottery_name, url, True, "Created synthetic image from HTML data")
                
                return filepath, screenshot_data, None
                
            except Exception as e:
                logger.warning(f"[{lottery_name}] Failed to generate image with Pillow: {str(e)}")
            
            # Last resort: Save HTML with .txt extension instead of pretending it's a PNG
            txt_filepath = filepath.replace('.png', '.txt')
            with open(txt_filepath, 'wb') as f:
                f.write(html_content)
            
            logger.warning(f"[{lottery_name}] Saved HTML content to {txt_filepath} with proper .txt extension")
            
            # Log the attempt as successful but note we're using a text file
            diag.log_sync_attempt(lottery_name, url, True, "Saved HTML content as text file")
            
            # Return the txt_filepath as the actual filepath that should be used in the database
            return txt_filepath, html_content, None
            
    except urllib.request.HTTPError as e:
        error_msg = f"HTTP Error {e.code}: {e.reason}"
        logger.error(f"[{lottery_name}] {error_msg} for {url}")
        
        # Retry on certain HTTP errors
        if retry_count < MAX_RETRIES - 1:
            # Wait before retry with exponential backoff
            wait_time = (2 ** retry_count) * 5 + random.uniform(1, 3)  # Exponential backoff with jitter
            logger.info(f"[{lottery_name}] Waiting {wait_time:.2f} seconds before retry...")
            time.sleep(wait_time)
            return capture_screenshot(url, retry_count + 1, lottery_type)
        
        diag.log_sync_attempt(lottery_name, url, False, error_msg)
        return None, None, None
        
    except Exception as e:
        # Handle any URL errors generically
        if hasattr(e, 'reason'):
            error_msg = f"URL Error: {str(e.reason)}"
        else:
            error_msg = f"Error during URL fetch: {str(e)}"
        
        logger.error(f"[{lottery_name}] {error_msg} for {url}")
        
        # Retry on errors
        if retry_count < MAX_RETRIES - 1:
            wait_time = (2 ** retry_count) * 5 + random.uniform(1, 3)
            logger.info(f"[{lottery_name}] Waiting {wait_time:.2f} seconds before retry...")
            time.sleep(wait_time)
            return capture_screenshot(url, retry_count + 1, lottery_type)
        
        diag.log_sync_attempt(lottery_name, url, False, error_msg)
        return None, None, None

def process_screenshot_task(screenshot):
    """
    Process a single screenshot in the queue
    Returns a tuple of (success, lottery_type, url)
    """
    try:
        lottery_type = screenshot.lottery_type
        url = screenshot.url
        
        logger.info(f"Processing {lottery_type} from {url}")
        
        # Pass the lottery_type to capture_screenshot for better error reporting
        with screenshot_semaphore:
            filepath, _, _ = capture_screenshot(url, lottery_type=lottery_type)
            
        if filepath:
            # Get the current time for both updates to ensure they match exactly
            now = datetime.now()
            
            # Update Screenshot record
            screenshot.path = filepath
            screenshot.timestamp = now
            logger.debug(f"Updated Screenshot timestamp for {lottery_type} to {now}")
            
            # Also update the corresponding ScheduleConfig record if it exists
            config = ScheduleConfig.query.filter_by(url=url).first()
            if config:
                # Use the exact same timestamp for consistency
                config.last_run = now
                logger.debug(f"Updated ScheduleConfig timestamp for {lottery_type} to {now}")
            else:
                logger.warning(f"No ScheduleConfig record found for {lottery_type}")
                
                # Create a ScheduleConfig record if it doesn't exist
                try:
                    new_config = ScheduleConfig(
                        url=url,
                        lottery_type=lottery_type,
                        last_run=now,
                        active=True
                    )
                    db.session.add(new_config)
                    logger.info(f"Created new ScheduleConfig record for {lottery_type}")
                except Exception as e:
                    logger.error(f"Failed to create ScheduleConfig for {lottery_type}: {str(e)}")
            
            # Commit all updates
            try:
                db.session.commit()
                logger.info(f"Successfully captured and updated data for {lottery_type}")
                return (True, lottery_type, url)
            except Exception as e:
                db.session.rollback()
                error_msg = f"Database commit error: {str(e)}"
                logger.error(f"{error_msg} for {lottery_type}")
                diag.log_sync_attempt(lottery_type, url, False, error_msg)
                return (False, lottery_type, url)
        else:
            logger.warning(f"Failed to capture data for {lottery_type}: {url}")
            diag.log_sync_attempt(lottery_type, url, False, "Capture returned no filepath")
            return (False, lottery_type, url)
    
    except Exception as e:
        # Handle any unexpected errors
        error_msg = f"Error processing screenshot task: {str(e)}"
        logger.error(error_msg)
        logger.error(traceback.format_exc())
        
        # Try to get lottery_type from screenshot if it exists
        try:
            lottery_type = screenshot.lottery_type if screenshot else "Unknown"
            url = screenshot.url if screenshot else "Unknown URL"
        except:
            lottery_type = "Unknown"
            url = "Unknown URL"
            
        diag.log_sync_attempt(lottery_type, url, False, error_msg)
        return (False, lottery_type, url)

def capture_all_screenshots():
    """
    Capture screenshots for all lottery URLs in the database with enhanced diagnostics.
    Uses a queue system to ensure all screenshots are processed even with thread limits.
    Returns the number of successful captures or a results dictionary.
    """
    results = {
        'total': 0,
        'success': 0,
        'failure': 0,
        'lottery_types': {}
    }
    
    try:
        # Get all active screenshot configs
        screenshots = Screenshot.query.all()
        
        if not screenshots:
            logger.warning("No screenshot records found in database")
            return results
        
        results['total'] = len(screenshots)
        logger.info(f"Found {len(screenshots)} screenshot URLs to process")
        
        # Create a queue of screenshots to process
        for screenshot in screenshots:
            screenshot_queue.put(screenshot)
        
        # Create worker threads
        threads = []
        for i in range(min(MAX_CONCURRENT_THREADS, len(screenshots))):
            thread = threading.Thread(target=worker)
            thread.daemon = True
            threads.append(thread)
            thread.start()
        
        # Wait for all threads to complete
        # Add a timeout to prevent hanging indefinitely
        max_wait_time = 300  # 5 minutes max wait time
        start_time = time.time()
        
        while not screenshot_queue.empty() and time.time() - start_time < max_wait_time:
            # Calculate approximate percentage complete
            approx_complete = results['success'] + results['failure']
            if results['total'] > 0:
                percent_complete = (approx_complete / results['total']) * 100
                logger.debug(f"Progress: {percent_complete:.1f}% complete ({approx_complete}/{results['total']})")
            time.sleep(5)  # Check every 5 seconds
        
        # Check if we timed out
        if not screenshot_queue.empty():
            remaining = screenshot_queue.qsize()
            logger.warning(f"Timed out waiting for screenshots to complete. {remaining} screenshots still in queue.")
            results['timeout'] = True
            results['remaining'] = remaining
        
        # Join threads with timeout
        for thread in threads:
            thread.join(timeout=1.0)
            
        return results
    
    except Exception as e:
        logger.error(f"Error during capture_all_screenshots: {str(e)}")
        logger.error(traceback.format_exc())
        results['error'] = str(e)
        return results
    
    def worker():
        """Worker thread to process screenshots from the queue"""
        while True:
            try:
                # Get the next screenshot from the queue with a timeout
                try:
                    screenshot = screenshot_queue.get(timeout=1)
                except queue.Empty:
                    # No more items to process
                    break
                
                # Process the screenshot
                success, lottery_type, url = process_screenshot_task(screenshot)
                
                # Update results
                if lottery_type not in results['lottery_types']:
                    results['lottery_types'][lottery_type] = {'success': 0, 'failure': 0}
                
                if success:
                    results['success'] += 1
                    results['lottery_types'][lottery_type]['success'] += 1
                else:
                    results['failure'] += 1
                    results['lottery_types'][lottery_type]['failure'] += 1
                
                # Mark task as done
                screenshot_queue.task_done()
                
            except Exception as e:
                logger.error(f"Error in worker thread: {str(e)}")
                logger.error(traceback.format_exc())
                continue

def sync_single_screenshot(screenshot_id):
    """
    Sync a single screenshot by ID with enhanced diagnostics.
    Returns True if successful, False otherwise.
    """
    try:
        screenshot = Screenshot.query.get(screenshot_id)
        if not screenshot:
            logger.error(f"No screenshot found with ID {screenshot_id}")
            return False
        
        # Process the screenshot
        success, lottery_type, url = process_screenshot_task(screenshot)
        return success
        
    except Exception as e:
        logger.error(f"Error syncing screenshot ID {screenshot_id}: {str(e)}")
        logger.error(traceback.format_exc())
        return False