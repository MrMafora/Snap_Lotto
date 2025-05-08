"""
Fix screenshot download functionality

This script:
1. Creates a safe way to serve screenshot files for download
2. Ensures binary data is properly sent to client
3. Fixes empty file downloads issue
"""
import os
import io
import logging
from datetime import datetime
from PIL import Image, ImageDraw, ImageFont

# Set up logging
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

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

def create_download_placeholder_image(lottery_type, timestamp=None, width=800, height=600):
    """
    Create a placeholder image for download if the original is missing or corrupt
    
    Args:
        lottery_type (str): Type of lottery
        timestamp (datetime, optional): Timestamp for the image
        width (int): Width of the image
        height (int): Height of the image
        
    Returns:
        BytesIO: Image data in a BytesIO object
    """
    try:
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
            
        # Draw a blue rectangle at the top
        draw.rectangle(((0, 0), (width, 60)), fill=(0, 51, 102))
        
        # Draw header with white text
        draw.rectangle(((0, 0), (width, 50)), fill=(0, 51, 102))
        title = f"{lottery_type} Screenshot"
        draw.text((20, 15), title, fill=(255, 255, 255), font=font)
        
        # Draw timestamp
        timestamp_str = ts.strftime("%Y-%m-%d %H:%M:%S")
        draw.text((20, 70), f"Generated: {timestamp_str}", fill=(0, 0, 0), font=small_font)
        
        # Draw message
        draw.text((20, 120), "This is a placeholder image.", fill=(0, 0, 0), font=small_font)
        draw.text((20, 150), "The original screenshot could not be retrieved.", fill=(0, 0, 0), font=small_font)
        
        # Save the image to a BytesIO object
        img_io = io.BytesIO()
        image.save(img_io, 'PNG')
        img_io.seek(0)
        
        return img_io
        
    except Exception as e:
        logger.error(f"Error creating placeholder image: {str(e)}")
        # Return an empty BytesIO as a fallback
        return io.BytesIO()

def add_download_route_to_app():
    """
    Add a route to the Flask app for safe screenshot downloads
    
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        from main import app
        from flask import send_file, abort, flash, redirect, url_for
        from flask_login import login_required
        from models import Screenshot
        
        @app.route('/download-screenshot/<int:screenshot_id>')
        @login_required
        def download_screenshot(screenshot_id):
            """
            Download a screenshot as an attachment
            
            Args:
                screenshot_id (int): ID of the screenshot
                
            Returns:
                Response: File download response
            """
            try:
                # Get the screenshot
                screenshot = Screenshot.query.get_or_404(screenshot_id)
                
                # Create a proper filename for the download
                filename = f"{screenshot.lottery_type.replace(' ', '_')}_{screenshot.timestamp.strftime('%Y%m%d')}.png"
                
                # Check if the file exists and has content
                has_content = False
                if screenshot.path and os.path.exists(screenshot.path):
                    try:
                        filesize = os.path.getsize(screenshot.path)
                        has_content = filesize > 0
                    except:
                        has_content = False
                
                if has_content:
                    # Serve the file as an attachment with proper filename
                    return send_file(
                        screenshot.path,
                        mimetype='image/png',
                        as_attachment=True,
                        download_name=filename
                    )
                else:
                    # Create a placeholder image
                    img_io = create_download_placeholder_image(
                        screenshot.lottery_type,
                        screenshot.timestamp
                    )
                    
                    # Serve the placeholder image
                    return send_file(
                        img_io,
                        mimetype='image/png',
                        as_attachment=True,
                        download_name=filename
                    )
                    
            except Exception as e:
                logger.error(f"Error downloading screenshot {screenshot_id}: {str(e)}")
                flash(f"Error downloading screenshot: {str(e)}", "danger")
                return redirect(url_for('export_screenshots'))
        
        logger.info("Screenshot download route added successfully")
        return True
        
    except Exception as e:
        logger.error(f"Error adding download route: {str(e)}")
        return False

if __name__ == "__main__":
    logger.info("Adding screenshot download route to app")
    success = add_download_route_to_app()
    logger.info(f"Route added: {success}")