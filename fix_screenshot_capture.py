"""
Fix Screenshot Capture

This script directly captures screenshots using Playwright and updates the database
"""
import os
import sys
import logging
import time
from datetime import datetime
from PIL import Image, ImageDraw, ImageFont
from config import Config

# Configure logging
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Ensure screenshot directory exists
os.makedirs('screenshots', exist_ok=True)

# URLs to capture
LOTTERY_URLS = [
    {'url': 'https://www.nationallottery.co.za/results/lotto', 'lottery_type': 'Lotto'},
    {'url': 'https://www.nationallottery.co.za/results/lotto-plus-1-results', 'lottery_type': 'Lotto Plus 1'},
    {'url': 'https://www.nationallottery.co.za/results/lotto-plus-2-results', 'lottery_type': 'Lotto Plus 2'},
    {'url': 'https://www.nationallottery.co.za/results/powerball', 'lottery_type': 'Powerball'},
    {'url': 'https://www.nationallottery.co.za/results/powerball-plus', 'lottery_type': 'Powerball Plus'},
    {'url': 'https://www.nationallottery.co.za/results/daily-lotto', 'lottery_type': 'Daily Lotto'},
    {'url': 'https://www.nationallottery.co.za/lotto-history', 'lottery_type': 'Lotto History'},
    {'url': 'https://www.nationallottery.co.za/lotto-plus-1-history', 'lottery_type': 'Lotto Plus 1 History'},
    {'url': 'https://www.nationallottery.co.za/lotto-plus-2-history', 'lottery_type': 'Lotto Plus 2 History'},
    {'url': 'https://www.nationallottery.co.za/powerball-history', 'lottery_type': 'Powerball History'},
    {'url': 'https://www.nationallottery.co.za/powerball-plus-history', 'lottery_type': 'Powerball Plus History'},
    {'url': 'https://www.nationallottery.co.za/daily-lotto-history', 'lottery_type': 'Daily Lotto History'}
]

def create_placeholder_image(lottery_type, timestamp=None, width=800, height=600):
    """
    Create a placeholder image with lottery information
    
    Args:
        lottery_type (str): Type of lottery
        timestamp (datetime, optional): Timestamp for the image
        width (int): Width of the image
        height (int): Height of the image
        
    Returns:
        tuple: (filepath, image_data)
    """
    try:
        # Create a timestamp if not provided
        ts = timestamp or datetime.now()
        ts_str = ts.strftime("%Y%m%d_%H%M%S")
        
        # Create filename
        filename = f"{ts_str}_{lottery_type.lower().replace(' ', '-').replace('/', '-')}.png"
        filepath = os.path.join('screenshots', filename)
        
        # Create a blank image with white background
        image = Image.new('RGB', (width, height), color=(255, 255, 255))
        draw = ImageDraw.Draw(image)
        
        # Draw header background
        draw.rectangle([(0, 0), (width, 60)], fill=(0, 51, 102))  # Dark blue header
        
        # Draw title
        title = f"{lottery_type} Screenshot"
        draw.text((20, 20), title, fill=(255, 255, 255))  # White text
        
        # Draw timestamp
        timestamp_str = ts.strftime("%Y-%m-%d %H:%M:%S")
        draw.text((20, 80), f"Generated: {timestamp_str}", fill=(0, 0, 0))
        
        # Draw information
        draw.text((20, 120), "This is a placeholder screenshot.", fill=(0, 0, 0))
        draw.text((20, 150), "The actual screenshot could not be captured.", fill=(0, 0, 0))
        draw.text((20, 180), "Please try regenerating the screenshot.", fill=(0, 0, 0))
        
        # Save the image
        image.save(filepath)
        
        # Read the image data
        with open(filepath, 'rb') as f:
            image_data = f.read()
        
        logger.info(f"Created placeholder image: {filepath}")
        
        return filepath, image_data
    except Exception as e:
        logger.error(f"Failed to create placeholder image: {str(e)}")
        return None, None

