"""
Fix the download link in the export_screenshots.html template.

This script will update the download link to use the new download_screenshot route.
"""
import os
import sys
import logging

# Set up logging
logging.basicConfig(level=logging.INFO,
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def update_download_links():
    """
    Update the export_screenshots.html template to use the new download route
    
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        template_path = 'templates/export_screenshots.html'
        
        # Check if file exists
        if not os.path.exists(template_path):
            logger.error(f"Template file not found: {template_path}")
            return False
            
        # Read the template file
        with open(template_path, 'r') as f:
            content = f.read()
        
        # Replace the download link
        old_link_pattern = '<a href="{{ url_for(\'view_screenshot\', screenshot_id=screenshot.id) }}"'
        new_link = '<a href="{{ url_for(\'download_screenshot\', screenshot_id=screenshot.id) }}"'
        
        # Check if the pattern exists
        if old_link_pattern in content:
            # Replace the link in the content
            updated_content = content.replace(old_link_pattern, new_link)
            
            # Write the updated content back to the file
            with open(template_path, 'w') as f:
                f.write(updated_content)
                
            logger.info("Download links updated in template")
            return True
        else:
            logger.warning(f"Download link pattern not found in template: {old_link_pattern}")
            logger.info("Looking for alternative pattern...")
            
            # Try a simpler pattern
            alt_pattern = "url_for('view_screenshot'"
            if alt_pattern in content:
                updated_content = content.replace(alt_pattern, "url_for('download_screenshot'")
                
                # Write the updated content back to the file
                with open(template_path, 'w') as f:
                    f.write(updated_content)
                    
                logger.info("Download links updated using alternative pattern")
                return True
            else:
                logger.error("No suitable download link pattern found in template")
                return False
            
    except Exception as e:
        logger.error(f"Error updating download links: {str(e)}")
        return False

if __name__ == "__main__":
    logger.info("Updating download links in template...")
    success = update_download_links()
    
    if success:
        logger.info("Download links updated successfully")
        print("Download links updated successfully")
    else:
        logger.error("Failed to update download links")
        print("Error: Failed to update download links")
        sys.exit(1)