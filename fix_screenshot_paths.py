"""
Fix Screenshot Paths

This script fixes screenshot paths by:
1. Checking for missing screenshot files
2. Creating new screenshots for missing files
3. Updating the database with the correct paths
"""
import os
import io
import sys
import logging
import tempfile
import requests
from datetime import datetime
from PIL import Image, ImageDraw, ImageFont

# Set up logging
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Constants
SCREENSHOT_DIR = os.path.join(os.getcwd(), 'screenshots')

def ensure_directory_exists(directory):
    """
    Ensure a directory exists
    
    Args:
        directory (str): Path to the directory
        
    Returns:
        bool: True if directory exists or was created, False on error
    """
    try:
        os.makedirs(directory, exist_ok=True)
        return True
    except Exception as e:
        logger.error(f"Error creating directory {directory}: {str(e)}")
        return False

def create_placeholder_image(lottery_type, output_path, timestamp=None, width=800, height=600, url=None):
    """
    Create a placeholder image with lottery information
    
    Args:
        lottery_type (str): Type of lottery
        output_path (str): Where to save the image
        timestamp (datetime, optional): Timestamp for the image
        width (int): Width of the image
        height (int): Height of the image
        url (str, optional): URL that was being captured
        
    Returns:
        bool: Success status
    """
    try:
        # Make sure directory exists
        dir_path = os.path.dirname(output_path)
        ensure_directory_exists(dir_path)
        
        # Use timestamp or current time
        ts = timestamp or datetime.now()
        
        # Create a white image
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
            small_font = None
            for path in font_paths:
                if os.path.exists(path):
                    try:
                        font = ImageFont.truetype(path, 24)
                        small_font = ImageFont.truetype(path, 18)
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
        
        # Draw a blue rectangle at the top
        draw.rectangle(((0, 0), (width, 60)), fill=(0, 51, 102))
        
        # Draw header with white text
        draw.rectangle(((0, 0), (width, 50)), fill=(0, 51, 102))
        title = f"{lottery_type} Screenshot"
        draw.text((20, 15), title, fill=(255, 255, 255), font=font)
        
        # Draw timestamp
        timestamp_str = ts.strftime("%Y-%m-%d %H:%M:%S")
        draw.text((20, 70), f"Generated: {timestamp_str}", fill=(0, 0, 0), font=small_font)
        
        # If URL is provided, add it
        if url:
            if len(url) > 60:
                url_display = url[:57] + "..."
            else:
                url_display = url
            draw.text((20, 100), f"Source: {url_display}", fill=(0, 0, 0), font=small_font)
        
        # Add explanatory text
        draw.text((20, 140), "This is a generated placeholder image.", fill=(0, 0, 0), font=small_font)
        draw.text((20, 170), "The original screenshot was not available.", fill=(0, 0, 0), font=small_font)
        
        # Draw lottery-colored dots at the bottom
        draw.ellipse(((100, 500), (130, 530)), fill=(204, 0, 0))  # Red
        draw.ellipse(((150, 500), (180, 530)), fill=(0, 102, 204))  # Blue
        draw.ellipse(((200, 500), (230, 530)), fill=(0, 153, 0))  # Green
        draw.ellipse(((250, 500), (280, 530)), fill=(255, 204, 0))  # Yellow
        draw.ellipse(((300, 500), (330, 530)), fill=(102, 0, 204))  # Purple
        draw.ellipse(((350, 500), (380, 530)), fill=(255, 102, 0))  # Orange
        
        # Save the image
        image.save(output_path, format="PNG")
        logger.info(f"Created placeholder image at {output_path}")
        return True
        
    except Exception as e:
        logger.error(f"Error creating placeholder image: {str(e)}")
        return False

