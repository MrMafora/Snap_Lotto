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
    Synchronous wrapper for capturing a screenshot,
    that works safely in threads by creating a new event loop if needed
    
    Args:
        url (str): URL to capture
        filename_prefix (str): Prefix for the filename
        fullpage (bool): Whether to capture the full page
        
    Returns:
        tuple: (success, filepath, html_filepath, error_message)
    """
    # Create a new event loop for thread safety
    try:
        # First try to get the current event loop
        loop = asyncio.get_event_loop()
    except RuntimeError:
        # If we're in a thread without an event loop, create a new one
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    
    # Run the async function and return results
    try:
        return loop.run_until_complete(
            PuppeteerService.capture_screenshot(url, filename_prefix, fullpage)
        )
    except Exception as e:
        logger.error(f"Error in capture_screenshot: {str(e)}")
        return False, None, None, f"Error in capture_screenshot: {str(e)}"

def generate_png_from_html(html_path, output_path=None):
    """
    Generate a PNG thumbnail from an HTML file without using Playwright or wkhtmltoimage
    
    Args:
        html_path (str): Path to the HTML file
        output_path (str, optional): Path to save the PNG file. If None, a temporary file is created.
        
    Returns:
        tuple: (success, filepath, error_message)
    """
    import os
    import tempfile
    from datetime import datetime
    
    # Create a temporary file if no output path is provided
    if not output_path:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        file_basename = os.path.basename(html_path).replace('.html', '')
        output_path = os.path.join(
            tempfile.gettempdir(),
            f"temp_{timestamp}_{file_basename}.png"
        )
    
    logger.info(f"Creating thumbnail for HTML file: {html_path}")
    
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
    
    # Create a simple thumbnail image using PIL/Pillow
    try:
        from PIL import Image, ImageDraw, ImageFont
        
        # Create a basic thumbnail image with lottery branding
        img = Image.new('RGB', (800, 600), color=(255, 248, 240))  # Light warm background
        draw = ImageDraw.Draw(img)
        
        # Add header bar with primary color
        draw.rectangle([(0, 0), (800, 60)], fill=(231, 76, 60))  # Red header (primary color)
        
        # Try to use a default font
        try:
            font = ImageFont.load_default()
            large_font = ImageFont.load_default()
            small_font = ImageFont.load_default()
        except Exception:
            font = None
            large_font = None
            small_font = None
        
        # Get the lottery type from the filename
        lottery_type = ""
        filename = os.path.basename(html_path).lower()
        
        if "lotto_plus_1" in filename or "lottoplus1" in filename:
            lottery_type = "Lottery Plus 1"
        elif "lotto_plus_2" in filename or "lottoplus2" in filename:
            lottery_type = "Lottery Plus 2"
        elif "powerball_plus" in filename or "powerballplus" in filename:
            lottery_type = "Powerball Plus"
        elif "powerball" in filename:
            lottery_type = "Powerball"
        elif "daily_lotto" in filename or "dailylotto" in filename:
            lottery_type = "Daily Lottery"
        elif "lotto" in filename:
            lottery_type = "Lottery"
        else:
            lottery_type = "Lottery Results"
        
        # Draw the lottery type as title
        draw.text((20, 15), f"{lottery_type}", fill=(255, 255, 255), font=large_font)
        
        # Add timestamp
        timestamp_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        draw.text((20, 80), f"HTML Content Available", fill=(50, 50, 50), font=large_font)
        draw.text((20, 120), f"Timestamp: {timestamp_str}", fill=(80, 80, 80), font=font)
        draw.text((20, 150), f"Filesize: {html_file_size} bytes", fill=(80, 80, 80), font=font)
        
        # Add some explanatory text
        draw.text((20, 200), "This HTML file contains the lottery results.", fill=(80, 80, 80), font=font)
        draw.text((20, 230), "Click to view the full HTML content instead of this thumbnail.", fill=(80, 80, 80), font=font)
        
        # Add a yellow box with a message (looks like a lottery ball)
        draw.ellipse([(350, 300), (450, 400)], fill=(255, 222, 89))  # Yellow circle
        draw.text((385, 340), "HTML", fill=(0, 0, 0), font=font)
        
        # Add note at the bottom
        draw.rectangle([(0, 520), (800, 600)], fill=(240, 240, 240))
        draw.text((20, 540), "Note: View the HTML directly for complete lottery results and information.", fill=(80, 80, 80), font=font)
        
        # Save the image
        img.save(output_path)
        logger.info(f"Created HTML thumbnail image: {output_path}")
        return True, output_path, "Used HTML thumbnail image"
    
    except Exception as e:
        logger.error(f"Failed to create thumbnail image: {str(e)}")
        return False, None, f"Failed to generate image: {str(e)}"

def capture_single_screenshot(lottery_type, url):
    """
    Synchronous wrapper for capturing a single screenshot
    with lottery type and URL, using its own event loop in threads
    
    Args:
        lottery_type (str): Type of lottery (used for filename)
        url (str): URL to capture
        
    Returns:
        dict: Result dictionary with status, path, etc.
    """
    try:
        # Create a safe filename from lottery type
        safe_filename = lottery_type.replace(' ', '_').lower()
        
        # Use a safer approach to run async code in a separate thread
        # First, define a helper function that doesn't rely on signals
        def run_async_capture():
            # Create a new event loop specific to this thread
            new_loop = asyncio.new_event_loop()
            asyncio.set_event_loop(new_loop)
            
            try:
                # Run the async function with the new loop
                result = new_loop.run_until_complete(
                    PuppeteerService.capture_screenshot(url, safe_filename)
                )
                new_loop.close()
                return result
            except Exception as inner_e:
                logger.error(f"Error in thread-local async capture for {lottery_type}: {str(inner_e)}")
                new_loop.close()
                return (False, None, None, f"Thread-local async error: {str(inner_e)}")
        
        # Execute the capture in the current thread, but with proper async handling
        # This avoids the signal handling issue in threads
        success, filepath, html_filepath, error_message = run_async_capture()
        
        if not success:
            logger.error(f"Failed to capture screenshot for {lottery_type}: {error_message}")
            return {
                'status': 'failed',
                'error': error_message,
                'url': url
            }
        
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
    Synchronous wrapper for capturing multiple screenshots,
    that works safely in threads by creating a new event loop
    
    Args:
        urls_with_types (list): List of dictionaries with 'url' and 'type' keys
        
    Returns:
        dict: Results for each lottery type
    """
    # Use a safer approach to run async code in a separate thread
    # Define a helper function that doesn't rely on signals
    def run_async_multiple_capture():
        # Create a new event loop specific to this thread
        new_loop = asyncio.new_event_loop()
        asyncio.set_event_loop(new_loop)
        
        try:
            # Run the async function with the new loop
            result = new_loop.run_until_complete(
                PuppeteerService.capture_multiple_screenshots(urls_with_types)
            )
            new_loop.close()
            return result
        except Exception as inner_e:
            logger.error(f"Error in thread-local async capture for multiple screenshots: {str(inner_e)}")
            new_loop.close()
            return {}
    
    # Execute the capture in the current thread, but with proper async handling
    # This avoids the signal handling issue in threads
    try:
        return run_async_multiple_capture()
    except Exception as e:
        logger.error(f"Error in capture_multiple_screenshots: {str(e)}")
        return {}

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