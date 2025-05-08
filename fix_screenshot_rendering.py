"""
Fix the screenshot rendering and download issues.

This script:
1. Verifies if screenshots are actually PNG files
2. Recaptures screenshots if they are HTML/text files
3. Updates database records to point to proper PNG files
"""
import os
import sys
import logging
import subprocess
import mimetypes
import shutil
from datetime import datetime
from flask import Flask
from config import Config
from models import db, Screenshot, ScheduleConfig

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def ensure_wkhtmltoimage_installed():
    """Ensure wkhtmltoimage is installed"""
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

def is_valid_png(filepath):
    """Check if a file is a valid PNG image by examining its magic bytes"""
    try:
        if not os.path.exists(filepath):
            logger.warning(f"File does not exist: {filepath}")
            return False
            
        # Check file size (PNG files should be at least a few hundred bytes)
        if os.path.getsize(filepath) < 100:
            logger.warning(f"File too small to be a valid PNG: {filepath}")
            return False
            
        # Check file signature/magic bytes
        with open(filepath, 'rb') as f:
            header = f.read(8)
            # PNG signature is 89 50 4E 47 0D 0A 1A 0A in hex
            if header != b'\x89\x50\x4e\x47\x0d\x0a\x1a\x0a':
                logger.warning(f"File is not a valid PNG image: {filepath}")
                return False
                
        return True
    except Exception as e:
        logger.error(f"Error checking PNG validity: {str(e)}")
        return False

def capture_with_wkhtmltoimage(url, output_path, lottery_type=None):
    """
    Capture a screenshot using wkhtmltoimage with enhanced reliability
    
    Args:
        url (str): URL to capture
        output_path (str): Path to save the screenshot
        lottery_type (str, optional): Type of lottery for logging
        
    Returns:
        bool: Success status
    """
    try:
        lottery_name = lottery_type or "Unknown"
        logger.info(f"[{lottery_name}] Capturing screenshot with wkhtmltoimage: {url}")
        
        # Remove any existing file with the same name
        if os.path.exists(output_path):
            os.remove(output_path)
        
        # Create a cookie file if needed
        cookie_file = os.path.join(os.getcwd(), 'cookies.txt')
        
        # Enhanced wkhtmltoimage command with more reliable parameters
        cmd = [
            'wkhtmltoimage',
            '--quality', '100',
            '--width', '1200',
            '--height', '1500',
            '--javascript-delay', '8000',  # Increased wait for JavaScript execution (8 seconds)
            '--no-stop-slow-scripts',  # Don't stop slow running JavaScript
            '--disable-smart-width',  # Disable smart width sizing
            '--enable-javascript',
            '--disable-local-file-access',
            '--load-error-handling', 'ignore',
            url,
            output_path
        ]
        
        # Add cookie file if it exists
        if os.path.exists(cookie_file):
            cmd.insert(1, f'--cookie-jar')
            cmd.insert(2, cookie_file)
            
        # Execute the command
        logger.info(f"Running command: {' '.join(cmd)}")
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
        
        # Verify the file was created and is a valid PNG
        if os.path.exists(output_path) and is_valid_png(output_path):
            logger.info(f"[{lottery_name}] Successfully captured screenshot with wkhtmltoimage")
            return True
        else:
            error_msg = f"wkhtmltoimage failed or created an invalid file: {result.stderr}"
            logger.error(f"[{lottery_name}] {error_msg}")
            
            # If the file exists but isn't a valid PNG, remove it
            if os.path.exists(output_path) and not is_valid_png(output_path):
                os.remove(output_path)
                
            return False
    except Exception as e:
        error_msg = f"Error using wkhtmltoimage: {str(e)}"
        logger.error(f"[{lottery_name}] {error_msg}")
        return False

