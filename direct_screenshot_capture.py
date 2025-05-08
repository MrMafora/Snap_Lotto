"""
Direct Screenshot Capture - Reliable URL Screenshot Tool

This module provides a direct and reliable way to capture screenshots from lottery URLs.
It uses a combination of methods to ensure success even in challenging environments:

1. First attempts with requests to verify URL availability
2. Uses a headless Chrome approach for taking the actual screenshot
3. Directly updates the database with the file paths
"""
import os
import sys
import time
import logging
import traceback
from datetime import datetime
import requests
from PIL import Image, ImageDraw, ImageFont
import io

# Configure logging
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Ensure the screenshot directory exists
SCREENSHOT_DIR = 'screenshots'
os.makedirs(SCREENSHOT_DIR, exist_ok=True)

# Lottery URLs to capture
LOTTERY_URLS = [
    {'url': 'https://www.nationallottery.co.za/results/lotto', 'lottery_type': 'Lotto'},
    {'url': 'https://www.nationallottery.co.za/results/lotto-plus-1-results', 'lottery_type': 'Lotto Plus 1'},
    {'url': 'https://www.nationallottery.co.za/results/lotto-plus-2-results', 'lottery_type': 'Lotto Plus 2'},
    {'url': 'https://www.nationallottery.co.za/results/powerball', 'lottery_type': 'Powerball'},
    {'url': 'https://www.nationallottery.co.za/results/powerball-plus', 'lottery_type': 'Powerball Plus'},
    {'url': 'https://www.nationallottery.co.za/results/daily-lotto', 'lottery_type': 'Daily Lotto'}
]

def capture_screenshot(url, lottery_type):
    """
    Capture a screenshot of the URL
    
    Args:
        url (str): URL to capture
        lottery_type (str): Type of lottery
        
    Returns:
        tuple: (success, filepath) where success is a boolean and filepath is the path to the screenshot file
    """
    logger.info(f"Capturing screenshot for {lottery_type} from {url}")
    
    # Create a timestamp for the filename
    timestamp = datetime.now()
    timestamp_str = timestamp.strftime("%Y%m%d_%H%M%S")
    clean_lottery_type = lottery_type.replace(' ', '_').lower()
    filename = f"{timestamp_str}_{clean_lottery_type}.png"
    filepath = os.path.join(SCREENSHOT_DIR, filename)
    
    # First check if the URL is reachable
    try:
        logger.info(f"Checking if URL is reachable: {url}")
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        response = requests.head(url, headers=headers, timeout=10)
        if response.status_code >= 400:
            logger.error(f"URL not reachable. Status code: {response.status_code}")
            return False, None
    except Exception as e:
        logger.error(f"Error checking URL: {str(e)}")
        return False, None
    
    # Use a simple method to capture the screenshot
    try:
        # Try with selenium first - it's more reliable in Replit
        success, filepath = capture_with_selenium(url, filepath, lottery_type)
        if success:
            logger.info(f"Successfully captured screenshot with Selenium: {filepath}")
            return True, filepath
        
        # If selenium fails, try with wkhtmltoimage
        logger.info("Selenium failed, trying with wkhtmltoimage")
        success, filepath = capture_with_wkhtmltoimage(url, filepath, lottery_type)
        if success:
            logger.info(f"Successfully captured screenshot with wkhtmltoimage: {filepath}")
            return True, filepath
            
        # If all methods fail, use requests to at least get some content
        logger.info("All screenshot methods failed, using requests to get content")
        success, filepath = capture_with_requests(url, filepath, lottery_type)
        if success:
            logger.info(f"Successfully captured content with requests: {filepath}")
            return True, filepath
        
        logger.error("All screenshot capture methods failed")
        return False, None
        
    except Exception as e:
        logger.error(f"Error capturing screenshot: {str(e)}")
        traceback.print_exc()
        return False, None

def capture_with_selenium(url, filepath, lottery_type):
    """
    Capture screenshot using Selenium
    
    Args:
        url (str): URL to capture
        filepath (str): Path to save the screenshot
        lottery_type (str): Type of lottery
        
    Returns:
        tuple: (success, filepath) where success is a boolean and filepath is the path to the screenshot file
    """
    try:
        from selenium import webdriver
        from selenium.webdriver.chrome.options import Options
        from selenium.webdriver.chrome.service import Service
        
        logger.info(f"Setting up Chrome for {lottery_type}")
        
        # Set up Chrome options
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--window-size=1280,1024")
        chrome_options.add_argument("--disable-blink-features=AutomationControlled")
        chrome_options.add_argument(f"user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36")
        
        # Create the Chrome driver
        driver = webdriver.Chrome(options=chrome_options)
        
        try:
            # Navigate to the URL
            logger.info(f"Navigating to {url}")
            driver.get(url)
            
            # Wait for the page to load
            logger.info("Waiting for page to load")
            time.sleep(5)  # Simple delay to let content render
            
            # Take the screenshot
            logger.info(f"Taking screenshot and saving to {filepath}")
            driver.save_screenshot(filepath)
            
            # Check if the file was created
            if os.path.exists(filepath) and os.path.getsize(filepath) > 1000:  # Ensure it's not an empty file
                logger.info(f"Screenshot saved successfully: {filepath}")
                return True, filepath
            else:
                logger.error(f"Screenshot file is missing or too small: {filepath}")
                return False, None
                
        finally:
            # Clean up
            driver.quit()
            
    except Exception as e:
        logger.error(f"Error with Selenium screenshot: {str(e)}")
        traceback.print_exc()
        return False, None