def capture_screenshot_with_playwright(url, lottery_type):
    """
    Capture a screenshot using Playwright
    
    Args:
        url (str): URL to capture
        lottery_type (str): Type of lottery
        
    Returns:
        tuple: (filepath, screenshot_data, error_message)
    """
    try:
        # Create a timestamp for the filename
        timestamp = datetime.now()
        timestamp_str = timestamp.strftime("%Y%m%d_%H%M%S")
        filename = f"{timestamp_str}_{lottery_type.lower().replace(' ', '-').replace('/', '-')}.png"
        filepath = os.path.join('screenshots', filename)
        
        logger.info(f"Capturing screenshot from {url} for {lottery_type}")
        
        # Import playwright here to avoid import issues
        from playwright.sync_api import sync_playwright
        
        # Define user agents for rotation
        user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/96.0.4664.110 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:95.0) Gecko/20100101 Firefox/95.0',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/15.1 Safari/605.1.15',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/97.0.4692.71 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:96.0) Gecko/20100101 Firefox/96.0'
        ]
        import random
        user_agent = random.choice(user_agents)
        
        with sync_playwright() as p:
            # Launch browser with additional arguments to improve stability
            browser = p.chromium.launch(
                headless=True,
                args=[
                    '--no-sandbox',
                    '--disable-dev-shm-usage',
                    '--disable-setuid-sandbox',
                    '--disable-gpu',
                    '--disable-software-rasterizer'
                ]
            )
            
            # Create a context with viewport and user agent
            context = browser.new_context(
                viewport={'width': 1280, 'height': 1600},
                user_agent=user_agent
            )
            
            # Create a new page
            page = context.new_page()
            
            # Set a timeout for navigation (30 seconds)
            # A longer timeout helps with slower sites
            page.set_default_timeout(30000)
            
            try:
                # Navigate to the URL
                logger.info(f"Navigating to {url}")
                page.goto(url, wait_until='networkidle')
                
                # Wait for content to load (additional waiting)
                logger.info(f"Waiting for page to stabilize")
                page.wait_for_load_state('networkidle')
                
                # Additional wait for JavaScript rendering
                time.sleep(3)
                
                # Take the screenshot
                logger.info(f"Taking screenshot")
                screenshot_data = page.screenshot(path=filepath, full_page=True)
                
                # Verify the screenshot was saved
                if os.path.exists(filepath) and os.path.getsize(filepath) > 0:
                    logger.info(f"Screenshot successfully saved to {filepath}")
                    return filepath, screenshot_data, None
                else:
                    logger.error(f"Screenshot file missing or empty: {filepath}")
                    return None, None, "Screenshot file missing or empty"
                
            except Exception as e:
                logger.error(f"Error during screenshot capture: {str(e)}")
                return None, None, str(e)
            finally:
                # Always close these resources
                page.close()
                context.close()
                browser.close()
                
    except Exception as e:
        logger.error(f"Error in capture_screenshot_with_playwright: {str(e)}")
        import traceback
        traceback.print_exc()
        return None, None, str(e)

