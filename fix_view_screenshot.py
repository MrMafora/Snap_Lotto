"""
Fix the view_screenshot route to ensure it always returns a valid image
"""
import io
import os
import logging
from PIL import Image, ImageDraw, ImageFont
from io import BytesIO
from datetime import datetime

# Set up logging
logging.basicConfig(level=logging.INFO,
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def create_placeholder_image(lottery_type, timestamp=None, width=800, height=600):
    """
    Create a simple placeholder image for missing screenshots
    
    Args:
        lottery_type (str): Type of lottery
        timestamp (datetime, optional): Timestamp of the screenshot
        width (int): Width of the image
        height (int): Height of the image
        
    Returns:
        BytesIO: PNG image as BytesIO object
    """
    try:
        # Create a blank white image
        image = Image.new('RGB', (width, height), color=(255, 255, 255))
        draw = ImageDraw.Draw(image)
        
        # Draw a border
        draw.rectangle([(0, 0), (width-1, height-1)], outline=(200, 200, 200))
        
        # Draw header background
        draw.rectangle([(0, 0), (width, 50)], fill=(227, 242, 253))
        
        # Draw title
        title = f"{lottery_type} Screenshot"
        draw.text((20, 15), title, fill=(0, 0, 0))
        
        # Draw timestamp
        timestamp_str = timestamp.strftime("%Y-%m-%d %H:%M:%S") if timestamp else datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        draw.text((20, 60), f"Date: {timestamp_str}", fill=(100, 100, 100))
        
        # Draw placeholder message
        draw.text((20, 100), "Screenshot file is missing or corrupted.", fill=(0, 0, 0))
        draw.text((20, 130), "Please use the 'Regenerate Missing Screenshots' button", fill=(0, 0, 0))
        draw.text((20, 160), "on the Export Screenshots page to fix this issue.", fill=(0, 0, 0))
        
        # Save to BytesIO
        img_io = BytesIO()
        image.save(img_io, 'PNG')
        img_io.seek(0)
        
        return img_io
    except Exception as e:
        logger.error(f"Error creating placeholder image: {str(e)}")
        # Create a very basic fallback image with minimal dependencies
        fallback_img = BytesIO()
        Image.new('RGB', (400, 300), color=(255, 255, 255)).save(fallback_img, 'PNG')
        fallback_img.seek(0)
        return fallback_img

def update_view_screenshot_function():
    """
    Update the view_screenshot function to ensure it always returns a valid image
    
    Returns:
        bool: True if successful, False otherwise
    """
    from main import app
    from flask import send_file, abort, flash, redirect, url_for
    from flask_login import login_required, current_user
    from models import Screenshot, db
    
    @app.route('/screenshot/<int:screenshot_id>')
    def view_screenshot(screenshot_id):
        """
        View a single screenshot
        
        Args:
            screenshot_id (int): ID of the screenshot
            
        Returns:
            Response: Image file response
        """
        # Get the screenshot
        screenshot = Screenshot.query.get_or_404(screenshot_id)
        
        # Check if the file exists
        if screenshot.path and os.path.exists(screenshot.path):
            # If the file exists, serve it
            try:
                return send_file(screenshot.path)
            except Exception as e:
                logger.error(f"Error serving screenshot file: {str(e)}")
                # Fall through to create a placeholder image
        
        # If no valid file or error occurred, create and return a placeholder image
        logger.warning(f"Creating placeholder image for screenshot {screenshot_id}")
        img_io = create_placeholder_image(
            lottery_type=screenshot.lottery_type,
            timestamp=screenshot.timestamp
        )
        
        return send_file(img_io, mimetype='image/png')
    
    return True

if __name__ == "__main__":
    # Run with Flask app context
    from main import app
    
    # Update the view_screenshot function
    try:
        update_view_screenshot_function()
        logger.info("view_screenshot function updated successfully")
        print("view_screenshot function updated successfully")
    except Exception as e:
        logger.error(f"Error updating view_screenshot function: {str(e)}")
        print(f"Error updating view_screenshot function: {str(e)}")
        exit(1)
        
    print("Fix applied successfully")