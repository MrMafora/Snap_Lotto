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
import queue
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
        
    try:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        url_filename = url.split('/')[-1] or 'index'
        filename = f"{timestamp}_{url_filename}.txt"
        filepath = os.path.join(SCREENSHOT_DIR, filename)
        
        logger.debug(f"[{lottery_name}] Capturing data from {url} - Attempt {retry_count + 1}/{MAX_RETRIES}")
        
        # Use urllib to get the HTML content
        try:
            # Add jitter to avoid synchronized anti-bot detection
            jitter_delay = random.uniform(0.5, 2.0)
            if retry_count > 0:
                logger.debug(f"[{lottery_name}] Adding jitter delay of {jitter_delay:.2f}s")
                time.sleep(jitter_delay)
            
            # Use a custom User-Agent to avoid being blocked
            # Rotate between different user agents for variety
            user_agents = [
                'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.0 Safari/605.1.15',
                'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/119.0'
            ]
            headers = {
                'User-Agent': random.choice(user_agents),
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
                
                # Save the HTML content to a file
                with open(filepath, 'wb') as f:
                    f.write(html_content)
                
                logger.info(f"[{lottery_name}] HTML content successfully saved to {filepath}")
                
                # Log the successful attempt
                diag.log_sync_attempt(lottery_name, url, True)
                
                # Return the filepath and data
                return filepath, html_content, None
                
        except urllib.error.HTTPError as e:
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
            
        except urllib.error.URLError as e:
            error_msg = f"URL Error: {str(e.reason)}"
            logger.error(f"[{lottery_name}] {error_msg} for {url}")
            
            # Retry on URL errors (often network-related)
            if retry_count < MAX_RETRIES - 1:
                wait_time = (2 ** retry_count) * 5 + random.uniform(1, 3)
                logger.info(f"[{lottery_name}] Waiting {wait_time:.2f} seconds before retry...")
                time.sleep(wait_time)
                return capture_screenshot(url, retry_count + 1, lottery_type)
            
            diag.log_sync_attempt(lottery_name, url, False, error_msg)
            return None, None, None
            
        except Exception as e:
            error_msg = f"Error during URL fetch: {str(e)}"
            logger.error(f"[{lottery_name}] {error_msg}")
            
            # Retry on general errors
            if retry_count < MAX_RETRIES - 1:
                wait_time = (2 ** retry_count) * 5 + random.uniform(1, 3)
                logger.info(f"[{lottery_name}] Waiting {wait_time:.2f} seconds before retry...")
                time.sleep(wait_time)
                return capture_screenshot(url, retry_count + 1, lottery_type)
            
            diag.log_sync_attempt(lottery_name, url, False, error_msg)
            return None, None, None
            
    except Exception as e:
        error_msg = f"Critical error capturing data: {str(e)}"
        logger.error(f"[{lottery_name}] {error_msg}")
        traceback.print_exc()
        
        diag.log_sync_attempt(lottery_name, url, False, error_msg)
        return None, None, None

@diag.track_sync
def capture_all_screenshots():
    """
    Capture screenshots for all lottery URLs in the database with enhanced diagnostics.
    Returns the number of successful captures.
    """
    success_count = 0
    failed_urls = []
    
    try:
        # Diagnose any existing inconsistencies before starting new captures
        diag.diagnose_sync_issues()
        
        # Get all screenshot records from database
        screenshots = Screenshot.query.all()
        logger.info(f"Found {len(screenshots)} screenshot records to capture")
        
        # Shuffle the order of screenshots to prevent predictable patterns
        # This helps avoid being blocked by anti-scraping measures
        random.shuffle(screenshots)
        
        # Track starting time for overall process
        start_time = datetime.now()
        
        for i, screenshot in enumerate(screenshots):
            lottery_type = screenshot.lottery_type
            url = screenshot.url
            
            try:
                logger.info(f"Processing {i+1}/{len(screenshots)}: {lottery_type} from {url}")
                
                # Add slight delay between requests to avoid overwhelming the target server
                if i > 0:
                    delay = random.uniform(1.0, 3.0)
                    logger.debug(f"Waiting {delay:.2f} seconds before next request")
                    time.sleep(delay)
                
                with screenshot_semaphore:
                    # Pass the lottery_type to capture_screenshot for better error reporting
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
                        success_count += 1
                        logger.info(f"Successfully captured and updated data for {lottery_type}")
                    except Exception as e:
                        db.session.rollback()
                        logger.error(f"Database commit error for {lottery_type}: {str(e)}")
                        failed_urls.append((lottery_type, url))
                        diag.log_sync_attempt(lottery_type, url, False, f"Database commit error: {str(e)}")
                else:
                    failed_urls.append((lottery_type, url))
                    logger.warning(f"Failed to capture data for {lottery_type}: {url}")
                    diag.log_sync_attempt(lottery_type, url, False, "Capture returned no filepath")
                    
            except Exception as e:
                error_msg = f"Error processing data: {str(e)}"
                failed_urls.append((lottery_type, url))
                logger.error(f"Error processing data for {lottery_type}: {str(e)}")
                logger.error(traceback.format_exc())
                diag.log_sync_attempt(lottery_type, url, False, error_msg)
                
                # Try to rollback any failed transaction
                try:
                    db.session.rollback()
                except:
                    pass
        
        # Calculate total duration
        duration = (datetime.now() - start_time).total_seconds()
        
        # Log summary of results
        logger.info(f"Data capture complete: {success_count} successful, {len(failed_urls)} failed in {duration:.2f} seconds")
        for lottery_type, url in failed_urls:
            logger.warning(f"Failed: {lottery_type} - {url}")
        
        # Check for any remaining inconsistencies after captures
        diag.diagnose_sync_issues()
            
        return success_count
        
    except Exception as e:
        logger.error(f"Error in capture_all_screenshots: {str(e)}")
        logger.error(traceback.format_exc())
        
        # Try to rollback any failed transaction
        try:
            db.session.rollback()
        except:
            pass
            
        return 0

@diag.track_sync
def sync_single_screenshot(screenshot_id):
    """
    Sync a single screenshot by ID with enhanced diagnostics.
    Returns True if successful, False otherwise.
    """
    try:
        # Find the screenshot by ID
        screenshot = Screenshot.query.get(screenshot_id)
        if not screenshot:
            logger.error(f"Screenshot with ID {screenshot_id} not found")
            diag.log_sync_attempt("Unknown", f"Screenshot ID: {screenshot_id}", False, "Screenshot ID not found")
            return False
            
        lottery_type = screenshot.lottery_type
        url = screenshot.url
            
        logger.info(f"Syncing data for {lottery_type} from {url}")
        
        with screenshot_semaphore:
            # Pass lottery_type for better error tracking
            filepath, _, _ = capture_screenshot(url, lottery_type=lottery_type)
            
        if filepath:
            # Use the same timestamp for both updates
            now = datetime.now()
            
            # Update the Screenshot record
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
                
                # Create a new ScheduleConfig record if it doesn't exist
                try:
                    new_config = ScheduleConfig(
                        url=url,
                        lottery_type=lottery_type,
                        last_run=now,
                        active=True
                    )
                    db.session.add(new_config)
                    logger.info(f"Created new ScheduleConfig record for {lottery_type}")
                except Exception as config_err:
                    logger.error(f"Failed to create ScheduleConfig for {lottery_type}: {str(config_err)}")
            
            # Commit all updates in a single transaction
            try:
                db.session.commit()
                
                # Run diagnostics to verify timestamp consistency
                consistency_check = all([
                    screenshot.timestamp == now,
                    (not config or config.last_run == now)
                ])
                
                if consistency_check:
                    logger.info(f"Successfully synced data for {lottery_type} with consistent timestamps")
                else:
                    logger.warning(f"Data synced for {lottery_type} but timestamps may be inconsistent")
                
                diag.log_sync_attempt(lottery_type, url, True)
                return True
            except Exception as commit_err:
                db.session.rollback()
                error_msg = f"Database commit error: {str(commit_err)}"
                logger.error(f"{error_msg} for {lottery_type}")
                diag.log_sync_attempt(lottery_type, url, False, error_msg)
                return False
        else:
            error_msg = "Capture returned no filepath"
            logger.warning(f"Failed to sync data for {lottery_type}: {error_msg}")
            diag.log_sync_attempt(lottery_type, url, False, error_msg)
            return False
            
    except Exception as e:
        error_msg = f"Error syncing data: {str(e)}"
        logger.error(f"{error_msg} for screenshot ID {screenshot_id}")
        logger.error(traceback.format_exc())
        
        # Try to extract lottery type and URL for better logging
        lottery_type = "Unknown"
        url = f"Screenshot ID: {screenshot_id}"
        try:
            if 'screenshot' in locals() and screenshot:
                lottery_type = screenshot.lottery_type
                url = screenshot.url
        except:
            pass
        
        diag.log_sync_attempt(lottery_type, url, False, error_msg)
        
        # Try to rollback any failed transaction
        try:
            db.session.rollback()
        except:
            pass
            
        return False