def update_screenshot_in_db(lottery_type, url, filepath):
    """
    Update or create screenshot record in database
    
    Args:
        lottery_type (str): Type of lottery
        url (str): URL of the screenshot
        filepath (str): Path to the screenshot file
        
    Returns:
        bool: Success status
    """
    try:
        # Import DB models
        from models import db, Screenshot
        from main import app
        
        with app.app_context():
            # Check if a screenshot record already exists for this lottery type
            existing_screenshot = Screenshot.query.filter_by(lottery_type=lottery_type).first()
            
            if existing_screenshot:
                # Update existing screenshot
                existing_screenshot.url = url
                existing_screenshot.path = filepath
                existing_screenshot.timestamp = datetime.now()
                db.session.commit()
                logger.info(f"Updated existing screenshot record for {lottery_type}")
                return True
            else:
                # Create new screenshot record
                new_screenshot = Screenshot(
                    lottery_type=lottery_type,
                    url=url,
                    path=filepath,
                    timestamp=datetime.now()
                )
                db.session.add(new_screenshot)
                db.session.commit()
                logger.info(f"Created new screenshot record for {lottery_type}")
                return True
    except Exception as e:
        logger.error(f"Database error: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def capture_all_screenshots():
    """
    Capture screenshots for all lottery types
    
    Returns:
        dict: Results of the capture process
    """
    results = {
        'total': len(LOTTERY_URLS),
        'success': 0,
        'failure': 0,
        'details': []
    }
    
    for item in LOTTERY_URLS:
        url = item['url']
        lottery_type = item['lottery_type']
        
        logger.info(f"Processing {lottery_type}: {url}")
        
        # Try to capture the screenshot
        filepath, data, error = capture_screenshot_with_playwright(url, lottery_type)
        
        if filepath and data:
            # Screenshot captured successfully
            update_success = update_screenshot_in_db(lottery_type, url, filepath)
            
            if update_success:
                results['success'] += 1
                results['details'].append({
                    'lottery_type': lottery_type,
                    'url': url,
                    'filepath': filepath,
                    'status': 'success'
                })
            else:
                results['failure'] += 1
                results['details'].append({
                    'lottery_type': lottery_type,
                    'url': url,
                    'filepath': filepath,
                    'status': 'database_error'
                })
        else:
            # Failed to capture screenshot, create placeholder
            logger.warning(f"Failed to capture screenshot for {lottery_type}. Creating placeholder.")
            placeholder_path, placeholder_data = create_placeholder_image(lottery_type)
            
            if placeholder_path:
                update_success = update_screenshot_in_db(lottery_type, url, placeholder_path)
                
                if update_success:
                    results['failure'] += 1  # Still count as failure since real capture failed
                    results['details'].append({
                        'lottery_type': lottery_type,
                        'url': url,
                        'filepath': placeholder_path,
                        'status': 'placeholder_created',
                        'error': error
                    })
                else:
                    results['failure'] += 1
                    results['details'].append({
                        'lottery_type': lottery_type,
                        'url': url,
                        'filepath': placeholder_path,
                        'status': 'database_error',
                        'error': error
                    })
            else:
                results['failure'] += 1
                results['details'].append({
                    'lottery_type': lottery_type,
                    'url': url,
                    'filepath': None,
                    'status': 'complete_failure',
                    'error': error
                })
    
    return results

def add_routes_to_app():
    """
    Add routes to Flask app for screenshot operations
    """
    from main import app
    from flask import jsonify, redirect, url_for, flash
    from flask_login import login_required
    
    @app.route('/fix-screenshot-capture', methods=['GET', 'POST'])
    @login_required
    def fix_screenshot_capture_route():
        """Route to manually fix screenshot capture"""
        results = capture_all_screenshots()
        
        # Log results
        logger.info(f"Screenshot capture results: {results['success']} successful, {results['failure']} failed")
        
        # Flash message to user
        flash(f"Screenshot capture completed: {results['success']} successful, {results['failure']} failed", "info")
        
        # Redirect back to screenshots page
        return redirect(url_for('export_screenshots'))

if __name__ == "__main__":
    print("Starting screenshot capture...")
    results = capture_all_screenshots()
    
    # Print results summary
    print("\nScreenshot Capture Results:")
    print(f"Total: {results['total']}")
    print(f"Success: {results['success']}")
    print(f"Failure: {results['failure']}")
    
    # Print details for each item
    print("\nDetails:")
    for item in results['details']:
        status = item['status']
        lottery_type = item['lottery_type']
        
        if status == 'success':
            print(f"✓ {lottery_type}: Screenshot captured successfully")
        elif status == 'placeholder_created':
            print(f"⚠ {lottery_type}: Used placeholder image. Error: {item.get('error', 'Unknown')}")
        elif status == 'database_error':
            print(f"✗ {lottery_type}: Database update failed")
        else:
            print(f"✗ {lottery_type}: Complete failure. Error: {item.get('error', 'Unknown')}")