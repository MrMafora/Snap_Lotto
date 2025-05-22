"""
Playwright-based screenshot manager for capturing lottery website screenshots
Use this only when you need full browser capabilities for JavaScript-heavy websites.
"""
import os
import logging
import traceback
from datetime import datetime
import threading
from models import db, Screenshot

logger = logging.getLogger(__name__)

# Create directory for screenshots if it doesn't exist
SCREENSHOT_DIR = os.path.join(os.getcwd(), 'screenshots')
os.makedirs(SCREENSHOT_DIR, exist_ok=True)

def ensure_playwright_browsers():
    """
    Ensure that Playwright browsers are installed.
    This should be run once at the start of the application.
    """
    try:
        import subprocess
        subprocess.check_call(['playwright', 'install', 'chromium'])
        logger.info("Playwright browsers installed successfully")
    except Exception as e:
        logger.error(f"Error installing Playwright browsers: {str(e)}")

def capture_screenshot_with_playwright(url, lottery_type=None):
    """
    Capture screenshot of the specified URL using Playwright.
    This uses a full browser instance to properly render JavaScript and bypass anti-scraping measures.
    
    Args:
        url (str): The URL to capture
        lottery_type (str, optional): The type of lottery. If None, extracted from URL.
        
    Returns:
        tuple: (filepath, screenshot_data, zoom_filepath) or (None, None, None) if failed
    """
    if not lottery_type:
        from screenshot_manager_light import extract_lottery_type_from_url
        lottery_type = extract_lottery_type_from_url(url)
    
    try:
        # Import Playwright here to avoid dependency issues if not installed
        from playwright.sync_api import sync_playwright
        import time
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{timestamp}_{url.split('/')[-1]}.png"
        filepath = os.path.join(SCREENSHOT_DIR, filename)
        
        logger.info(f"Capturing screenshot from {url} using Playwright")
        
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
                logger.info(f"Using Chromium from: {path}")
                chromium_path = path
                break
                
        # Use Playwright to capture screenshot with built-in timeouts
        with sync_playwright() as p:
            browser_type = p.chromium
            
            try:
                browser = browser_type.launch(
                    headless=True,
                    executable_path=chromium_path
                )
                
                context = browser.new_context(
                    viewport={'width': 1280, 'height': 1600},
                    user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
                )
                
                page = context.new_page()
                
                # Set extra HTTP headers to appear more like a real browser
                page.set_extra_http_headers({
                    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
                    "Accept-Language": "en-US,en;q=0.9",
                    "Accept-Encoding": "gzip, deflate, br",
                    "Connection": "keep-alive",
                    "Upgrade-Insecure-Requests": "1",
                    "Sec-Fetch-Dest": "document",
                    "Sec-Fetch-Mode": "navigate",
                    "Sec-Fetch-Site": "none",
                    "Sec-Fetch-User": "?1",
                    "DNT": "1"
                })
                
                # Navigate and wait for the page to fully load with a timeout
                start_time = time.time()
                max_time = 30  # Maximum time in seconds
                
                try:
                    # Try to navigate with a 20-second timeout
                    page.goto(url, wait_until='networkidle', timeout=20000)
                except Exception as e:
                    # If timeout occurs, log but continue - we might still get a partial page
                    logger.warning(f"Page navigation timeout for {url}: {str(e)}")
                    
                    # Since we caught the timeout, let's try to continue with whatever page was loaded
                    if time.time() - start_time > max_time:
                        logger.error("Exceeded maximum time, aborting")
                        raise TimeoutError("Screenshot capture exceeded maximum time")
                
                # Scroll down to ensure all content is loaded
                try:
                    page.evaluate('window.scrollTo(0, document.body.scrollHeight)')
                    page.wait_for_timeout(1000)  # Wait a second for any animations
                except Exception as e:
                    logger.warning(f"Error during page scrolling: {str(e)}")
                
                # Save the full page screenshot
                page.screenshot(path=filepath, full_page=True)
                logger.info(f"Full screenshot saved to {filepath}")
                
                # Create a separate zoomed-in screenshot of the main data
                zoom_filepath = None
                try:
                    # For results pages, try to capture the specific lottery results box
                    if 'results' in url.lower():
                        # Look for the main results container with lottery numbers and divisions
                        main_content = None
                        
                        # Try several potential selectors for the main content
                        selectors = [
                            '.results-section', 
                            '.lottery-results', 
                            '.main-content',
                            '.results-container',
                            '#results-container',
                            'table.results-table',
                            'div.container'
                        ]
                        
                        for selector in selectors:
                            try:
                                main_content = page.query_selector(selector)
                                if main_content:
                                    logger.info(f"Found main content with selector: {selector}")
                                    break
                            except:
                                continue
                        
                        # If we couldn't find a specific selector, try to find the red-bordered section
                        # by looking for typical content like lottery numbers or division tables
                        if not main_content:
                            # Look for lottery number balls (they usually have specific classes)
                            ball_selectors = [
                                '.lottery-ball', 
                                '.ball',
                                '.number-ball',
                                '.winning-number',
                                'span[class*="ball"]',
                                'div[class*="ball"]'
                            ]
                            
                            for selector in ball_selectors:
                                try:
                                    balls = page.query_selector_all(selector)
                                    if balls and len(balls) > 5:  # Typical lottery has at least 6 numbers
                                        # Get the parent element that contains all balls
                                        parent = page.evaluate('el => el.parentElement.parentElement', balls[0])
                                        if parent:
                                            main_content = parent
                                            logger.info(f"Found lottery balls with selector: {selector}")
                                            break
                                except:
                                    continue
                        
                        # As a fallback, try using a more generic approach by looking for content
                        # with lottery keywords like "winning numbers" or "division"
                        if not main_content:
                            try:
                                # Look for text content that indicates lottery results
                                main_content = page.query_selector('div:has-text("WINNING NUMBERS"), div:has-text("Divisions"), div:has-text("DIVISION"), table:has-text("WINNERS")')
                                logger.info("Found main content using text content search")
                            except:
                                pass
                        
                        # If we found content to zoom in on
                        if main_content:
                            # Use a custom filename for the zoomed screenshot
                            zoom_filename = f"{timestamp}_{url.split('/')[-1]}_zoomed.png"
                            zoom_filepath = os.path.join(SCREENSHOT_DIR, zoom_filename)
                            
                            # Take a screenshot of just this element with a bit of padding
                            bounding_box = main_content.bounding_box()
                            if bounding_box:
                                # Add 20px padding around the element
                                clip = {
                                    'x': max(0, bounding_box['x'] - 20),
                                    'y': max(0, bounding_box['y'] - 20),
                                    'width': bounding_box['width'] + 40,
                                    'height': bounding_box['height'] + 40
                                }
                                
                                # Take the zoomed screenshot
                                page.screenshot(path=zoom_filepath, clip=clip)
                                logger.info(f"Zoomed screenshot saved to {zoom_filepath}")
                        else:
                            logger.warning("Could not find a specific content area to zoom in on")
                
                except Exception as e:
                    logger.error(f"Error creating zoomed screenshot: {str(e)}")
                    # Continue with the regular screenshot even if zoomed fails
                
                logger.info(f"Screenshot process completed for {url}")
                
                # Read the full screenshot data
                with open(filepath, 'rb') as f:
                    screenshot_data = f.read()
                
                # Save the HTML content for potential parsing
                html_filepath = os.path.splitext(filepath)[0] + '.html'
                html_content = page.content()
                with open(html_filepath, 'w', encoding='utf-8') as f:
                    f.write(html_content)
                
                browser.close()
                
                # Create a Screenshot record in the database
                try:
                    screenshot = Screenshot(
                        url=url,
                        lottery_type=lottery_type,
                        timestamp=datetime.now(),
                        path=filepath,
                        processed=False
                    )
                    db.session.add(screenshot)
                    db.session.commit()
                    logger.info(f"Screenshot record added to database for {lottery_type}")
                except Exception as e:
                    logger.error(f"Error saving screenshot record to database: {str(e)}")
                
                # Return with or without zoomed path
                return filepath, screenshot_data, zoom_filepath
                
            except Exception as e:
                logger.error(f"Playwright screenshot capture failed: {str(e)}")
                traceback.print_exc()
                
                # Clean up any browser instances
                try:
                    browser.close()
                except:
                    pass
                
                return None, None, None
            
    except Exception as e:
        logger.error(f"Error capturing screenshot with Playwright: {str(e)}")
        traceback.print_exc()
        return None, None, None