"""
Puppeteer Service for Lottery Screenshots

This module provides a service to capture screenshots from lottery websites using Pyppeteer.
It can be imported and used as part of the main application.
"""

import os
import asyncio
import logging
import traceback
from datetime import datetime
from pyppeteer import launch

# Set up logging
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Ensure the screenshots directory exists
SCREENSHOTS_DIR = 'screenshots'
os.makedirs(SCREENSHOTS_DIR, exist_ok=True)

# Create a specific subfolder for HTML content if needed
HTML_DIR = os.path.join(SCREENSHOTS_DIR, 'html')
os.makedirs(HTML_DIR, exist_ok=True)

class PuppeteerService:
    """Service for capturing screenshots using Pyppeteer"""
    
    @staticmethod
    async def capture_screenshot(url, filename_prefix, fullpage=True):
        """
        Capture a screenshot from a URL with advanced anti-blocking techniques
        
        Args:
            url (str): URL to capture
            filename_prefix (str): Prefix for the filename (e.g., lottery type)
            fullpage (bool): Whether to capture the full page
            
        Returns:
            tuple: (success, filepath, html_filepath, error_message)
        """
        browser = None
        max_attempts = 3
        current_attempt = 0
        
        # List of diverse modern user agents to rotate
        user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.5 Safari/605.1.15',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/116.0.0.0 Safari/537.36 Edg/116.0.1938.69',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/117.0',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/116.0.0.0 Safari/537.36',
            'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:109.0) Gecko/20100101 Firefox/117.0',
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/116.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/116.0.0.0 Safari/537.36 OPR/102.0.0.0',
        ]
        
        # Set different wait strategies for retry attempts
        wait_strategies = ['networkidle0', 'domcontentloaded', 'networkidle2', 'load']
        
        while current_attempt < max_attempts:
            current_attempt += 1
            
            try:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                
                # Define PNG file path (primary screenshot)
                filename = f"{timestamp}_{filename_prefix}.png"
                filepath = os.path.join(SCREENSHOTS_DIR, filename)
                
                # Define HTML file path (stored in HTML_DIR subfolder)
                html_filename = f"{timestamp}_{filename_prefix}.html"
                html_filepath = os.path.join(HTML_DIR, html_filename)
                
                # Log the attempt number
                logger.info(f"Capturing screenshot from {url} (Attempt {current_attempt}/{max_attempts})")
                
                # Add random delay to appear more human-like
                await asyncio.sleep(0.5 + (current_attempt - 1) * 1.5)
                
                # Select different browser arguments for each attempt
                browser_args = [
                    '--no-sandbox',
                    '--disable-setuid-sandbox',
                    '--disable-dev-shm-usage',
                    '--disable-gpu',
                    '--hide-scrollbars',  # Hide scrollbars in screenshots
                ]
                
                # Add more anti-detection flags for aggressive anti-blocking
                anti_detection_args = [
                    '--disable-blink-features=AutomationControlled',  # Critical to avoid detection
                    '--disable-features=IsolateOrigins,site-per-process',  # Better for iframe handling
                    '--disable-web-security',  # Bypass CORS restrictions
                    f'--window-size={1280 + current_attempt * 50},{1024 + current_attempt * 30}',  # Randomize window size
                ]
                
                # Add randomized window size
                browser_args.extend(anti_detection_args)
                
                # Launch browser with appropriate settings for screenshot capture
                browser = await launch(
                    headless=True,
                    ignoreHTTPSErrors=True,  # Bypass SSL errors
                    args=browser_args,
                    ignoreDefaultArgs=['--enable-automation']  # Critical for avoiding detection
                )
                
                # Open new page
                page = await browser.newPage()
                
                # Randomize viewport size slightly with each attempt
                viewport_width = 1280 + int((current_attempt - 1) * 50)
                viewport_height = 1024 + int((current_attempt - 1) * 40)
                await page.setViewport({
                    'width': viewport_width, 
                    'height': viewport_height,
                    'deviceScaleFactor': 1 + (current_attempt - 1) * 0.25,  # Increase scale factor with each attempt
                })
                
                # Choose a random user agent
                selected_user_agent = user_agents[current_attempt % len(user_agents)]
                await page.setUserAgent(selected_user_agent)
                logger.info(f"Using user agent: {selected_user_agent}")
                
                # Set extra HTTP headers to appear more like a real browser
                await page.setExtraHTTPHeaders({
                    'Accept-Language': 'en-US,en;q=0.9,fr;q=0.8,de;q=0.7',
                    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
                    'Cache-Control': 'max-age=0',
                    'Connection': 'keep-alive', 
                    'Upgrade-Insecure-Requests': '1',
                    'Sec-Fetch-Site': 'none',
                    'Sec-Fetch-Mode': 'navigate',
                    'Sec-Fetch-User': '?1',
                    'Sec-Fetch-Dest': 'document',
                    'Accept-Encoding': 'gzip, deflate, br',
                })
                
                # Add JavaScript to mask being a headless browser
                await page.evaluateOnNewDocument("""
                // Overwrite properties that could detect automation
                Object.defineProperty(navigator, 'webdriver', {
                    get: () => false
                });
                Object.defineProperty(navigator, 'plugins', {
                    get: () => [
                        { name: 'Chrome PDF Plugin', filename: 'internal-pdf-viewer' },
                        { name: 'Chrome PDF Viewer', filename: 'mhjfbmdgcfjbbpaeojofohoefgiehjai' },
                        { name: 'Native Client', filename: 'internal-nacl-plugin' }
                    ]
                });
                Object.defineProperty(navigator, 'languages', {
                    get: () => ['en-US', 'en', 'es']
                });
                
                // Overwrite permissions
                const originalQuery = window.navigator.permissions?.query;
                if (originalQuery) {
                    window.navigator.permissions.query = (parameters) => (
                        parameters.name === 'notifications' ?
                            Promise.resolve({ state: Notification.permission }) :
                            originalQuery(parameters)
                    );
                }
                
                // Add randomized timing functions to make detection harder
                const originalSetTimeout = window.setTimeout;
                const originalSetInterval = window.setInterval;
                window.setTimeout = function(cb, time, ...args) {
                    const randomOffset = Math.floor(Math.random() * 10); 
                    return originalSetTimeout(cb, time + randomOffset, ...args);
                };
                window.setInterval = function(cb, time, ...args) {
                    const randomOffset = Math.floor(Math.random() * 10);
                    return originalSetInterval(cb, time + randomOffset, ...args);
                };
                """)
                
                # Intercept and block tracking scripts and bot detection
                await page.setRequestInterception(True)
                
                async def intercept_request(request):
                    # Block known tracking and bot detection scripts
                    blocked_resources = ['google-analytics', 'googletagmanager', 'gtm.js', 
                                       'fingerprint', 'bot-detection', 'captcha']
                    url = request.url.lower()
                    
                    if any(resource in url for resource in blocked_resources):
                        await request.abort()
                    # Allow all other requests
                    else:
                        await request.continue_()
                
                page.on('request', lambda req: asyncio.ensure_future(intercept_request(req)))
                
                # Select different wait strategy based on attempt number
                wait_strategy = wait_strategies[current_attempt % len(wait_strategies)]
                
                # Add increasing timeout for successive attempts
                timeout = 60000 + (current_attempt - 1) * 15000
                
                # Navigate to the URL with appropriate wait conditions
                logger.info(f"Navigating to {url} with strategy: {wait_strategy}, timeout: {timeout}ms")
                response = await page.goto(url, {'waitUntil': wait_strategy, 'timeout': timeout})
                
                # Check response status if available
                if response:
                    status = response.status if hasattr(response, 'status') else 'unknown'
                    logger.info(f"Response status: {status}")
                    
                    if status != 200:
                        logger.warning(f"Non-200 response: {status}")
                
                # Wait for content to be fully loaded
                try:
                    await page.waitForSelector('body', {'visible': True, 'timeout': 30000})
                except Exception as e:
                    logger.warning(f"Error waiting for body: {e}. Will try to continue anyway.")
                
                # Perform some human-like interactions
                random_scroll_count = min(3 + current_attempt, 6)  # More scrolls with each attempt
                
                for i in range(random_scroll_count):
                    # Scroll down in chunks like a human would
                    scroll_amount = 300 + (i * 100)
                    await page.evaluate(f"window.scrollBy(0, {scroll_amount})")
                    await asyncio.sleep(0.3 + (0.1 * i))  # Gradually slower scrolls
                
                # Scroll back to the top
                await page.evaluate("window.scrollTo(0, 0)")
                await asyncio.sleep(0.8)
                
                # Hide cookie banners and other overlays that might block content
                await page.evaluate("""
                () => {
                    // Remove cookie banners and overlays
                    const elementsToRemove = [
                        '.cookie-banner', '#cookie-banner', '.cookie-consent', '#cookie-consent',
                        '.modal', '.modal-backdrop', '.popup', '#popup', '.overlay', '#overlay',
                        '[class*="cookie"]', '[id*="cookie"]', '[class*="consent"]', '[id*="consent"]',
                        '[class*="popup"]', '[id*="popup"]'
                    ];
                    
                    // Remove elements that match selectors
                    elementsToRemove.forEach(selector => {
                        document.querySelectorAll(selector).forEach(el => {
                            el.style.display = 'none';
                            el.style.visibility = 'hidden';
                            el.style.opacity = '0';
                        });
                    });
                    
                    // Remove fixed position elements that might be overlays
                    document.querySelectorAll('body > *').forEach(el => {
                        const style = window.getComputedStyle(el);
                        if (style.position === 'fixed' && 
                            (style.zIndex === 'auto' || parseInt(style.zIndex) > 100)) {
                            el.style.display = 'none';
                        }
                    });
                    
                    // Auto-click cookie accept buttons if they exist
                    ['Accept', 'Accept All', 'I Agree', 'I Accept', 'Continue'].forEach(text => {
                        document.querySelectorAll('button, a, div').forEach(el => {
                            if (el.textContent && el.textContent.includes(text) && 
                                (el.tagName === 'BUTTON' || el.tagName === 'A' || 
                                 el.getAttribute('role') === 'button')) {
                                try { el.click(); } catch (e) {}
                            }
                        });
                    });
                }
                """)
                
                # Wait after manipulations
                await asyncio.sleep(1)
                
                # Take screenshot - THIS IS THE CRITICAL PART
                # First, make sure all content is fully loaded and visible
                await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                await page.evaluate("window.scrollTo(0, 0)")
                await asyncio.sleep(1.5)  # Give it more time to settle after scrolling
                
                # Enhanced screenshot options with improved settings
                screenshot_options = {
                    'path': filepath,
                    'fullPage': fullpage,
                    'type': 'png',
                    'omitBackground': False,
                    'encoding': 'binary',
                    'quality': 100  # Maximum quality for PNG
                }
                
                # Take the screenshot with a larger timeout
                logger.info(f"Taking screenshot with fullPage={fullpage} option")
                try:
                    await page.screenshot(screenshot_options)
                except Exception as e:
                    logger.error(f"Error with fullPage screenshot: {str(e)}")
                
                # Verify the file was created successfully
                if os.path.exists(filepath) and os.path.getsize(filepath) > 10000:  # Ensure file is not tiny
                    logger.info(f"✅ Screenshot successfully saved to {filepath} ({os.path.getsize(filepath)} bytes)")
                    
                    # Save HTML content for backup/debugging
                    try:
                        html_content = await page.content()
                        with open(html_filepath, 'w', encoding='utf-8') as f:
                            f.write(html_content)
                        logger.info(f"HTML content saved to {html_filepath}")
                        
                        # Close the browser
                        await browser.close()
                        browser = None
                        
                        # Success - return file paths
                        return True, filepath, html_filepath, None
                    except Exception as html_error:
                        logger.error(f"Error saving HTML content: {str(html_error)}")
                else:
                    logger.error(f"❌ Screenshot file not created or too small: {filepath}")
                    # Try a second approach with different settings
                    logger.info("Trying alternate screenshot approach")
                    try:
                        # Reset scroll position
                        await page.evaluate("window.scrollTo(0, 0)")
                        
                        # Try with device emulation for different attempt
                        if current_attempt == 2:
                            # Try as mobile device on second attempt
                            await page.emulate({
                                'viewport': {
                                    'width': 375,
                                    'height': 812,
                                    'deviceScaleFactor': 3,
                                    'isMobile': True,
                                    'hasTouch': True,
                                    'isLandscape': False
                                },
                                'userAgent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 15_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/15.0 Mobile/15E148 Safari/604.1'
                            })
                        elif current_attempt >= 3:
                            # Try with a tablet for third attempt
                            await page.emulate({
                                'viewport': {
                                    'width': 768,
                                    'height': 1024,
                                    'deviceScaleFactor': 2,
                                    'isMobile': True,
                                    'hasTouch': True,
                                    'isLandscape': False
                                },
                                'userAgent': 'Mozilla/5.0 (iPad; CPU OS 15_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/15.0 Mobile/15E148 Safari/604.1'
                            })
                        
                        # Try clipping to viewport for more reliable capture
                        viewport = await page.evaluate("""() => {
                            return {
                                width: Math.max(document.documentElement.clientWidth, window.innerWidth || 0),
                                height: Math.max(document.documentElement.clientHeight, window.innerHeight || 0)
                            }
                        }""")
                        
                        screenshot_options = {
                            'path': filepath,
                            'fullPage': False,
                            'clip': {
                                'x': 0,
                                'y': 0,
                                'width': viewport['width'],
                                'height': viewport['height']
                            },
                            'type': 'png'
                        }
                        await page.screenshot(screenshot_options)
                        
                        if os.path.exists(filepath) and os.path.getsize(filepath) > 5000:
                            logger.info(f"✅ Viewport screenshot successful: {filepath} ({os.path.getsize(filepath)} bytes)")
                            
                            # Save HTML even for the fallback approach
                            html_content = await page.content()
                            with open(html_filepath, 'w', encoding='utf-8') as f:
                                f.write(html_content)
                            
                            # Close browser
                            await browser.close()
                            browser = None
                            
                            # Return with success
                            return True, filepath, html_filepath, None
                    except Exception as e:
                        logger.error(f"Alternate screenshot method failed: {str(e)}")
            
            except Exception as e:
                logger.error(f"Error in attempt {current_attempt}/{max_attempts}: {str(e)}")
                
                # Try to close browser if it exists
                if browser:
                    try:
                        await browser.close()
                    except:
                        pass
                    browser = None
                
                # If this was the last attempt, we failed
                if current_attempt >= max_attempts:
                    logger.error(f"All {max_attempts} attempts to capture screenshot failed")
                    return False, None, None, f"Failed after {max_attempts} attempts: {str(e)}"
                
                # Otherwise, continue to next attempt
                logger.info(f"Retrying... Attempt {current_attempt + 1}/{max_attempts}")
                
                # Add increasing delay between retries
                await asyncio.sleep(3 * current_attempt)
        
        # This should never be reached due to the returns in the loop
        return False, None, None, "Unknown error occurred"
    
    @staticmethod
    async def capture_multiple_screenshots(urls_with_types):
        """
        Capture multiple screenshots
        
        Args:
            urls_with_types (list): List of dictionaries with 'url' and 'type' keys
            
        Returns:
            dict: Results for each lottery type
        """
        browser = None
        results = {}
        
        try:
            # Launch browser with optimal settings for screenshots
            browser = await launch(
                headless=True,
                args=[
                    '--no-sandbox',
                    '--disable-setuid-sandbox',
                    '--disable-dev-shm-usage',
                    '--disable-accelerated-2d-canvas',
                    '--disable-gpu',
                    '--window-size=1280,1024'
                ]
            )
            
            for item in urls_with_types:
                url = item['url']
                lottery_type = item['type']
                
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                
                # Define PNG file path (this is the primary screenshot file)
                filename = f"{timestamp}_{lottery_type}.png"
                filepath = os.path.join(SCREENSHOTS_DIR, filename)
                
                # Define HTML file path (stored in HTML_DIR subfolder)
                html_filename = f"{timestamp}_{lottery_type}.html"
                html_filepath = os.path.join(HTML_DIR, html_filename)
                
                logger.info(f"Capturing {lottery_type} from {url}")
                
                try:
                    # Create a new page
                    page = await browser.newPage()
                    
                    # Set viewport size for consistent screenshots
                    await page.setViewport({'width': 1280, 'height': 1024})
                    
                    # Set user agent to avoid detection
                    await page.setUserAgent('Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36')
                    
                    # Navigate to the URL with appropriate wait conditions
                    response = await page.goto(url, {'waitUntil': 'networkidle0', 'timeout': 60000})
                    
                    # Check response status if available
                    if response and hasattr(response, 'ok') and not response.ok:
                        if hasattr(response, 'status'):
                            logger.warning(f"Page response not OK: {response.status} for {url}")
                        else:
                            logger.warning(f"Page response not OK for {url}")
                    
                    # Wait for content to be fully loaded
                    await page.waitForSelector('body', {'visible': True, 'timeout': 30000})
                    
                    # Wait a moment for any dynamic content to fully render
                    await asyncio.sleep(2)
                    
                    # Take screenshot - THIS IS THE CRITICAL PART
                    # First, make sure all content is fully loaded and visible
                    await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                    await page.evaluate("window.scrollTo(0, 0)")
                    await asyncio.sleep(1)  # Give it time to settle after scrolling
                    
                    # Enhanced screenshot options with improved settings
                    screenshot_options = {
                        'path': filepath,
                        'fullPage': True,
                        'type': 'png',
                        'omitBackground': False,
                        'encoding': 'binary',
                        'quality': 100  # Maximum quality for PNG
                    }
                    
                    # Take the screenshot with a larger timeout
                    logger.info(f"Taking screenshot with fullPage=True option")
                    try:
                        await page.screenshot(screenshot_options)
                    except Exception as e:
                        logger.error(f"Error with fullPage screenshot: {str(e)}")
                    
                    # Verify the file was created successfully
                    if os.path.exists(filepath) and os.path.getsize(filepath) > 10000:  # Ensure file is not tiny
                        logger.info(f"✅ Screenshot successfully saved to {filepath} ({os.path.getsize(filepath)} bytes)")
                    else:
                        logger.error(f"❌ Screenshot file not created or too small: {filepath}")
                        # Try a second approach with different settings
                        logger.info("Trying alternate screenshot approach")
                        try:
                            # Reset scroll position
                            await page.evaluate("window.scrollTo(0, 0)")
                            
                            # Try clipping to viewport
                            viewport = await page.evaluate("""() => {
                                return {
                                    width: Math.max(document.documentElement.clientWidth, window.innerWidth || 0),
                                    height: Math.max(document.documentElement.clientHeight, window.innerHeight || 0)
                                }
                            }""")
                            
                            screenshot_options = {
                                'path': filepath,
                                'fullPage': False,
                                'clip': {
                                    'x': 0,
                                    'y': 0,
                                    'width': viewport['width'],
                                    'height': viewport['height']
                                },
                                'type': 'png'
                            }
                            await page.screenshot(screenshot_options)
                            if os.path.exists(filepath) and os.path.getsize(filepath) > 10000:
                                logger.info(f"✅ Viewport screenshot successful: {filepath} ({os.path.getsize(filepath)} bytes)")
                            else:
                                # Last resort - most basic screenshot
                                screenshot_options = {
                                    'path': filepath,
                                    'fullPage': False,
                                    'type': 'png'
                                }
                                await page.screenshot(screenshot_options)
                                logger.info(f"✅ Basic screenshot approach: {filepath} ({os.path.getsize(filepath)} bytes)")
                        except Exception as e:
                            logger.error(f"All screenshot attempts failed: {str(e)}")
                    
                    # Save HTML content for backup/debugging
                    html_content = await page.content()
                    with open(html_filepath, 'w', encoding='utf-8') as f:
                        f.write(html_content)
                    logger.info(f"✅ HTML content saved to {html_filepath}")
                    
                    # Close the page
                    await page.close()
                    
                    results[lottery_type] = {
                        'status': 'success',
                        'path': filepath,
                        'html_path': html_filepath,
                        'url': url
                    }
                except Exception as e:
                    logger.error(f"❌ Error capturing {lottery_type}: {str(e)}")
                    traceback.print_exc()
                    results[lottery_type] = {
                        'status': 'failed',
                        'message': str(e),
                        'url': url
                    }
                
                # Add a delay between captures to avoid rate limiting
                await asyncio.sleep(3)
        except Exception as e:
            logger.error(f"Error in capture process: {str(e)}")
            traceback.print_exc()
        finally:
            # Ensure browser is closed
            if browser:
                await browser.close()
        
        return results

