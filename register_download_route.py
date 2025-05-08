"""
Register the download route automatically when main.py starts.

This script should be run once to register the download functionality.
"""
import os
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def add_import_to_main():
    """
    Add an import to main.py to automatically load our download functionality
    
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        # Path to main.py
        main_path = 'main.py'
        
        # Read the file
        with open(main_path, 'r') as f:
            content = f.read()
        
        # Check if we've already applied this fix
        if 'import download_route' in content:
            logger.info("Import already exists in main.py")
            return True
        
        # Find the right place to insert our import
        import_section = '# Import required modules'
        if import_section in content:
            # Add our import at the end of the import section
            updated_content = content.replace(
                import_section,
                import_section + '\n# Import download route for screenshots\nimport download_route'
            )
            
            # Write back to the file
            with open(main_path, 'w') as f:
                f.write(updated_content)
                
            logger.info("Added import to main.py")
            return True
        else:
            logger.error("Could not find import section in main.py")
            return False
            
    except Exception as e:
        logger.error(f"Error adding import to main.py: {str(e)}")
        return False

def create_download_route_module():
    """
    Create a download_route.py module with our download functionality
    
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        # Path to the new module
        module_path = 'download_route.py'
        
        # Content for the module
        content = """# Download route for screenshots
import os
import logging
from flask import send_file, flash, redirect, url_for, send_from_directory
from flask_login import login_required
from main import app
from models import Screenshot

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@app.route('/download-screenshot/<int:screenshot_id>')
@login_required
def download_screenshot(screenshot_id):
    \"\"\"
    Download a screenshot as an attachment
    
    Args:
        screenshot_id (int): ID of the screenshot
        
    Returns:
        Response: File download response
    \"\"\"
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

# Log that the download route has been registered
logger.info("Screenshot download route registered successfully")
"""
        
        # Write the module
        with open(module_path, 'w') as f:
            f.write(content)
            
        logger.info(f"Created {module_path}")
        return True
        
    except Exception as e:
        logger.error(f"Error creating download_route.py: {str(e)}")
        return False

if __name__ == "__main__":
    # Create the download route module
    module_success = create_download_route_module()
    
    # Add the import to main.py
    import_success = add_import_to_main()
    
    if module_success and import_success:
        print("Successfully registered the download route!")
        print("The application will now correctly handle screenshot downloads.")
        print("Restart the server for the changes to take effect.")
    else:
        print("Failed to register the download route.")
        if not module_success:
            print("- Failed to create download_route.py")
        if not import_success:
            print("- Failed to add import to main.py")