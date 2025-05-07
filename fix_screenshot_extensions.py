"""
Fix screenshot file extensions

This script identifies all screenshot files that are actually HTML content
but have .png extensions, and renames them to use .txt extensions instead.
It also updates the database records to point to the correct file paths.
"""
import os
import sys
import logging
from datetime import datetime
from models import db, Screenshot

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def is_html_file(filepath):
    """Check if a file contains HTML content despite its extension"""
    try:
        with open(filepath, 'rb') as f:
            content = f.read(200)  # Just read the first 200 bytes to check
            return (b'<!DOCTYPE html>' in content or 
                   b'<html' in content or 
                   b'<HTML' in content)
    except Exception as e:
        logger.error(f"Error checking file {filepath}: {str(e)}")
        return False

def fix_screenshot_extensions():
    """
    Find all screenshot records, check if they're actually HTML files,
    and rename them to use .txt extensions if necessary.
    """
    try:
        # Get all screenshot records
        screenshots = Screenshot.query.all()
        logger.info(f"Found {len(screenshots)} screenshot records to check")
        
        fixed_count = 0
        error_count = 0
        
        for screenshot in screenshots:
            if not screenshot.path or not os.path.exists(screenshot.path):
                logger.warning(f"Screenshot ID {screenshot.id} has invalid path: {screenshot.path}")
                continue
                
            # Check if the file is actually HTML
            if is_html_file(screenshot.path) and screenshot.path.lower().endswith('.png'):
                try:
                    # Rename the file to use .txt extension
                    new_path = screenshot.path.replace('.png', '.txt')
                    os.rename(screenshot.path, new_path)
                    
                    # Update the database record
                    old_path = screenshot.path
                    screenshot.path = new_path
                    
                    # Update zoomed_path too if it exists and has the same issue
                    if screenshot.zoomed_path and os.path.exists(screenshot.zoomed_path):
                        if is_html_file(screenshot.zoomed_path) and screenshot.zoomed_path.lower().endswith('.png'):
                            new_zoomed_path = screenshot.zoomed_path.replace('.png', '.txt')
                            os.rename(screenshot.zoomed_path, new_zoomed_path)
                            screenshot.zoomed_path = new_zoomed_path
                    
                    # Add a note about the fix to the comments field
                    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    if screenshot.comments:
                        screenshot.comments += f"\nRenamed from {old_path} to {new_path} on {timestamp}"
                    else:
                        screenshot.comments = f"Renamed from {old_path} to {new_path} on {timestamp}"
                    
                    # Commit the change
                    db.session.commit()
                    
                    logger.info(f"Fixed screenshot ID {screenshot.id} - renamed {old_path} to {new_path}")
                    fixed_count += 1
                    
                except Exception as e:
                    logger.error(f"Error fixing screenshot ID {screenshot.id}: {str(e)}")
                    db.session.rollback()
                    error_count += 1
        
        # Return the summary results
        return {
            'screenshots_checked': len(screenshots),
            'fixed_count': fixed_count,
            'error_count': error_count
        }
        
    except Exception as e:
        logger.error(f"Error in fix_screenshot_extensions: {str(e)}")
        return {
            'error': str(e)
        }

if __name__ == "__main__":
    from flask import Flask
    from config import Config
    
    app = Flask(__name__)
    app.config.from_object(Config)
    db.init_app(app)
    
    with app.app_context():
        print("Starting screenshot extension fix...")
        results = fix_screenshot_extensions()
        print(f"Results: {results}")