def capture_screenshot(url, filename_prefix, fullpage=True):
    """
    Synchronous wrapper for capturing a screenshot
    
    Args:
        url (str): URL to capture
        filename_prefix (str): Prefix for the filename
        fullpage (bool): Whether to capture the full page
        
    Returns:
        tuple: (success, filepath, html_filepath, error_message)
    """
    return asyncio.get_event_loop().run_until_complete(
        PuppeteerService.capture_screenshot(url, filename_prefix, fullpage)
    )

def generate_png_from_html(html_path, output_path=None):
    """
    Generate a PNG screenshot from an HTML file using Playwright
    
    Args:
        html_path (str): Path to the HTML file
        output_path (str, optional): Path to save the PNG file. If None, a temporary file is created.
        
    Returns:
        tuple: (success, filepath, error_message)
    """
    import os
    import tempfile
    import random
    import time
    from datetime import datetime
    from playwright.sync_api import sync_playwright
    
    # Create a temporary file if no output path is provided
    if not output_path:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        file_basename = os.path.basename(html_path).replace('.html', '')
        output_path = os.path.join(
            tempfile.gettempdir(),
            f"temp_{timestamp}_{file_basename}.png"
        )
    
    logger.info(f"Generating PNG from HTML file: {html_path}")
    
    # Check if HTML file exists and has content
    if not os.path.exists(html_path):
        error_message = f"HTML file does not exist: {html_path}"
        logger.error(error_message)
        return False, None, error_message
    
    # Check file size to make sure it has content
    html_file_size = os.path.getsize(html_path)
    if html_file_size < 100:  # Extremely small HTML file is likely empty or corrupt
        error_message = f"HTML file is too small ({html_file_size} bytes): {html_path}"
        logger.error(error_message)
        return False, None, error_message
    
    # Read file content
    try:
        with open(html_path, 'r', encoding='utf-8', errors='ignore') as f:
            html_content = f.read()
    except Exception as e:
        logger.error(f"Failed to read HTML file: {e}")
        return False, None, f"Failed to read HTML file: {e}"
    
    # Directly create a screenshot from the HTML content using a reliable approach
    for attempt in range(1, 4):  # Try up to 3 times with different approaches
        logger.info(f"Attempt {attempt} to generate PNG from HTML")
        try:
            # Use a different approach based on attempt number
            with sync_playwright() as p:
                # Choose a different browser engine for each attempt
                if attempt == 1:
                    browser_engine = p.chromium
                elif attempt == 2:
                    browser_engine = p.firefox
                else:
                    browser_engine = p.webkit
                
                # Launch the selected browser
                browser = browser_engine.launch(
                    headless=True,
                    args=[
                        '--no-sandbox',
                        '--disable-setuid-sandbox',
                        '--disable-dev-shm-usage',
                        '--disable-web-security',
                        '--allow-file-access-from-files',
                        '--disable-features=site-per-process',
                    ]
                )
                
                # Create different browser contexts for each attempt
                if attempt == 1:
                    # Standard desktop context
                    context = browser.new_context(
                        viewport={'width': 1280, 'height': 800},
                        user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36'
                    )
                elif attempt == 2:
                    # Mobile context
                    context = browser.new_context(
                        viewport={'width': 414, 'height': 896},
                        user_agent='Mozilla/5.0 (iPhone; CPU iPhone OS 16_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.0 Mobile/15E148 Safari/604.1',
                        is_mobile=True,
                        has_touch=True
                    )
                else:
                    # Tablet context
                    context = browser.new_context(
                        viewport={'width': 1024, 'height': 768},
                        user_agent='Mozilla/5.0 (iPad; CPU OS 15_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/15.0 Mobile/15E148 Safari/604.1',
                        is_mobile=True, 
                        has_touch=True
                    )
                
                # Create a new page
                page = context.new_page()
                
                # IMPORTANT: Since we're having issues with file:// protocol, 
                # we'll create a data URI to load the HTML directly instead
                safe_html = html_content.replace('\n', ' ').replace('"', '\\"')
                data_uri = f"data:text/html;charset=utf-8,{safe_html}"
                
                # Set a longer timeout and try different loading strategies
                page.set_default_timeout(45000)
                
                # Intercept all requests to fix paths (for images and resources)
                # This will help with HTML files that have relative paths
                base_dir = os.path.dirname(os.path.abspath(html_path))
                
                def handle_route(route):
                    url = route.request.url
                    if url.startswith('file://'):
                        # Convert file URL to actual file path
                        file_path = url.replace('file://', '')
                        try:
                            with open(file_path, 'rb') as f:
                                body = f.read()
                                route.fulfill(body=body)
                        except:
                            route.continue_()
                    else:
                        route.continue_()
                
                page.route('**/*', handle_route)
                
                # Load the HTML directly as data URI to avoid file:// protocol issues
                logger.info(f"Loading HTML content as data URI")
                page.goto(data_uri, timeout=30000)
                
                # Wait for the page to load
                page.wait_for_load_state("domcontentloaded")
                
                # Scroll through the page to ensure all content is loaded
                page.evaluate("window.scrollTo(0, document.body.scrollHeight / 2)")
                time.sleep(0.5)
                page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                time.sleep(0.5)
                page.evaluate("window.scrollTo(0, 0)")
                time.sleep(0.5)
                
                # Take the screenshot
                logger.info(f"Taking screenshot to: {output_path}")
                
                try:
                    # First try full page screenshot
                    page.screenshot(path=output_path, full_page=True)
                except Exception as e:
                    logger.warning(f"Full page screenshot failed, trying viewport screenshot: {e}")
                    # Fall back to viewport screenshot
                    page.screenshot(path=output_path)
                
                # Clean up
                context.close()
                browser.close()
                
                # Check if a valid screenshot was created
                if os.path.exists(output_path) and os.path.getsize(output_path) > 3000:
                    logger.info(f"✅ Successfully created PNG: {output_path} ({os.path.getsize(output_path)} bytes)")
                    return True, output_path, None
                    
                logger.warning(f"Screenshot attempt {attempt} produced unusable image ({os.path.getsize(output_path)} bytes)")
        
        except Exception as e:
            logger.error(f"Error in attempt {attempt}: {str(e)}")
    
    # If all previous attempts failed, use a direct library approach as last resort
    try:
        # Use HTML2Image or wkhtmltopdf approach as a last resort
        logger.info("Trying direct HTML rendering as final approach")
        
        try:
            # Try using wkhtmltoimage if available
            import subprocess
            
            # Create a temporary HTML file with the content
            temp_html = tempfile.NamedTemporaryFile(suffix='.html', delete=False)
            temp_html.write(html_content.encode('utf-8'))
            temp_html.close()
            
            # Try using wkhtmltoimage
            cmd = ['wkhtmltoimage', '--enable-local-file-access', '--quality', '100', temp_html.name, output_path]
            subprocess.check_output(cmd, stderr=subprocess.STDOUT)
            
            # Clean up
            os.unlink(temp_html.name)
            
            if os.path.exists(output_path) and os.path.getsize(output_path) > 1000:
                logger.info(f"✅ Successfully created PNG with wkhtmltoimage: {output_path}")
                return True, output_path, None
        except:
            logger.warning("wkhtmltoimage approach failed, trying Pillow fallback")
    
        # Last resort: Create a simple image with HTML preview text
        from PIL import Image, ImageDraw, ImageFont
        
        # Create a basic image
        img = Image.new('RGB', (1280, 1024), color=(250, 250, 250))
        draw = ImageDraw.Draw(img)
        
        # Add basic HTML preview (first 1000 chars)
        preview_text = html_content[:1000].replace('<', '[').replace('>', ']')
        
        # Draw text with word wrapping
        y_position = 20
        x_position = 20
        max_width = 1240
        
        # Split text into multiple lines
        words = preview_text.split()
        lines = []
        current_line = []
        
        for word in words:
            test_line = ' '.join(current_line + [word])
            if len(test_line) * 10 < max_width:  # Approximating text width
                current_line.append(word)
            else:
                lines.append(' '.join(current_line))
                current_line = [word]
        
        if current_line:
            lines.append(' '.join(current_line))
        
        # Draw header
        draw.text((x_position, y_position), f"HTML Preview Image", fill=(0, 0, 0))
        y_position += 30
        
        draw.text((x_position, y_position), f"Original file: {os.path.basename(html_path)}", fill=(0, 0, 0))
        y_position += 30
        
        draw.text((x_position, y_position), f"Size: {html_file_size} bytes", fill=(0, 0, 0))
        y_position += 50
        
        # Draw preview text
        for line in lines[:30]:  # Limit to 30 lines
            draw.text((x_position, y_position), line, fill=(100, 100, 100))
            y_position += 25
        
        # Add note at the bottom
        draw.text((x_position, 950), "Note: This is a fallback image as HTML rendering was not possible.", fill=(255, 0, 0))
        
        # Save the image
        img.save(output_path)
        logger.info(f"Created fallback HTML preview image: {output_path}")
        return True, output_path, "Used fallback HTML preview"
    
    except Exception as e:
        logger.error(f"All approaches failed: {str(e)}")
        return False, None, f"Failed to generate image: {str(e)}"

