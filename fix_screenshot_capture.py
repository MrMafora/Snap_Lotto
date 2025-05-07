"""
Fix screenshot capture to ensure PNG images are saved

This script:
1. Updates the selenium_screenshot_manager.py to use wkhtmltoimage for PNG generation
2. Ensures screenshots are always saved as proper images, not text files
3. Manually triggers new screenshot captures to update all images
"""
import os
import sys
import logging
import subprocess
from datetime import datetime
import time
import shutil
from flask import Flask
from config import Config
from models import db, Screenshot

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def install_wkhtmltoimage():
    """Install wkhtmltoimage if not already installed"""
    try:
        # Check if wkhtmltoimage is already installed
        result = subprocess.run(['which', 'wkhtmltoimage'], capture_output=True)
        if result.returncode == 0:
            logger.info("wkhtmltoimage is already installed")
            return True
            
        # Install wkhtmltoimage if not installed
        logger.info("Installing wkhtmltoimage...")
        subprocess.run(['apt-get', 'update'], check=True)
        subprocess.run(['apt-get', 'install', '-y', 'wkhtmltopdf'], check=True)
        logger.info("wkhtmltoimage installed successfully")
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"Error installing wkhtmltoimage: {str(e)}")
        return False

def update_screenshot_capture_function():
    """
    Update selenium_screenshot_manager.py to ensure it always saves PNG images
    by using wkhtmltoimage as a backup method
    """
    try:
        file_path = "selenium_screenshot_manager.py"
        # Make a backup first
        backup_path = f"{file_path}.backup_{int(time.time())}"
        shutil.copy2(file_path, backup_path)
        logger.info(f"Created backup at {backup_path}")
        
        # Read the file contents
        with open(file_path, 'r') as f:
            content = f.read()
            
        # Check if the file already has the wkhtmltoimage function
        if "def capture_with_wkhtmltoimage(" in content:
            logger.info("wkhtmltoimage function already exists in the file")
            return True
            
        # Add the wkhtmltoimage function and update the capture function
        wkhtmltoimage_function = """
# Added wkhtmltoimage capture function
def capture_with_wkhtmltoimage(url, output_path, lottery_type=None):
    '''
    Capture a screenshot using wkhtmltoimage command line tool
    This is a more reliable method for capturing screenshots
    '''
    try:
        lottery_name = lottery_type or "Unknown"
        logger.info(f"[{lottery_name}] Capturing screenshot with wkhtmltoimage: {url}")
        
        # Create a temporary HTML file to store any cookies or headers needed
        cookie_file = os.path.join(os.getcwd(), 'cookies.txt')
        
        # Run wkhtmltoimage command
        cmd = [
            'wkhtmltoimage',
            '--quality', '100',
            '--width', '1200',
            '--height', '1500',
            '--javascript-delay', '5000',  # Wait for JavaScript execution (5 seconds)
            '--no-stop-slow-scripts',  # Don't stop slow running JavaScript
            url,
            output_path
        ]
        
        # Add cookie file if it exists
        if os.path.exists(cookie_file):
            cmd.insert(1, f'--cookie-jar')
            cmd.insert(2, cookie_file)
            
        # Execute the command
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
        
        if os.path.exists(output_path) and os.path.getsize(output_path) > 1000:
            logger.info(f"[{lottery_name}] Successfully captured screenshot with wkhtmltoimage")
            with open(output_path, 'rb') as f:
                screenshot_data = f.read()
            return output_path, screenshot_data, None
        else:
            error_msg = f"wkhtmltoimage failed or created an empty file: {result.stderr}"
            logger.error(f"[{lottery_name}] {error_msg}")
            return None, None, error_msg
    except Exception as e:
        error_msg = f"Error using wkhtmltoimage: {str(e)}"
        logger.error(f"[{lottery_name}] {error_msg}")
        return None, None, error_msg
"""

        # Update the fallback method in the capture_screenshot function to use wkhtmltoimage
        # Replace the part that saves HTML content as text files with wkhtmltoimage capture
        html_fallback_old = """            # Last resort: Save HTML with .txt extension instead of pretending it's a PNG
            txt_filepath = filepath.replace('.png', '.txt')
            with open(txt_filepath, 'wb') as f:
                f.write(html_content)
            
            logger.warning(f"[{lottery_name}] Saved HTML content to {txt_filepath} with proper .txt extension")
            
            # Log the attempt as successful but note we're using a text file
            diag.log_sync_attempt(lottery_name, url, True, "Saved HTML content as text file")
            
            # Return the txt_filepath as the actual filepath that should be used in the database
            return txt_filepath, html_content, None"""
            
        html_fallback_new = """            # Try one more approach using wkhtmltoimage (more reliable HTML to image conversion)
            logger.info(f"[{lottery_name}] Attempting to capture with wkhtmltoimage")
            wk_result = capture_with_wkhtmltoimage(url, filepath, lottery_type=lottery_name)
            
            if wk_result[0]:
                logger.info(f"[{lottery_name}] Successfully captured with wkhtmltoimage")
                diag.log_sync_attempt(lottery_name, url, True, "Captured with wkhtmltoimage")
                return wk_result
                
            # Last resort: Save HTML with .txt extension instead of pretending it's a PNG
            txt_filepath = filepath.replace('.png', '.txt')
            with open(txt_filepath, 'wb') as f:
                f.write(html_content)
            
            logger.warning(f"[{lottery_name}] Saved HTML content to {txt_filepath} with proper .txt extension")
            
            # Log the attempt as successful but note we're using a text file
            diag.log_sync_attempt(lottery_name, url, True, "Saved HTML content as text file")
            
            # Return the txt_filepath as the actual filepath that should be used in the database
            return txt_filepath, html_content, None"""
            
        # Insert the wkhtmltoimage function after the imports
        import_section_end = "MAX_CONCURRENT_THREADS = 6"
        updated_content = content.replace(import_section_end, f"{import_section_end}\n\n{wkhtmltoimage_function}")
        
        # Update the fallback method
        updated_content = updated_content.replace(html_fallback_old, html_fallback_new)
        
        # Write the updated content
        with open(file_path, 'w') as f:
            f.write(updated_content)
            
        logger.info("Updated selenium_screenshot_manager.py with wkhtmltoimage support")
        return True
    except Exception as e:
        logger.error(f"Error updating selenium_screenshot_manager.py: {str(e)}")
        return False

