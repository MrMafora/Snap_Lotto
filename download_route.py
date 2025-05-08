"""
Download Route - Improved Screenshot Download Functionality

This module provides a robust route for downloading screenshots with proper headers
and error handling. It ensures that valid files are sent to users, with appropriate
content types and filenames.
"""
import os
import logging
from flask import send_file, flash, redirect, url_for
from io import BytesIO
from PIL import Image, ImageDraw, ImageFont

# Configure logging
logging.basicConfig(level=logging.INFO,
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def add_download_route_to_app(app):
    """
    Add a download route to the Flask app
    
    Args:
        app: Flask application instance
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        from flask_login import login_required, current_user
        
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
            if not current_user.is_admin:
                flash('You must be an admin to download screenshots.', 'danger')
                return redirect(url_for('index'))
                
            try:
                from models import Screenshot
                
                # Get the screenshot
                screenshot = Screenshot.query.get_or_404(screenshot_id)
                
                # If the screenshot record exists but the file doesn't
                if not os.path.exists(screenshot.path):
                    logger.error(f"Screenshot file {screenshot.path} doesn't exist")
                    flash(f"The file for {screenshot.lottery_type} screenshot doesn't exist. Try syncing screenshots first.", "danger")
                    return redirect(url_for('export_screenshots'))
                
                # Get the file size
                file_size = os.path.getsize(screenshot.path)
                
                # Get the file extension
                _, ext = os.path.splitext(screenshot.path)
                
                # Determine content type based on extension
                content_type = 'image/png'  # Default
                if ext.lower() == '.jpg' or ext.lower() == '.jpeg':
                    content_type = 'image/jpeg'
                elif ext.lower() == '.gif':
                    content_type = 'image/gif'
                elif ext.lower() == '.bmp':
                    content_type = 'image/bmp'
                elif ext.lower() == '.txt':
                    content_type = 'text/plain'
                    
                # Create a clean filename
                filename = f"{screenshot.lottery_type.lower().replace(' ', '_')}{ext}"
                
                logger.info(f"Sending file {screenshot.path} ({file_size} bytes, {content_type})")
                
                # Return the file as an attachment with proper headers
                return send_file(
                    screenshot.path,
                    as_attachment=True,
                    download_name=filename,
                    mimetype=content_type
                )
                
            except Exception as e:
                logger.error(f"Error downloading screenshot {screenshot_id}: {str(e)}")
                flash(f"Error downloading screenshot: {str(e)}", "danger")
                return redirect(url_for('export_screenshots'))
                
        logger.info("Download route added to app")
        return True
        
    except Exception as e:
        logger.error(f"Error adding download route to app: {str(e)}")
        return False
        
if __name__ == "__main__":
    # Just for testing
    print("This module adds a download route to a Flask app.")
    print("Import and use add_download_route_to_app() to use this functionality.")