def capture_single_screenshot(lottery_type, url):
    """
    Synchronous wrapper for capturing a single screenshot
    with lottery type and URL
    
    Args:
        lottery_type (str): Type of lottery (used for filename)
        url (str): URL to capture
        
    Returns:
        dict: Result dictionary with status, path, etc.
    """
    try:
        # Create a safe filename from lottery type
        safe_filename = lottery_type.replace(' ', '_').lower()
        
        # Capture the screenshot
        success, filepath, html_filepath, error_message = capture_screenshot(url, safe_filename)
        
        if success and filepath:
            return {
                'status': 'success',
                'path': filepath,
                'html_path': html_filepath,
                'url': url
            }
        else:
            return {
                'status': 'failed',
                'error': error_message or 'Unknown error',
                'url': url
            }
    except Exception as e:
        logger.error(f"Error in capture_single_screenshot for {lottery_type}: {str(e)}")
        return {
            'status': 'failed',
            'error': str(e),
            'url': url
        }

def capture_multiple_screenshots(urls_with_types):
    """
    Synchronous wrapper for capturing multiple screenshots
    
    Args:
        urls_with_types (list): List of dictionaries with 'url' and 'type' keys
        
    Returns:
        dict: Results for each lottery type
    """
    return asyncio.get_event_loop().run_until_complete(
        PuppeteerService.capture_multiple_screenshots(urls_with_types)
    )

