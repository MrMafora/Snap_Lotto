"""
Register Screenshot Download Fix

This script integrates the screenshot download fix with the main application
by adding the required routes and functions.
"""
import os
import sys
import logging

# Set up logging
logging.basicConfig(level=logging.INFO,
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def register_all_fixes():
    """
    Register all screenshot fixes with the main application
    
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        # Import Flask app
        from main import app
        
        # Import fix modules
        import fix_screenshot_download
        import fix_screenshot_paths
        
        # Register download fix
        logger.info("Registering screenshot download fix...")
        download_success = fix_screenshot_download.add_download_route_to_app()
        
        # Register path fix
        logger.info("Registering screenshot path fix...")
        path_success = fix_screenshot_paths.add_fix_route_to_app()
        
        # Update export_screenshots.html template to use our new download route
        update_template_success = update_download_links()
        
        # Return overall success
        return download_success and path_success and update_template_success
        
    except Exception as e:
        logger.error(f"Error registering fixes: {str(e)}")
        return False

def update_download_links():
    """
    Update the export_screenshots.html template to use the new download route
    
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        template_path = 'templates/export_screenshots.html'
        
        # Read the template file
        with open(template_path, 'r') as f:
            content = f.read()
        
        # Replace the download link
        old_link = """<a href="{{ url_for('view_screenshot', screenshot_id=screenshot.id) }}" 
                                           class="btn btn-sm btn-primary flex-fill" 
                                           download="{{ screenshot.lottery_type|replace(' ', '_') }}_{{ screenshot.timestamp.strftime('%Y%m%d') }}.png">
                                            <i class="fas fa-download me-1"></i> Download
                                        </a>"""
        
        new_link = """<a href="{{ url_for('download_screenshot', screenshot_id=screenshot.id) }}" 
                                           class="btn btn-sm btn-primary flex-fill">
                                            <i class="fas fa-download me-1"></i> Download
                                        </a>"""
        
        # Replace the link in the content
        if old_link in content:
            updated_content = content.replace(old_link, new_link)
            
            # Write the updated content back to the file
            with open(template_path, 'w') as f:
                f.write(updated_content)
                
            logger.info("Download links updated in template")
            return True
        else:
            logger.warning("Download link pattern not found in template")
            return False
            
    except Exception as e:
        logger.error(f"Error updating download links: {str(e)}")
        return False

def fix_missing_screenshots():
    """
    Fix missing screenshots by generating placeholders for all entries
    
    Returns:
        dict: Operation results
    """
    try:
        from main import app
        
        with app.app_context():
            from fix_screenshot_paths import fix_screenshot_paths
            results = fix_screenshot_paths()
            
            logger.info(f"Screenshot fix results: {results['fixed']} fixed, {results['failed']} failed, {results['skipped']} skipped")
            return results
    except Exception as e:
        logger.error(f"Error fixing missing screenshots: {str(e)}")
        return {
            'total': 0,
            'fixed': 0,
            'failed': 0,
            'skipped': 0,
            'error': str(e)
        }

if __name__ == "__main__":
    logger.info("Registering screenshot fixes...")
    success = register_all_fixes()
    
    if success:
        logger.info("Screenshot fixes registered successfully")
        
        # Run the fix to create missing screenshots
        logger.info("Fixing missing screenshots...")
        results = fix_missing_screenshots()
        
        logger.info(f"Missing screenshots fixed: {results['fixed']} of {results['total']}")
        logger.info(f"Failed: {results['failed']}, Skipped: {results['skipped']}")
        
        print("Screenshot fixes applied successfully")
    else:
        logger.error("Failed to register screenshot fixes")
        print("Error: Failed to register screenshot fixes")
        sys.exit(1)