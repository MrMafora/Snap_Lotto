"""
Capture a single screenshot without concurrency
This script creates a new screenshot file for a single lottery type to ensure it's today's data
"""
import os
import sys
import logging
from datetime import datetime
import time
from flask import Flask
from config import Config
from models import db, Screenshot, ScheduleConfig

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def capture_single_type(lottery_type):
    """
    Capture a screenshot for a single lottery type
    Args:
        lottery_type (str): Type of lottery (e.g., 'Lotto', 'Powerball')
    Returns:
        dict: Result of screenshot capture
    """
    try:
        # Import screenshot manager
        import selenium_screenshot_manager as ssm
        
        # Get the Screenshot record
        screenshot = Screenshot.query.filter_by(lottery_type=lottery_type).first()
        
        if not screenshot:
            logger.error(f"No Screenshot record found for {lottery_type}")
            return {"success": False, "error": f"No Screenshot record found for {lottery_type}"}
            
        logger.info(f"Capturing screenshot for {lottery_type} from {screenshot.url}")
        
        # Get current timestamp
        now = datetime.now()
        today_str = now.strftime("%Y%m%d")
        
        # Ensure screenshot directory exists
        screenshot_dir = os.path.join(os.getcwd(), 'screenshots')
        if not os.path.exists(screenshot_dir):
            os.makedirs(screenshot_dir)
            
        # Create a filename with today's date
        filename = f"{today_str}_{now.strftime('%H%M%S')}_{lottery_type.lower().replace(' ', '-')}.png"
        filepath = os.path.join(screenshot_dir, filename)
        
        # Capture screenshot - we'll manually rename it after
        capture_result = ssm.capture_screenshot(screenshot.url)
        
        if not capture_result:
            logger.error(f"Failed to capture screenshot for {lottery_type}")
            return {"success": False, "error": f"Failed to capture screenshot for {lottery_type}"}
            
        # Unpack the result
        captured_filepath, screenshot_data, _ = capture_result
        
        # Copy the file to our desired filename
        if os.path.exists(captured_filepath):
            import shutil
            try:
                shutil.copy2(captured_filepath, filepath)
                # Use the new filepath instead
                captured_filepath = filepath
                logger.info(f"Copied screenshot to {filepath}")
            except Exception as copy_error:
                logger.warning(f"Could not copy screenshot to {filepath}: {str(copy_error)}")
        
        # Update Screenshot record
        old_path = screenshot.path
        screenshot.path = captured_filepath
        screenshot.timestamp = now
        
        # Update ScheduleConfig record
        config = ScheduleConfig.query.filter_by(url=screenshot.url).first()
        if config:
            config.last_run = now
            
        # Commit changes
        db.session.commit()
        
        logger.info(f"Successfully captured screenshot for {lottery_type}: {captured_filepath}")
        return {
            "success": True, 
            "lottery_type": lottery_type,
            "old_path": old_path,
            "new_path": captured_filepath
        }
    except Exception as e:
        logger.error(f"Error capturing screenshot for {lottery_type}: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        db.session.rollback()
        return {"success": False, "error": str(e)}

def capture_all_sequential():
    """
    Capture screenshots for all lottery types one at a time
    Returns:
        list: Results of all screenshot captures
    """
    # List of lottery types in desired order
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
    for lottery_type in lottery_types:
        logger.info(f"Processing {lottery_type}...")
        result = capture_single_type(lottery_type)
        results.append(result)
        # Add a small delay between captures to avoid overwhelming the server
        time.sleep(2)
        
    # Count successful captures
    success_count = sum(1 for r in results if r.get("success", False))
    logger.info(f"Completed {success_count} of {len(results)} screenshot captures successfully")
    
    return results

if __name__ == "__main__":
    # Create Flask app context
    app = Flask(__name__)
    app.config.from_object(Config)
    db.init_app(app)
    
    with app.app_context():
        # Process command line arg if provided
        if len(sys.argv) > 1:
            lottery_type = sys.argv[1]
            print(f"Capturing screenshot for {lottery_type}...")
            result = capture_single_type(lottery_type)
            print(f"Result: {result}")
        else:
            # Capture all lottery types sequentially
            print("Capturing screenshots for all lottery types sequentially...")
            results = capture_all_sequential()
            print(f"Successfully captured {sum(1 for r in results if r.get('success', False))} of {len(results)} screenshots")