def update_screenshot_database(results, screenshot_model, db, map_type_to_db=None):
    """
    Update database with screenshot paths
    
    Args:
        results (dict): Results from capture_multiple_screenshots
        screenshot_model: Database model for screenshots
        db: SQLAlchemy database instance
        map_type_to_db (dict, optional): Mapping from lottery types to database names
        
    Returns:
        tuple: (success, updates, creates)
    """
    if map_type_to_db is None:
        map_type_to_db = {
            'lotto_history': 'Lotto',
            'lotto_plus_1_history': 'Lotto Plus 1',
            'lotto_plus_2_history': 'Lotto Plus 2',
            'powerball_history': 'Powerball',
            'powerball_plus_history': 'Powerball Plus',
            'daily_lotto_history': 'Daily Lotto',
            'lotto_results': 'Lotto Results',
            'lotto_plus_1_results': 'Lotto Plus 1 Results',
            'lotto_plus_2_results': 'Lotto Plus 2 Results',
            'powerball_results': 'Powerball Results',
            'powerball_plus_results': 'Powerball Plus Results',
            'daily_lotto_results': 'Daily Lotto Results',
        }
    
    try:
        updates = 0
        creates = 0
        
        for lottery_type, result in results.items():
            if result.get('status') != 'success':
                logger.warning(f"Skipping {lottery_type} due to capture failure")
                continue
            
            db_name = map_type_to_db.get(lottery_type)
            if not db_name:
                logger.warning(f"No database mapping for {lottery_type}")
                continue
            
            # Get filepath from result
            filepath = result.get('path')
            if not filepath:
                logger.warning(f"No filepath for {lottery_type}")
                continue
            
            # Look for exact match first
            screenshot = screenshot_model.query.filter_by(lottery_type=db_name).first()
            
            if not screenshot:
                # Try partial match
                for s in screenshot_model.query.all():
                    if db_name.lower() in s.lottery_type.lower():
                        screenshot = s
                        break
            
            # Get HTML path from result if available
            html_filepath = result.get('html_path')
            
            if screenshot:
                # Update existing record
                old_path = screenshot.path
                screenshot.path = filepath
                
                # Update HTML path if available
                if html_filepath:
                    screenshot.html_path = html_filepath
                    logger.info(f"Updated HTML path: {html_filepath}")
                
                screenshot.timestamp = datetime.now()
                logger.info(f"Updated {db_name} record: {old_path} -> {filepath}")
                updates += 1
            else:
                # Create new record
                url = result.get('url', '')
                
                screenshot = screenshot_model(
                    lottery_type=db_name,
                    url=url,
                    path=filepath,
                    html_path=html_filepath,  # Set HTML path when creating new record
                    timestamp=datetime.now()
                )
                db.session.add(screenshot)
                logger.info(f"Created new record for {db_name} with {filepath}")
                creates += 1
        
        # Commit all changes
        db.session.commit()
        logger.info(f"Database updated successfully. {updates} records updated, {creates} records created.")
        return True, updates, creates
    except Exception as e:
        logger.error(f"Error updating database: {str(e)}")
        return False, 0, 0

