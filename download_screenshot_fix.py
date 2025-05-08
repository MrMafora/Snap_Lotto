"""
Fix screenshot download functionality - No placeholders.

This script:
1. Adds a proper download route that correctly handles file attachments
2. Updates the template to use this download route
"""
import os
import sys
import logging

# Set up logging
logging.basicConfig(level=logging.INFO,
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def add_download_route():
    """
    Add a download route to the Flask app
    
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
            Download a screenshot file as an attachment
            
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
                
                # Validate the file path and exists
                if not screenshot.path:
                    flash(f"Screenshot path is missing for {screenshot.lottery_type}", "warning")
                    return redirect(url_for('export_screenshots'))
                
                if not os.path.exists(screenshot.path):
                    flash(f"Screenshot file does not exist: {screenshot.path}", "warning")
                    return redirect(url_for('export_screenshots'))
                
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
                    
            except Exception as e:
                logger.error(f"Error downloading screenshot {screenshot_id}: {str(e)}")
                flash(f"Error downloading screenshot: {str(e)}", "danger")
                return redirect(url_for('export_screenshots'))
        
        logger.info("Download route added successfully")
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
    logger.info("Applying screenshot download fix...")
    
    # Add download route
    route_success = add_download_route()
    
    # Update download links in template
    template_success = update_download_links()
    
    if route_success and template_success:
        logger.info("Screenshot download fix applied successfully")
        print("Screenshot download fix applied successfully!")
        print("NOTE: This fix only modifies the download functionality.")
        print("      It does NOT create any placeholder images.")
        print("      You'll need to use the existing screenshot capture tools")
        print("      to get actual lottery screenshots.")
    else:
        logger.error("Failed to apply screenshot download fix")
        print("Error: Failed to apply screenshot download fix")
        if not route_success:
            print("- Failed to add download route")
        if not template_success:
            print("- Failed to update template links")
        sys.exit(1)