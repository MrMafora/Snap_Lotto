"""
Update latest screenshots with real PNG images

This script:
1. Finds all real PNG images in the screenshots folder
2. Updates the database to use these PNG images
3. Triggers new screenshot captures to get the latest data
"""
import os
import sys
import logging
import subprocess
from datetime import datetime
import time
from flask import Flask
from config import Config
from models import db, Screenshot

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def get_latest_png_files():
    """
    Get the latest PNG files for each date in the screenshots folder
    Returns a dict of date -> list of PNG files
    """
    screenshot_dir = os.path.join(os.getcwd(), 'screenshots')
    all_files = os.listdir(screenshot_dir)
    png_files = [f for f in all_files if f.endswith('.png')]
    
    # Group files by date (YYYYMMDD from the filename format)
    date_to_files = {}
    for png_file in png_files:
        parts = png_file.split('_')
        if len(parts) >= 2:
            date = parts[0]  # YYYYMMDD format
            if date not in date_to_files:
                date_to_files[date] = []
            date_to_files[date].append(png_file)
    
    # Sort dates (newest first)
    dates = sorted(date_to_files.keys(), reverse=True)
    
    # For each date, get the list of PNG files
    result = {}
    for date in dates:
        files = date_to_files[date]
        result[date] = [os.path.join(screenshot_dir, f) for f in files]
    
    return result

def manual_sync_process():
    """Manually run the complete sync process"""
    try:
        # Import the scheduler module
        import scheduler
        
        # Get all the lottery screenshots
        print("Taking screenshots of all lottery pages...")
        result = scheduler.retake_all_screenshots(None, use_threading=False)
        
        # Wait for the screenshots to be saved
        print("Waiting for screenshots to be saved...")
        time.sleep(5)
        
        return {
            'success': True,
            'result': result
        }
    except Exception as e:
        print(f"Error in manual sync: {str(e)}")
        return {
            'success': False,
            'error': str(e)
        }

def fix_screenshot_database():
    """
    Update the database to use the latest PNG files
    """
    try:
        # First, find the latest PNG files
        date_to_files = get_latest_png_files()
        
        if not date_to_files:
            print("No PNG files found in the screenshots folder")
            return False
            
        # Get the latest date
        latest_date = list(date_to_files.keys())[0]
        latest_files = date_to_files[latest_date]
        
        print(f"Found {len(latest_files)} PNG files for date {latest_date}")
        
        # Get all screenshot records
        screenshots = Screenshot.query.all()
        
        if not screenshots:
            print("No screenshot records found in the database")
            return False
            
        print(f"Found {len(screenshots)} screenshot records in the database")
        
        # Try to match each screenshot record to a PNG file
        updated_count = 0
        
        for screenshot in screenshots:
            lottery_type = screenshot.lottery_type.lower().replace(' ', '-')
            
            # Find a matching PNG file
            matching_files = []
            for png_file in latest_files:
                if lottery_type in png_file.lower():
                    matching_files.append(png_file)
            
            if matching_files:
                # Sort by timestamp (newest first)
                matching_files.sort(reverse=True)
                
                # Update the database record
                old_path = screenshot.path
                screenshot.path = matching_files[0]
                
                print(f"Updated {screenshot.lottery_type}: {old_path} -> {screenshot.path}")
                updated_count += 1
        
        # Commit all changes
        db.session.commit()
        
        print(f"Updated {updated_count} of {len(screenshots)} screenshot records")
        return updated_count > 0
    except Exception as e:
        print(f"Error fixing screenshot database: {str(e)}")
        return False

def trigger_capture_all_screenshots():
    """Run the capture_all_screenshots function directly"""
    try:
        from selenium_screenshot_manager import capture_all_screenshots
        
        # Run the function
        print("Capturing all screenshots...")
        results = capture_all_screenshots()
        
        # Print results
        print(f"Screenshot capture results: {results}")
        
        # Return success status
        if isinstance(results, dict):
            return results.get('success', 0) > 0
        else:
            return results > 0
    except Exception as e:
        print(f"Error triggering capture_all_screenshots: {str(e)}")
        return False

if __name__ == "__main__":
    # Create a Flask app context
    app = Flask(__name__)
    app.config.from_object(Config)
    db.init_app(app)
    
    with app.app_context():
        print("Starting update of latest screenshots...")
        
        # Step 1: Fix the screenshot database to use existing PNG files
        print("Fixing screenshot database to use existing PNG files...")
        if fix_screenshot_database():
            print("Successfully updated screenshot database")
        else:
            print("Failed to update screenshot database")
            
        # Step 2: Trigger new screenshot captures
        print("\nTaking screenshots for latest lottery results...")
        manual_sync_result = manual_sync_process()
        
        if manual_sync_result['success']:
            print("Successfully triggered new screenshots")
        else:
            print(f"Failed to trigger new screenshots: {manual_sync_result.get('error', 'Unknown error')}")
            
        print("\nScreenshot update process completed!")
        print("Now when you download screenshots, you should get actual images with the latest lottery results.")