def capture_with_wkhtmltoimage(url, filepath, lottery_type):
    """
    Capture screenshot using wkhtmltoimage command line tool
    
    Args:
        url (str): URL to capture
        filepath (str): Path to save the screenshot
        lottery_type (str): Type of lottery
        
    Returns:
        tuple: (success, filepath) where success is a boolean and filepath is the path to the screenshot file
    """
    try:
        import subprocess
        
        logger.info(f"Capturing with wkhtmltoimage: {url}")
        
        # Command to run wkhtmltoimage
        cmd = [
            'wkhtmltoimage',
            '--width', '1280',
            '--height', '1024',
            '--quality', '90',
            '--javascript-delay', '5000',  # 5 second delay for JavaScript
            '--no-stop-slow-scripts',
            '--user-agent', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            url,
            filepath
        ]
        
        logger.info(f"Running command: {' '.join(cmd)}")
        
        # Run the command
        process = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        
        # Check if the command was successful
        if process.returncode == 0 and os.path.exists(filepath) and os.path.getsize(filepath) > 1000:
            logger.info(f"wkhtmltoimage successful: {filepath}")
            return True, filepath
        else:
            logger.error(f"wkhtmltoimage failed. Return code: {process.returncode}")
            logger.error(f"Error output: {process.stderr}")
            return False, None
            
    except Exception as e:
        logger.error(f"Error with wkhtmltoimage: {str(e)}")
        traceback.print_exc()
        return False, None

def capture_with_requests(url, filepath, lottery_type):
    """
    Capture content using requests and save as PNG
    
    Args:
        url (str): URL to capture
        filepath (str): Path to save the content
        lottery_type (str): Type of lottery
        
    Returns:
        tuple: (success, filepath) where success is a boolean and filepath is the path to the content file
    """
    try:
        logger.info(f"Capturing with requests: {url}")
        
        # Set up headers
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        # Get the content
        response = requests.get(url, headers=headers, timeout=30)
        
        # Check if the request was successful
        if response.status_code == 200:
            # Save the content to a text file to ensure we have something
            text_filepath = filepath.replace('.png', '.txt')
            with open(text_filepath, 'wb') as f:
                f.write(response.content)
                
            logger.info(f"Content saved as text: {text_filepath}")
            
            # Create a simple image with the URL, date and lottery type
            width, height = 1280, 800
            image = Image.new('RGB', (width, height), (245, 245, 245))
            draw = ImageDraw.Draw(image)
            
            # Try to load a font, fall back to default if not available
            try:
                font = ImageFont.truetype("arial.ttf", 24)
                small_font = ImageFont.truetype("arial.ttf", 18)
            except IOError:
                font = ImageFont.load_default()
                small_font = ImageFont.load_default()
            
            # Draw a header rectangle
            draw.rectangle([(0, 0), (width, 80)], fill=(0, 87, 183))  # Blue header
            
            # Draw title
            title = f"{lottery_type} Data Downloaded"
            draw.text((20, 20), title, fill=(255, 255, 255), font=font)  # White text
            
            # Draw timestamp and URL
            timestamp_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            draw.text((20, 100), f"Downloaded on: {timestamp_str}", fill=(0, 0, 0), font=small_font)
            draw.text((20, 130), f"From URL: {url}", fill=(0, 0, 0), font=small_font)
            draw.text((20, 160), f"Status code: {response.status_code}", fill=(0, 0, 0), font=small_font)
            
            # Draw a message about the content
            draw.text((20, 200), "The actual screenshot couldn't be captured.", fill=(0, 0, 0), font=small_font)
            draw.text((20, 230), "However, the HTML content was successfully downloaded.", fill=(0, 0, 0), font=small_font)
            draw.text((20, 260), f"The content has been saved to: {os.path.basename(text_filepath)}", fill=(0, 0, 0), font=small_font)
            
            # Save the image
            image.save(filepath)
            logger.info(f"Created content info image: {filepath}")
            
            return True, filepath
        else:
            logger.error(f"Request failed with status code: {response.status_code}")
            return False, None
            
    except Exception as e:
        logger.error(f"Error with requests capture: {str(e)}")
        traceback.print_exc()
        return False, None