# Default lottery URLs for convenience (dictionary format for easier access)
LOTTERY_URLS = {
    # History URLs
    'Lotto': 'https://www.nationallottery.co.za/lotto-history',
    'Lotto Plus 1': 'https://www.nationallottery.co.za/lotto-plus-1-history',
    'Lotto Plus 2': 'https://www.nationallottery.co.za/lotto-plus-2-history',
    'Powerball': 'https://www.nationallottery.co.za/powerball-history',
    'Powerball Plus': 'https://www.nationallottery.co.za/powerball-plus-history',
    'Daily Lotto': 'https://www.nationallottery.co.za/daily-lotto-history',
    
    # Results URLs
    'Lotto Results': 'https://www.nationallottery.co.za/results/lotto',
    'Lotto Plus 1 Results': 'https://www.nationallottery.co.za/results/lotto-plus-1-results',
    'Lotto Plus 2 Results': 'https://www.nationallottery.co.za/results/lotto-plus-2-results',
    'Powerball Results': 'https://www.nationallottery.co.za/results/powerball',
    'Powerball Plus Results': 'https://www.nationallottery.co.za/results/powerball-plus',
    'Daily Lotto Results': 'https://www.nationallottery.co.za/results/daily-lotto',
}

# Legacy format for backward compatibility
LOTTERY_URLS_LIST = [
    # History URLs
    {'url': 'https://www.nationallottery.co.za/lotto-history', 'type': 'lotto_history'},
    {'url': 'https://www.nationallottery.co.za/lotto-plus-1-history', 'type': 'lotto_plus_1_history'},
    {'url': 'https://www.nationallottery.co.za/lotto-plus-2-history', 'type': 'lotto_plus_2_history'},
    {'url': 'https://www.nationallottery.co.za/powerball-history', 'type': 'powerball_history'},
    {'url': 'https://www.nationallottery.co.za/powerball-plus-history', 'type': 'powerball_plus_history'},
    {'url': 'https://www.nationallottery.co.za/daily-lotto-history', 'type': 'daily_lotto_history'},
    
    # Results URLs
    {'url': 'https://www.nationallottery.co.za/results/lotto', 'type': 'lotto_results'},
    {'url': 'https://www.nationallottery.co.za/results/lotto-plus-1-results', 'type': 'lotto_plus_1_results'},
    {'url': 'https://www.nationallottery.co.za/results/lotto-plus-2-results', 'type': 'lotto_plus_2_results'},
    {'url': 'https://www.nationallottery.co.za/results/powerball', 'type': 'powerball_results'},
    {'url': 'https://www.nationallottery.co.za/results/powerball-plus', 'type': 'powerball_plus_results'},
    {'url': 'https://www.nationallottery.co.za/results/daily-lotto', 'type': 'daily_lotto_results'},
]

