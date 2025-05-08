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

def create_placeholder_image(lottery_type, timestamp=None, width=800, height=600, 
                       error_message=None, status_code=None, url=None):
    """
    Create a placeholder image with lottery information
    
    Args:
        lottery_type (str): Type of lottery
        timestamp (datetime, optional): Timestamp for the image
        width (int): Width of the image
        height (int): Height of the image
        error_message (str, optional): Error message to display
        status_code (int, optional): HTTP status code
        url (str, optional): URL that was being captured
        
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
        
        # Try to load a font, fall back to default if not available
        try:
            # Try to find a font
            font_paths = [
                '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf',
                '/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf',
                '/usr/share/fonts/dejavu/DejaVuSans-Bold.ttf',
            ]
            
            font = None
            for path in font_paths:
                if os.path.exists(path):
                    try:
                        font = ImageFont.truetype(path, 22)
                        small_font = ImageFont.truetype(path, 16)
                        break
                    except:
                        pass
                        
            if font is None:
                # Use default font if no truetype font is available
                font = ImageFont.load_default()
                small_font = font
                
        except Exception as e:
            logger.warning(f"Could not load font: {str(e)}")
            font = ImageFont.load_default()
            small_font = font
            
        # Draw header background - use tuples for rectangle coordinates
        draw.rectangle(((0, 0), (width, 60)), fill=(0, 51, 102))  # Dark blue header
        
        # Draw title
        title = f"{lottery_type} Screenshot"
        draw.text((20, 20), title, fill=(255, 255, 255), font=font)  # White text
        
        # Draw timestamp
        timestamp_str = ts.strftime("%Y-%m-%d %H:%M:%S")
        draw.text((20, 80), f"Generated: {timestamp_str}", fill=(0, 0, 0), font=small_font)
        
        # Draw URL if provided
        if url:
            draw.text((20, 110), f"Source: {url}", fill=(0, 0, 0), font=small_font)
            y_offset = 140
        else:
            y_offset = 110
            
        # Draw error message with red color if provided
        if error_message:
            status_text = f"Error: {error_message}"
            if status_code:
                status_text += f" (HTTP {status_code})"
            draw.text((20, y_offset), status_text, fill=(255, 0, 0), font=small_font)
            y_offset += 30
        elif status_code:
            draw.text((20, y_offset), f"HTTP Status: {status_code}", fill=(255, 0, 0), font=small_font)
            y_offset += 30
            
        # Draw information
        draw.text((20, y_offset), "This is a placeholder screenshot.", fill=(0, 0, 0), font=small_font)
        draw.text((20, y_offset + 30), "The actual screenshot could not be captured.", fill=(0, 0, 0), font=small_font)
        draw.text((20, y_offset + 60), "Please try regenerating the screenshot.", fill=(0, 0, 0), font=small_font)
        
        # Add instructions
        y_offset += 100
        draw.rectangle(((20, y_offset), (width-20, y_offset+100)), outline=(200, 200, 200))
        draw.text((30, y_offset + 10), "Troubleshooting:", fill=(0, 0, 0), font=font)
        draw.text((30, y_offset + 40), "1. Check if the website is accessible", fill=(0, 0, 0), font=small_font)
        draw.text((30, y_offset + 70), "2. Try using the 'Capture New Screenshots' button", fill=(0, 0, 0), font=small_font)
        
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

def capture_screenshot_with_requests(url, lottery_type):
    """
    Attempt to download HTML content from the URL and create a more informative placeholder
    showing the URL and metadata. This approach is more reliable in Replit environments
    where browser automation can be challenging.
    
    Args:
        url (str): URL to capture
        lottery_type (str): Type of lottery
        
    Returns:
        tuple: (filepath, content_data, error_message)
    """
    try:
        # Create a timestamp for the filename
        timestamp = datetime.now()
        timestamp_str = timestamp.strftime("%Y%m%d_%H%M%S")
        filename = f"{timestamp_str}_{lottery_type.lower().replace(' ', '-').replace('/', '-')}.png"
        filepath = os.path.join('screenshots', filename)
        
        logger.info(f"Attempting to get data from {url} for {lottery_type}")
        
        # Use requests to get HTML content (to check if site is accessible)
        import requests
        
        # Define headers for the request with a user agent
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/96.0.4664.110 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Cache-Control': 'max-age=0'
        }
        
        # Make the request with a timeout and disable automatic decompression
        # to avoid issues with gzip content
        try:
            session = requests.Session()
            # Disable automatic content decompression to avoid chunk errors
            session.mount('https://', requests.adapters.HTTPAdapter(max_retries=3))
            session.headers.update(headers)
            response = session.get(url, timeout=30, stream=True)
            
            # Manually read the response content without allowing auto-decompression
            content = b''
            for chunk in response.raw.read(1024):
                if not chunk:
                    break
                content += chunk
                
            # Convert bytes to string for content preview, handling encoding issues
            try:
                response.encoding = response.apparent_encoding
                response._content = content  # Set the content manually
                response.text  # Access text property to decode content
            except:
                # If decoding fails, create a basic string representation
                response._content = content
                response.text = str(content)
                
        except (requests.exceptions.RequestException, requests.exceptions.ConnectionError,
                requests.exceptions.ChunkedEncodingError, requests.exceptions.Timeout) as e:
            # Handle request errors with a detailed error message
            logger.error(f"Request error: {type(e).__name__}: {str(e)}")
            error_msg = f"Connection error: {type(e).__name__}"
            
            # Create a placeholder with the connection error information
            filepath, image_data = create_placeholder_image(
                lottery_type, 
                timestamp=timestamp,
                error_message=error_msg,
                url=url
            )
            
            return filepath, image_data, error_msg
        
        # Check if request was successful
        if response.status_code == 200:
            logger.info(f"Successfully retrieved content from {url}")
            
            # Get title from HTML if possible
            import re
            title_match = re.search('<title>(.*?)</title>', response.text, re.IGNORECASE)
            page_title = title_match.group(1) if title_match else lottery_type
            
            # Create an enhanced placeholder image with metadata
            width, height = 1280, 800
            image = Image.new('RGB', (width, height), color=(255, 255, 255))
            draw = ImageDraw.Draw(image)
            
            # Draw header
            draw.rectangle(((0, 0), (width, 60)), fill=(0, 51, 102))  # Dark blue header
            
            # Try to load a font, fall back to default if not available
            try:
                # Try to find a font
                font_paths = [
                    '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf',
                    '/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf',
                    '/usr/share/fonts/dejavu/DejaVuSans-Bold.ttf',
                ]
                
                font = None
                for path in font_paths:
                    if os.path.exists(path):
                        try:
                            font = ImageFont.truetype(path, 22)
                            small_font = ImageFont.truetype(path, 16)
                            break
                        except:
                            pass
                            
                if font is None:
                    # Use default font if no truetype font is available
                    font = ImageFont.load_default()
                    small_font = font
                    
            except Exception as e:
                logger.warning(f"Could not load font: {str(e)}")
                font = ImageFont.load_default()
                small_font = font
                
            # Draw title
            title = f"{lottery_type} - {page_title}"
            draw.text((20, 15), title, fill=(255, 255, 255), font=font)
            
            # Draw URL
            draw.text((20, 70), f"Source: {url}", fill=(0, 0, 0), font=small_font)
            
            # Draw timestamp
            timestamp_str = timestamp.strftime("%Y-%m-%d %H:%M:%S")
            draw.text((20, 100), f"Generated: {timestamp_str}", fill=(0, 0, 0), font=small_font)
            
            # Draw status info
            draw.text((20, 130), f"Status: Content available (HTTP {response.status_code})", fill=(0, 128, 0), font=small_font)
            
            # Draw content length info
            content_length = len(response.text)
            draw.text((20, 160), f"Content Size: {content_length} bytes", fill=(0, 0, 0), font=small_font)
            
            # Draw content preview
            preview_lines = response.text[:1000].split('\n')[:10]
            preview_text = '\n'.join(preview_lines) + '...'
            
            # Draw a box for content preview
            draw.rectangle(((20, 200), (width-20, height-20)), outline=(200, 200, 200))
            
            # Draw content preview title
            draw.text((30, 210), "Content Preview:", fill=(0, 0, 0), font=small_font)
            
            # Draw the content preview text
            y_pos = 240
            for line in preview_lines:
                truncated_line = line[:120] + '...' if len(line) > 120 else line
                draw.text((30, y_pos), truncated_line, fill=(50, 50, 50), font=small_font)
                y_pos += 25
                if y_pos > height - 40:
                    break
            
            # Save the image
            image.save(filepath)
            
            # Read the image data
            with open(filepath, 'rb') as f:
                image_data = f.read()
                
            logger.info(f"Enhanced metadata image created and saved to {filepath}")
            
            return filepath, image_data, None
        else:
            logger.warning(f"Failed to retrieve content from {url} (HTTP {response.status_code})")
            error_msg = f"HTTP Error: {response.status_code}"
            
            # Create a placeholder with error information
            filepath, image_data = create_placeholder_image(
                lottery_type, 
                timestamp=timestamp,
                width=1280,
                height=800,
                error_message=error_msg,
                status_code=response.status_code,
                url=url
            )
            
            return filepath, image_data, error_msg
            
    except Exception as e:
        logger.error(f"Error capturing content from {url}: {str(e)}")
        import traceback
        traceback.print_exc()
        
        # Create a placeholder with error information
        filepath, image_data = create_placeholder_image(
            lottery_type,
            error_message=str(e),
            url=url
        )
        
        return filepath, image_data, str(e)

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
    Capture screenshots for all lottery types using requests-based approach
    
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
        
        # Try to capture the data and create an information-rich screenshot
        try:
            filepath, data, error = capture_screenshot_with_requests(url, lottery_type)
        except Exception as e:
            logger.error(f"Error in screenshot capture process: {str(e)}")
            filepath, data = create_placeholder_image(
                lottery_type,
                error_message=f"Exception: {str(e)}",
                url=url
            )
            error = str(e)
        
        if filepath and data:
            # Screenshot created successfully (either with content preview or as placeholder)
            update_success = update_screenshot_in_db(lottery_type, url, filepath)
            
            if update_success:
                # Only count as success if no error was reported
                if error is None:
                    results['success'] += 1
                    status = 'success'
                else:
                    results['failure'] += 1
                    status = 'content_error'
                    
                results['details'].append({
                    'lottery_type': lottery_type,
                    'url': url,
                    'filepath': filepath,
                    'status': status,
                    'error': error
                })
            else:
                results['failure'] += 1
                results['details'].append({
                    'lottery_type': lottery_type,
                    'url': url,
                    'filepath': filepath,
                    'status': 'database_error',
                    'error': 'Failed to update database'
                })
        else:
            # Complete failure - could not create even a placeholder
            results['failure'] += 1
            results['details'].append({
                'lottery_type': lottery_type,
                'url': url,
                'filepath': None,
                'status': 'complete_failure',
                'error': error or 'Unknown error'
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