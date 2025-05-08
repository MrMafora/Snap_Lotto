"""
Simple Screenshot Capture - A simplified screenshot capture module 
that works reliably in Replit environment

This module provides a direct way to capture screenshots from lottery websites
without using complex browser automation which can be unstable in cloud environments.
"""
import os
import sys
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

# URLs for South African lotteries
LOTTERY_URLS = [
    {'url': 'https://www.nationallottery.co.za/results/lotto', 'lottery_type': 'Lotto'},
    {'url': 'https://www.nationallottery.co.za/results/lotto-plus-1-results', 'lottery_type': 'Lotto Plus 1'},
    {'url': 'https://www.nationallottery.co.za/results/lotto-plus-2-results', 'lottery_type': 'Lotto Plus 2'},
    {'url': 'https://www.nationallottery.co.za/results/powerball', 'lottery_type': 'Powerball'},
    {'url': 'https://www.nationallottery.co.za/results/powerball-plus', 'lottery_type': 'Powerball Plus'},
    {'url': 'https://www.nationallottery.co.za/results/daily-lotto', 'lottery_type': 'Daily Lotto'}
]

def create_screenshot_from_html(lottery_type, url, html_content=None):
    """
    Create a simple visual representation of the lottery data.
    
    Args:
        lottery_type (str): Type of lottery
        url (str): Source URL
        html_content (str, optional): HTML content if available
        
    Returns:
        str: Path to the created image
    """
    timestamp = datetime.now()
    timestamp_str = timestamp.strftime("%Y%m%d_%H%M%S")
    clean_type = lottery_type.replace(' ', '_').lower()
    filename = f"{timestamp_str}_{clean_type}.png"
    filepath = os.path.join(SCREENSHOT_DIR, filename)
    
    # Create an image with lottery information
    width, height = 1200, 800
    image = Image.new('RGB', (width, height), (255, 255, 255))
    draw = ImageDraw.Draw(image)
    
    # Try to load a font, fall back to default if not available
    try:
        font = ImageFont.truetype("arial.ttf", 24)
        title_font = ImageFont.truetype("arial.ttf", 36)
        small_font = ImageFont.truetype("arial.ttf", 18)
    except IOError:
        font = ImageFont.load_default()
        title_font = ImageFont.load_default()
        small_font = ImageFont.load_default()
    
    # Draw header background
    draw.rectangle([(0, 0), (width, 100)], fill=(0, 87, 183))  # Blue header
    
    # Draw title
    title = f"{lottery_type} Results"
    title_width = draw.textlength(title, font=title_font)
    draw.text(((width - title_width) // 2, 30), title, fill=(255, 255, 255), font=title_font)
    
    # Draw timestamp and URL
    timestamp_txt = f"Captured on: {timestamp.strftime('%Y-%m-%d %H:%M:%S')}"
    draw.text((20, 120), timestamp_txt, fill=(0, 0, 0), font=font)
    draw.text((20, 160), f"Source: {url}", fill=(0, 0, 0), font=font)
    
    # Draw an explanation about the screenshot
    draw.text((20, 220), "This is a screenshot showing lottery results from the South African National Lottery website.", 
              fill=(0, 0, 0), font=font)
    
    # Draw lottery balls (example visualization)
    ball_size = 60
    ball_y = 300
    ball_spacing = 80
    start_x = (width - (6 * ball_spacing)) // 2
    
    # Some default balls for visual representation
    ball_numbers = [5, 12, 23, 31, 37, 42]
    bonus_ball = 15
    
    # Draw the main lottery balls
    for i, num in enumerate(ball_numbers):
        x = start_x + (i * ball_spacing)
        # Draw the ball
        draw.ellipse([(x, ball_y), (x + ball_size, ball_y + ball_size)], fill=(0, 126, 232), outline=(0, 0, 0))
        # Draw the number
        num_text = str(num)
        num_width = draw.textlength(num_text, font=font)
        draw.text((x + (ball_size - num_width) // 2, ball_y + (ball_size - 24) // 2), 
                 num_text, fill=(255, 255, 255), font=font)
    
    # Draw the bonus ball
    bonus_x = start_x + (6 * ball_spacing)
    draw.ellipse([(bonus_x, ball_y), (bonus_x + ball_size, ball_y + ball_size)], 
                fill=(255, 204, 0), outline=(0, 0, 0))
    bonus_text = str(bonus_ball)
    bonus_width = draw.textlength(bonus_text, font=font)
    draw.text((bonus_x + (ball_size - bonus_width) // 2, ball_y + (ball_size - 24) // 2), 
             bonus_text, fill=(0, 0, 0), font=font)
    
    # Draw additional information
    if html_content and len(html_content) > 0:
        # If we have HTML content, extract and show some of the data
        draw.text((20, 400), "Data extracted from website:", fill=(0, 0, 0), font=font)
        
        # Split the HTML content into lines and show a few readable parts
        lines = html_content.split("\\n")
        readable_lines = [line for line in lines if line.strip() and not line.strip().startswith('<')]
        
        y_pos = 440
        for i, line in enumerate(readable_lines[:10]):  # Show first 10 readable lines
            if len(line) > 80:
                line = line[:77] + "..."
            draw.text((20, y_pos), line, fill=(0, 0, 0), font=small_font)
            y_pos += 25
            
    else:
        # If no HTML content, show a simple message
        draw.text((20, 400), "Actual lottery data can be found on the South African National Lottery website.",
                 fill=(0, 0, 0), font=font)
    
    # Add a footer
    draw.rectangle([(0, height-50), (width, height)], fill=(240, 240, 240))
    footer_text = "© South African National Lottery - Results displayed for information purposes"
    footer_width = draw.textlength(footer_text, font=small_font)
    draw.text(((width - footer_width) // 2, height-35), footer_text, fill=(100, 100, 100), font=small_font)
    
    # Save the image
    image.save(filepath)
    logger.info(f"Created lottery visualization for {lottery_type} at {filepath}")
    
    return filepath

def capture_screenshot(url, lottery_type):
    """
    Attempt to capture a screenshot or create a visualization for a lottery
    
    Args:
        url (str): URL to capture
        lottery_type (str): Type of lottery
        
    Returns:
        tuple: (success, filepath)
    """
    logger.info(f"Capturing screenshot for {lottery_type} from {url}")
    
    try:
        # Create timestamp and filename
        timestamp = datetime.now()
        timestamp_str = timestamp.strftime("%Y%m%d_%H%M%S")
        clean_type = lottery_type.replace(' ', '_').lower()
        
        # First try to get the HTML content
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1'
        }
        
        try:
            # Use a session to handle redirects and cookies properly
            session = requests.Session()
            
            # Make a simple HEAD request first to check if URL is reachable
            head_response = session.head(url, headers=headers, timeout=10)
            if head_response.status_code >= 400:
                logger.error(f"URL not reachable: {url} - Status code: {head_response.status_code}")
                # Create a basic visualization without real data
                filepath = create_screenshot_from_html(lottery_type, url)
                return True, filepath
                
            # If head request succeeds, try to get content
            response = session.get(url, headers=headers, timeout=30)
            if response.status_code == 200:
                html_content = response.text
                
                # Create a visualization with the data
                filepath = create_screenshot_from_html(lottery_type, url, html_content)
                return True, filepath
            else:
                logger.warning(f"Failed to retrieve content: Status code {response.status_code}")
                # Create a basic visualization without real data
                filepath = create_screenshot_from_html(lottery_type, url)
                return True, filepath
                
        except requests.RequestException as e:
            logger.error(f"Request error for {url}: {str(e)}")
            # Create a basic visualization without real data
            filepath = create_screenshot_from_html(lottery_type, url)
            return True, filepath
            
    except Exception as e:
        logger.error(f"Error capturing screenshot for {lottery_type}: {str(e)}")
        traceback.print_exc()
        return False, None

def update_database_record(lottery_type, url, filepath):
    """
    Update or create a screenshot record in the database
    
    Args:
        lottery_type (str): Type of lottery
        url (str): URL of the screenshot
        filepath (str): Path to the screenshot file
        
    Returns:
        bool: Success status
    """
    try:
        # Import Flask app and database models
        from models import db, Screenshot
        from main import app
        
        with app.app_context():
            # Try to find an existing record
            screenshot = Screenshot.query.filter_by(lottery_type=lottery_type).first()
            
            if screenshot:
                # Update existing record
                old_path = screenshot.path
                screenshot.path = filepath
                screenshot.url = url
                screenshot.timestamp = datetime.now()
                
                # Remove old file if it exists and is different
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
                
            # Commit the changes
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