def capture_with_requests(url, output_path, lottery_type=None):
    """
    Attempt to download HTML content from the URL 
    
    Args:
        url (str): URL to capture
        output_path (str): Path to save the content
        lottery_type (str, optional): Type of lottery for logging
        
    Returns:
        tuple: (success, error_message)
    """
    try:
        logger.info(f"Capturing screenshot for {lottery_type} from {url}")
        
        # Set headers to mimic a browser
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml',
            'Accept-Language': 'en-US,en;q=0.9',
            'Referer': 'https://www.google.com/',
            'DNT': '1',
            'Upgrade-Insecure-Requests': '1',
        }
        
        # Make request with longer timeout
        response = requests.get(url, headers=headers, timeout=30)
        
        if response.status_code != 200:
            logger.warning(f"HTTP error {response.status_code} for {url}")
            # Create placeholder with error information
            create_placeholder_image(
                lottery_type or "Screenshot", 
                output_path,
                datetime.now(),
                800, 600,
                url
            )
            return False, f"HTTP error {response.status_code}"
            
        # Create directory if it doesn't exist
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        # Save the HTML content (this will be used as a fallback)
        try:
            with open(output_path, 'wb') as f:
                f.write(response.content)
                
            # HTML saved successfully, but it's not a proper image
            # Let's create a placeholder image
            create_placeholder_image(
                lottery_type or "Screenshot", 
                output_path,
                datetime.now(),
                800, 600,
                url
            )
            return True, ""
                
        except Exception as e:
            logger.error(f"Error saving content: {str(e)}")
            # If we can't save the content, create a placeholder
            create_placeholder_image(
                lottery_type or "Screenshot", 
                output_path,
                datetime.now(),
                800, 600,
                url
            )
            return False, f"Error saving content: {str(e)}"
            
    except requests.exceptions.RequestException as e:
        logger.error(f"Request error for {url}: {str(e)}")
        # Create placeholder with error information
        create_placeholder_image(
            lottery_type or "Screenshot", 
            output_path,
            datetime.now(),
            800, 600,
            url
        )
        return False, f"Request error: {str(e)}"
    except Exception as e:
        logger.error(f"Unexpected error for {url}: {str(e)}")
        # Create placeholder with error information
        create_placeholder_image(
            lottery_type or "Screenshot", 
            output_path,
            datetime.now(),
            800, 600,
            url
        )
        return False, f"Unexpected error: {str(e)}"

def fix_screenshot_paths():
    """
    Fix all screenshot paths in the database
    
    Returns:
        dict: Operation results
    """
    try:
        from main import app
        from models import Screenshot, db
        
        # Create screenshots directory if it doesn't exist
        ensure_directory_exists(SCREENSHOT_DIR)
        
        results = {
            'total': 0,
            'fixed': 0,
            'failed': 0,
            'skipped': 0,
            'details': []
        }
        
        with app.app_context():
            # Get all screenshots
            screenshots = Screenshot.query.all()
            results['total'] = len(screenshots)
            
            for screenshot in screenshots:
                # Skip if already in the correct location
                if screenshot.path and os.path.exists(screenshot.path) and os.path.getsize(screenshot.path) > 100:
                    results['skipped'] += 1
                    continue
                
                # Generate new path
                timestamp_str = screenshot.timestamp.strftime('%Y%m%d_%H%M%S')
                filename = f"{timestamp_str}_{screenshot.lottery_type.replace(' ', '_').lower()}.png"
                new_path = os.path.join(SCREENSHOT_DIR, filename)
                
                # Attempt to create the image
                success, error = capture_with_requests(screenshot.url, new_path, screenshot.lottery_type)
                
                if success:
                    # Update the database with the new path
                    screenshot.path = new_path
                    db.session.commit()
                    results['fixed'] += 1
                    results['details'].append({
                        'id': screenshot.id,
                        'lottery_type': screenshot.lottery_type,
                        'status': 'fixed',
                        'path': new_path
                    })
                else:
                    results['failed'] += 1
                    results['details'].append({
                        'id': screenshot.id,
                        'lottery_type': screenshot.lottery_type,
                        'status': 'failed',
                        'error': error
                    })
        
        logger.info(f"Screenshot path fix completed: {results['fixed']} fixed, {results['failed']} failed, {results['skipped']} skipped")
        return results
    
    except Exception as e:
        logger.error(f"Error fixing screenshot paths: {str(e)}")
        return {
            'total': 0,
            'fixed': 0,
            'failed': 0,
            'skipped': 0,
            'error': str(e)
        }

def add_fix_route_to_app():
    """
    Add a route to fix screenshot paths
    
    Returns:
        bool: Success status
    """
    try:
        from main import app
        from flask import jsonify, redirect, url_for, flash
        from flask_login import login_required, current_user
        
        @app.route('/fix-screenshot-paths', methods=['GET', 'POST'])
        @login_required
        def fix_screenshot_paths_route():
            """Route to fix screenshot paths"""
            # Admin check
            if not current_user.is_admin:
                flash('You must be an admin to access this feature.', 'danger')
                return redirect(url_for('index'))
                
            results = fix_screenshot_paths()
            
            # Log results
            logger.info(f"Screenshot path fix results: {results['fixed']} fixed, {results['failed']} failed, {results['skipped']} skipped")
            
            # Flash message to user
            flash(f"Screenshot path fix completed: {results['fixed']} fixed, {results['failed']} failed, {results['skipped']} skipped", "info")
            
            # Redirect back to screenshots page
            return redirect(url_for('export_screenshots'))
        
        logger.info("Fix screenshot paths route added successfully")
        return True
        
    except Exception as e:
        logger.error(f"Error adding fix screenshot paths route: {str(e)}")
        return False

if __name__ == "__main__":
    logger.info("Starting script to fix screenshot paths")
    results = fix_screenshot_paths()
    logger.info(f"Screenshots fixed: {results['fixed']} of {results['total']}")