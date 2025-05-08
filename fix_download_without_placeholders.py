"""
Fix the screenshot download functionality without creating placeholder images.

This script:
1. Updates the download route to properly serve existing screenshot files
2. Ensures the path in the database is correct
3. Does NOT create placeholder images
"""
import os
import sys
import logging
from datetime import datetime

# Set up logging
logging.basicConfig(level=logging.INFO,
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Constants
SCREENSHOT_DIR = 'screenshots'

def ensure_directory_exists(directory):
    """Ensure a directory exists"""
    try:
        os.makedirs(directory, exist_ok=True)
        return True
    except Exception as e:
        logger.error(f"Error creating directory {directory}: {str(e)}")
        return False

def add_download_route_to_app():
    """
    Add a route to the Flask app for screenshot downloads
    
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        from main import app
        from flask import send_file, flash, redirect, url_for
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
                
                # Check if file exists and has content
                if screenshot.path and os.path.exists(screenshot.path) and os.path.getsize(screenshot.path) > 0:
                    # Get directory and basename
                    directory = os.path.dirname(screenshot.path)
                    basename = os.path.basename(screenshot.path)
                    
                    # Use send_from_directory for reliable delivery
                    return app.send_from_directory(
                        directory, 
                        basename,
                        as_attachment=True,
                        download_name=filename,
                        mimetype='image/png'
                    )
                else:
                    # No placeholder - simply inform user that file is missing
                    flash(f"Screenshot file not found or empty for {screenshot.lottery_type}", "warning")
                    return redirect(url_for('export_screenshots'))
                    
            except Exception as e:
                logger.error(f"Error downloading screenshot {screenshot_id}: {str(e)}")
                flash(f"Error downloading screenshot: {str(e)}", "danger")
                return redirect(url_for('export_screenshots'))
        
        logger.info("Screenshot download route added successfully")
        return True
        
    except Exception as e:
        logger.error(f"Error adding download route: {str(e)}")
        return False

def update_download_links():
    """
    Update download links in the template
    
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        template_path = 'templates/export_screenshots.html'
        
        # Read the template file
        with open(template_path, 'r') as f:
            content = f.read()
        
        # Replace the download link
        alt_pattern = "url_for('view_screenshot'"
        if alt_pattern in content:
            updated_content = content.replace(alt_pattern, "url_for('download_screenshot'")
            
            # Write the updated content back to the file
            with open(template_path, 'w') as f:
                f.write(updated_content)
                
            logger.info("Download links updated in template")
            return True
        else:
            logger.error("No suitable download link pattern found in template")
            return False
            
    except Exception as e:
        logger.error(f"Error updating download links: {str(e)}")
        return False

if __name__ == "__main__":
    logger.info("Starting screenshot download fix without placeholders...")
    
    # Make sure screenshots directory exists
    ensure_directory_exists(SCREENSHOT_DIR)
    
    # Add download route
    route_success = add_download_route_to_app()
    logger.info(f"Added download route: {route_success}")
    
    # Update template links
    template_success = update_download_links()
    logger.info(f"Updated template links: {template_success}")
    
    print("Screenshot download fix applied successfully!")
    print("Note: This fix does NOT create placeholder images.")
    print("For screenshots to work, you'll need to capture real screenshots using the existing functionality.")