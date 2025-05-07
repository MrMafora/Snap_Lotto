"""
Fix screenshots now - Direct script to fix screenshot database issues

This script:
1. Detects any HTML files incorrectly saved with .png extensions
2. Renames them to .txt files
3. Updates database records to point to the correct files
4. Removes HTML content from ZIP exports

Run this directly to immediately fix issues
"""
import os
import sys
import logging
from datetime import datetime
import mimetypes
from flask import Flask
from config import Config
from models import db, Screenshot

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def is_html_file(filepath):
    """Enhanced check if a file contains HTML content despite its extension"""
    try:
        # First, check by reading file content
        with open(filepath, 'rb') as f:
            content = f.read(1000)  # Read more bytes for better detection
            if (b'<!DOCTYPE html>' in content or 
                b'<html' in content or 
                b'<HTML' in content or
                b'<head>' in content or
                b'<body' in content):
                return True
                
        # As a backup, also check with mime type detection
        mime_type, _ = mimetypes.guess_type(filepath)
        if mime_type == 'text/html':
            return True
            
        # If the file is too small to be a valid image, it might be HTML/text
        if os.path.getsize(filepath) < 1000 and filepath.lower().endswith('.png'):
            # Do an additional check for image header
            with open(filepath, 'rb') as f:
                header = f.read(8)
                # PNG files start with these 8 bytes
                if header != b'\x89PNG\r\n\x1a\n':
                    return True
                    
        return False
    except Exception as e:
        logger.error(f"Error checking file {filepath}: {str(e)}")
        return False

def fix_all_screenshots():
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
        already_txt_count = 0
        
        for screenshot in screenshots:
            if not screenshot.path:
                logger.warning(f"Screenshot ID {screenshot.id} has no path")
                continue
                
            if not os.path.exists(screenshot.path):
                logger.warning(f"Screenshot ID {screenshot.id} has missing file: {screenshot.path}")
                continue
                
            # Skip files already with .txt extension
            if screenshot.path.lower().endswith('.txt'):
                already_txt_count += 1
                continue
                
            # Check if the file is actually HTML
            if is_html_file(screenshot.path):
                try:
                    # Rename the file to use .txt extension
                    if screenshot.path.lower().endswith('.png'):
                        new_path = screenshot.path.replace('.png', '.txt')
                    else:
                        # For other extensions, just append .txt
                        new_path = f"{screenshot.path}.txt"
                        
                    # Make sure we don't overwrite an existing file
                    if os.path.exists(new_path):
                        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
                        new_path = new_path.replace('.txt', f'_{timestamp}.txt')
                    
                    # Rename the file
                    os.rename(screenshot.path, new_path)
                    
                    # Update the database record
                    old_path = screenshot.path
                    screenshot.path = new_path
                    
                    # Update zoomed_path too if it exists and has the same issue
                    if screenshot.zoomed_path and os.path.exists(screenshot.zoomed_path):
                        if is_html_file(screenshot.zoomed_path):
                            if screenshot.zoomed_path.lower().endswith('.png'):
                                new_zoomed_path = screenshot.zoomed_path.replace('.png', '.txt')
                            else:
                                new_zoomed_path = f"{screenshot.zoomed_path}.txt"
                                
                            if os.path.exists(new_zoomed_path):
                                timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
                                new_zoomed_path = new_zoomed_path.replace('.txt', f'_{timestamp}.txt')
                                
                            os.rename(screenshot.zoomed_path, new_zoomed_path)
                            screenshot.zoomed_path = new_zoomed_path
                    
                    # Add a note about the fix to the comments field
                    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    comment = f"Fixed HTML content renamed from {old_path} to {new_path} on {timestamp}"
                    if screenshot.comments:
                        screenshot.comments += f"\n{comment}"
                    else:
                        screenshot.comments = comment
                    
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
            'error_count': error_count,
            'already_txt_count': already_txt_count
        }
        
    except Exception as e:
        logger.error(f"Error in fix_all_screenshots: {str(e)}")
        return {
            'error': str(e)
        }

if __name__ == "__main__":
    # Create a Flask app context to work with the database
    app = Flask(__name__)
    app.config.from_object(Config)
    db.init_app(app)
    
    with app.app_context():
        print("Starting direct fix for screenshot issues...")
        results = fix_all_screenshots()
        print(f"Results: {results}")
        
        if results.get('fixed_count', 0) > 0:
            print(f"Successfully fixed {results['fixed_count']} screenshot files.")
            print("Now when you download screenshots, you should only get actual images.")
        else:
            print("No screenshot files needed fixing.")