def update_database_record(lottery_type, url, filepath):
    """
    Update the database record for this screenshot
    
    Args:
        lottery_type (str): Type of lottery
        url (str): URL that was captured
        filepath (str): Path to the screenshot file
        
    Returns:
        bool: Success status
    """
    try:
        from models import db, Screenshot
        from main import app
        
        with app.app_context():
            # Find existing record or create new one
            screenshot = Screenshot.query.filter_by(lottery_type=lottery_type).first()
            
            if screenshot:
                # Update existing record
                old_path = screenshot.path
                screenshot.path = filepath
                screenshot.url = url
                screenshot.timestamp = datetime.now()
                
                # Delete the old file if it exists and is different
                if old_path and old_path != filepath and os.path.exists(old_path):
                    try:
                        os.remove(old_path)
                        logger.info(f"Deleted old screenshot: {old_path}")
                    except Exception as e:
                        logger.warning(f"Failed to delete old screenshot: {str(e)}")
            else:
                # Create new record
                screenshot = Screenshot(
                    lottery_type=lottery_type,
                    url=url,
                    path=filepath,
                    timestamp=datetime.now()
                )
                db.session.add(screenshot)
                
            # Commit changes
            db.session.commit()
            logger.info(f"Updated database record for {lottery_type}")
            return True
            
    except Exception as e:
        logger.error(f"Error updating database record: {str(e)}")
        traceback.print_exc()
        return False

def capture_all_screenshots():
    """
    Capture screenshots for all lottery types
    
    Returns:
        dict: Results of all screenshots
    """
    results = {}
    
    for lottery_info in LOTTERY_URLS:
        url = lottery_info['url']
        lottery_type = lottery_info['lottery_type']
        
        try:
            logger.info(f"Processing {lottery_type}")
            
            # Capture the screenshot
            success, filepath = capture_screenshot(url, lottery_type)
            
            if success and filepath:
                # Update the database
                db_success = update_database_record(lottery_type, url, filepath)
                
                results[lottery_type] = {
                    'status': 'success' if db_success else 'database_error',
                    'path': filepath
                }
                
                logger.info(f"Successfully processed {lottery_type}")
            else:
                results[lottery_type] = {
                    'status': 'failed',
                    'message': f"Failed to capture screenshot for {lottery_type}"
                }
                
                logger.error(f"Failed to capture screenshot for {lottery_type}")
        
        except Exception as e:
            logger.error(f"Error processing {lottery_type}: {str(e)}")
            traceback.print_exc()
            
            results[lottery_type] = {
                'status': 'error',
                'message': str(e)
            }
    
    return results

def capture_screenshot_by_id(screenshot_id):
    """
    Capture a screenshot by its database ID
    
    Args:
        screenshot_id (int): Database ID of the screenshot
        
    Returns:
        dict: Result of the operation
    """
    try:
        from models import db, Screenshot
        from main import app
        
        with app.app_context():
            # Find the screenshot
            screenshot = Screenshot.query.get(screenshot_id)
            
            if not screenshot:
                logger.error(f"Screenshot with ID {screenshot_id} not found")
                return {
                    'status': 'error',
                    'message': f"Screenshot with ID {screenshot_id} not found"
                }
            
            # Capture the screenshot
            success, filepath = capture_screenshot(screenshot.url, screenshot.lottery_type)
            
            if success and filepath:
                # Update the database
                old_path = screenshot.path
                screenshot.path = filepath
                screenshot.timestamp = datetime.now()
                db.session.commit()
                
                # Delete the old file if it exists and is different
                if old_path and old_path != filepath and os.path.exists(old_path):
                    try:
                        os.remove(old_path)
                        logger.info(f"Deleted old screenshot: {old_path}")
                    except Exception as e:
                        logger.warning(f"Failed to delete old screenshot: {str(e)}")
                
                return {
                    'status': 'success',
                    'path': filepath,
                    'lottery_type': screenshot.lottery_type
                }
            else:
                return {
                    'status': 'failed',
                    'message': f"Failed to capture screenshot for {screenshot.lottery_type}"
                }
    
    except Exception as e:
        logger.error(f"Error capturing screenshot by ID {screenshot_id}: {str(e)}")
        traceback.print_exc()
        
        return {
            'status': 'error',
            'message': str(e)
        }

if __name__ == "__main__":
    # If run as a script, capture all screenshots
    results = capture_all_screenshots()
    
    # Print results
    print(f"\nResults:")
    for lottery_type, result in results.items():
        if result.get('status') == 'success':
            print(f"✅ {lottery_type}: {result.get('path')}")
        else:
            print(f"❌ {lottery_type}: {result.get('message')}")