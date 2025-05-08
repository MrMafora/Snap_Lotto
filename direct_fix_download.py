"""
Direct fix for screenshot downloads.

This script directly adds a download route to main.py.
"""
from main import app
from flask import send_file, flash, redirect, url_for, send_from_directory
from flask_login import login_required
from models import Screenshot
import os
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

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
            return send_from_directory(
                directory, 
                basename,
                as_attachment=True,
                download_name=filename,
                mimetype='image/png'
            )
        else:
            # Log detailed information
            logger.warning(f"Screenshot file issue: path={screenshot.path}, exists={os.path.exists(screenshot.path) if screenshot.path else False}")
            
            # Redirect to capture screenshots
            flash(f"Screenshot file not found or empty. Try capturing screenshots again.", "warning")
            return redirect(url_for('export_screenshots'))
            
    except Exception as e:
        logger.error(f"Error downloading screenshot {screenshot_id}: {str(e)}")
        flash(f"Error downloading screenshot: {str(e)}", "danger")
        return redirect(url_for('export_screenshots'))

print("Download route added successfully!")
print("To download screenshots, use the URL /download-screenshot/<screenshot_id>")
print("The files will be properly served as attachments with the correct filename.")