def fix_screenshot_by_id(screenshot_id):
    """
    Fix a specific screenshot by recapturing it properly as a PNG
    
    Args:
        screenshot_id (int): ID of the screenshot to fix
        
    Returns:
        dict: Result information
    """
    try:
        # Get the screenshot record
        screenshot = Screenshot.query.get(screenshot_id)
        if not screenshot:
            return {"success": False, "error": f"No screenshot found with ID {screenshot_id}"}
            
        logger.info(f"Fixing screenshot for {screenshot.lottery_type} (ID: {screenshot_id})")
        
        # Check if the current path is a valid PNG
        current_path = screenshot.path
        if current_path and os.path.exists(current_path) and is_valid_png(current_path):
            logger.info(f"Screenshot is already a valid PNG: {current_path}")
            return {"success": True, "path": current_path, "action": "verified"}
            
        # Create screenshots directory if needed
        screenshot_dir = os.path.join(os.getcwd(), 'screenshots')
        if not os.path.exists(screenshot_dir):
            os.makedirs(screenshot_dir)
        
        # Generate a new filename
        now = datetime.now()
        today_str = now.strftime("%Y%m%d")
        filename = f"{today_str}_{now.strftime('%H%M%S')}_{screenshot.lottery_type.lower().replace(' ', '-')}.png"
        new_path = os.path.join(screenshot_dir, filename)
        
        # Capture the screenshot properly
        if capture_with_wkhtmltoimage(screenshot.url, new_path, screenshot.lottery_type):
            # Screenshot successfully captured, update database
            old_path = screenshot.path
            screenshot.path = new_path
            screenshot.timestamp = now
            
            # Update related schedule config
            config = ScheduleConfig.query.filter_by(url=screenshot.url).first()
            if config:
                config.last_run = now
                
            # Commit changes
            db.session.commit()
            
            logger.info(f"Successfully updated screenshot for {screenshot.lottery_type}: {new_path}")
            return {
                "success": True, 
                "old_path": old_path, 
                "new_path": new_path, 
                "action": "recaptured"
            }
        else:
            return {"success": False, "error": "Failed to capture screenshot"}
    except Exception as e:
        logger.error(f"Error fixing screenshot {screenshot_id}: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return {"success": False, "error": str(e)}

def fix_all_screenshots():
    """
    Fix all screenshots by ensuring they are proper PNG files
    
    Returns:
        dict: Results summary
    """
    # Get all screenshots
    screenshots = Screenshot.query.all()
    
    results = []
    success_count = 0
    total_count = len(screenshots)
    
    for screenshot in screenshots:
        logger.info(f"Processing screenshot {screenshot.id} ({screenshot.lottery_type})...")
        result = fix_screenshot_by_id(screenshot.id)
        results.append(result)
        
        if result.get("success", False):
            success_count += 1
            
        # Add a delay between captures to avoid overwhelming the server
        import time
        time.sleep(2)
        
    return {
        "success": success_count > 0,
        "total": total_count,
        "fixed": success_count,
        "results": results
    }

if __name__ == "__main__":
    # Create Flask app context
    app = Flask(__name__)
    app.config.from_object(Config)
    db.init_app(app)
    
    with app.app_context():
        logger.info("Starting screenshot rendering fix process...")
        
        # Ensure wkhtmltoimage is installed
        if not ensure_wkhtmltoimage_installed():
            logger.error("Failed to install wkhtmltoimage, exiting...")
            sys.exit(1)
            
        # Process specific screenshot if ID provided
        if len(sys.argv) > 1:
            try:
                screenshot_id = int(sys.argv[1])
                logger.info(f"Fixing screenshot with ID {screenshot_id}...")
                result = fix_screenshot_by_id(screenshot_id)
                logger.info(f"Result: {result}")
            except ValueError:
                logger.error(f"Invalid screenshot ID: {sys.argv[1]}")
                sys.exit(1)
        else:
            # Fix all screenshots
            logger.info("Fixing all screenshots...")
            results = fix_all_screenshots()
            logger.info(f"Results: Successfully fixed {results['fixed']} of {results['total']} screenshots")