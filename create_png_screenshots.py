"""
Create PNG screenshots directly using wkhtmltoimage

This script:
1. Installs wkhtmltoimage if not already installed
2. Uses wkhtmltoimage to directly generate PNG screenshots
3. Updates the database to use these PNG files
"""
import os
import sys
import logging
import subprocess
from datetime import datetime
import time
from flask import Flask
from config import Config
from models import db, Screenshot, ScheduleConfig

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

def capture_with_wkhtmltoimage(url, output_path, lottery_type=None):
    """
    Capture a screenshot using wkhtmltoimage command line tool
    This is a more reliable method for capturing screenshots
    
    Args:
        url (str): URL to capture
        output_path (str): Path to save the screenshot
        lottery_type (str, optional): Type of lottery for logging
        
    Returns:
        tuple: (output_path, screenshot_data, error_message)
    """
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
        logger.info(f"Running command: {' '.join(cmd)}")
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

def capture_lottery_type(lottery_type):
    """
    Capture a screenshot for a specific lottery type
    
    Args:
        lottery_type (str): Type of lottery
        
    Returns:
        dict: Result of the screenshot capture
    """
    try:
        # Get the screenshot record from the database
        screenshot = Screenshot.query.filter_by(lottery_type=lottery_type).first()
        
        if not screenshot:
            logger.error(f"No screenshot record found for {lottery_type}")
            return {"success": False, "error": f"No screenshot record found for {lottery_type}"}
            
        logger.info(f"Capturing screenshot for {lottery_type} from {screenshot.url}")
        
        # Create the screenshots directory if it doesn't exist
        screenshot_dir = os.path.join(os.getcwd(), 'screenshots')
        if not os.path.exists(screenshot_dir):
            os.makedirs(screenshot_dir)
            
        # Generate a filename with today's date
        now = datetime.now()
        today_str = now.strftime("%Y%m%d")
        filename = f"{today_str}_{now.strftime('%H%M%S')}_{lottery_type.lower().replace(' ', '-')}.png"
        filepath = os.path.join(screenshot_dir, filename)
        
        # Capture the screenshot with wkhtmltoimage
        result = capture_with_wkhtmltoimage(screenshot.url, filepath, lottery_type)
        
        if not result or not result[0]:
            logger.error(f"Failed to capture screenshot for {lottery_type}")
            return {"success": False, "error": "Failed to capture screenshot"}
            
        # Update the screenshot record
        old_path = screenshot.path
        screenshot.path = filepath
        screenshot.timestamp = now
        
        # Update the schedule config record
        config = ScheduleConfig.query.filter_by(url=screenshot.url).first()
        if config:
            config.last_run = now
            
        # Commit the changes
        db.session.commit()
        
        logger.info(f"Successfully captured screenshot for {lottery_type}: {filepath}")
        return {
            "success": True,
            "lottery_type": lottery_type,
            "old_path": old_path,
            "new_path": filepath
        }
    except Exception as e:
        logger.error(f"Error capturing screenshot for {lottery_type}: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return {"success": False, "error": str(e)}

def capture_all():
    """
    Capture screenshots for all lottery types
    
    Returns:
        dict: Results of all screenshot captures
    """
    # Lottery types in desired order
    lottery_types = [
        "Lotto",
        "Lotto Plus 1",
        "Lotto Plus 2",
        "Powerball",
        "Powerball Plus",
        "Daily Lotto",
        "Lotto Results",
        "Lotto Plus 1 Results",
        "Lotto Plus 2 Results",
        "Powerball Results",
        "Powerball Plus Results",
        "Daily Lotto Results"
    ]
    
    results = []
    success_count = 0
    
    for lottery_type in lottery_types:
        logger.info(f"Processing {lottery_type}...")
        result = capture_lottery_type(lottery_type)
        results.append(result)
        
        if result.get("success", False):
            success_count += 1
            
        # Add a delay between captures
        time.sleep(2)
        
    return {
        "success": success_count > 0,
        "total": len(lottery_types),
        "successful": success_count,
        "results": results
    }

if __name__ == "__main__":
    # Create Flask app context
    app = Flask(__name__)
    app.config.from_object(Config)
    db.init_app(app)
    
    with app.app_context():
        print("Starting PNG screenshot creation process...")
        
        # Step 1: Install wkhtmltoimage if needed
        if not install_wkhtmltoimage():
            print("Failed to install wkhtmltoimage, exiting...")
            sys.exit(1)
            
        # Step 2: Process command line argument if provided
        if len(sys.argv) > 1:
            lottery_type = sys.argv[1]
            print(f"Capturing screenshot for {lottery_type}...")
            result = capture_lottery_type(lottery_type)
            print(f"Result: {result}")
        else:
            # Step 3: Capture all screenshots
            print("Capturing screenshots for all lottery types...")
            results = capture_all()
            print(f"Results: Successfully captured {results['successful']} of {results['total']} screenshots")