# Simple test function
if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "single":
        # Test single screenshot capture
        url = 'https://www.nationallottery.co.za/lotto-history'
        success, filepath, html_filepath, error = capture_screenshot(url, 'test_lotto')
        if success:
            print(f"Screenshot captured successfully: {filepath}")
            print(f"HTML content saved to: {html_filepath}")
        else:
            print(f"Error: {error}")
    elif len(sys.argv) > 1 and sys.argv[1] == "single_new":
        # Test single screenshot capture using new function
        lottery_type = "Lotto"
        if lottery_type in LOTTERY_URLS:
            url = LOTTERY_URLS[lottery_type]
            result = capture_single_screenshot(lottery_type, url)
            status = "Success" if result.get('status') == 'success' else "Failed"
            print(f"{lottery_type}: {status}")
            if result.get('status') == 'success':
                print(f"  Screenshot: {result.get('path')}")
                print(f"  HTML path: {result.get('html_path')}")
            else:
                print(f"  Error: {result.get('error')}")
        else:
            print(f"Error: Lottery type '{lottery_type}' not found in LOTTERY_URLS")
    else:
        # Test multiple screenshot capture (using legacy format for compatibility)
        # Convert first two items from the dictionary to list format
        test_urls = []
        for i, (lottery_type, url) in enumerate(LOTTERY_URLS.items()):
            if i < 2:  # Just test first two
                test_urls.append({'type': lottery_type, 'url': url})
        
        results = capture_multiple_screenshots(test_urls)  # Just capture first two URLs for testing
        
        # Print results
        for lottery_type, result in results.items():
            status = "Success" if result.get('status') == 'success' else "Failed"
            print(f"{lottery_type}: {status}")
            if result.get('status') == 'success':
                print(f"  Screenshot: {result.get('path')}")
                print(f"  HTML content: {result.get('html_path')}")
            else:
                print(f"  Error: {result.get('message')}")
                
        print("\nTesting single_screenshot function:")
        # Test the single_screenshot function with the first URL
        first_type = list(LOTTERY_URLS.keys())[0]
        first_url = LOTTERY_URLS[first_type]
        result = capture_single_screenshot(first_type, first_url)
        status = "Success" if result.get('status') == 'success' else "Failed"
        print(f"{first_type}: {status}")
        if result.get('status') == 'success':
            print(f"  Screenshot: {result.get('path')}")
            print(f"  HTML path: {result.get('html_path')}")
        else:
            print(f"  Error: {result.get('error')}")