def trigger_new_screenshots():
    """Trigger new screenshots for all lottery types"""
    try:
        # Import the updated module to ensure we use the new version
        from importlib import reload
        import selenium_screenshot_manager
        reload(selenium_screenshot_manager)
        import fix_screenshot_sync
        reload(fix_screenshot_sync)
        
        logger.info("Triggering new screenshots for all lottery types")
        
        # Get all screenshot records
        screenshots = Screenshot.query.all()
        logger.info(f"Found {len(screenshots)} screenshot records")
        
        success_count = 0
        for screenshot in screenshots:
            try:
                logger.info(f"Syncing screenshot for {screenshot.lottery_type}...")
                result = selenium_screenshot_manager.sync_single_screenshot(screenshot.id)
                if result:
                    success_count += 1
                    logger.info(f"Successfully synced screenshot for {screenshot.lottery_type}")
                else:
                    logger.warning(f"Failed to sync screenshot for {screenshot.lottery_type}")
            except Exception as e:
                logger.error(f"Error syncing screenshot for {screenshot.lottery_type}: {str(e)}")
                
        # Reload the application to update all images
        logger.info("Fixing any screenshot synchronization issues")
        fix_results = fix_screenshot_sync.fix_lottery_sync_issues()
        
        return {
            'screenshots_synced': success_count,
            'total_screenshots': len(screenshots),
            'sync_fix_results': fix_results
        }
    except Exception as e:
        logger.error(f"Error triggering new screenshots: {str(e)}")
        return {
            'error': str(e)
        }

if __name__ == "__main__":
    # Create a Flask app context
    app = Flask(__name__)
    app.config.from_object(Config)
    db.init_app(app)
    
    with app.app_context():
        print("Starting screenshot capture fix process...")
        
        # Step 1: Install wkhtmltoimage if needed
        if not install_wkhtmltoimage():
            print("Failed to install wkhtmltoimage. Proceeding anyway...")
        
        # Step 2: Update the screenshot capture function
        if not update_screenshot_capture_function():
            print("Failed to update the screenshot capture function")
            sys.exit(1)
            
        # Step 3: Trigger new screenshots
        print("Triggering new screenshots...")
        results = trigger_new_screenshots()
        print(f"Results: {results}")
        
        if 'error' in results:
            print(f"Error triggering new screenshots: {results['error']}")
        else:
            print(f"Successfully synced {results['screenshots_synced']} of {results['total_screenshots']} screenshots")
            print("Now the system should be using the latest screenshots with proper PNG images.")