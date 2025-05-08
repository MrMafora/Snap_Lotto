"""
Simple fix for screenshot download issues.

This script:
1. Identifies HTML files saved as screenshots
2. Modifies file extensions to .txt if needed
3. Updates Flask routes to properly handle content types
"""
import os
import logging
import mimetypes
from flask import Flask
from config import Config
from models import db, Screenshot

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def check_file_type(filepath):
    """
    Check the actual file type of a file
    
    Args:
        filepath (str): Path to the file
        
    Returns:
        str: Detected MIME type
    """
    if not os.path.exists(filepath):
        return "unknown"
        
    try:
        # Try to read the first few bytes to detect file type
        with open(filepath, 'rb') as f:
            header = f.read(32)
            
        # Check for PNG signature
        if header.startswith(b'\x89PNG\r\n\x1a\n'):
            return "image/png"
            
        # Check for JPEG signature
        if header.startswith(b'\xff\xd8'):
            return "image/jpeg"
            
        # Check for HTML content
        if b'<!DOCTYPE html>' in header or b'<html' in header:
            return "text/html"
            
        # Default to binary data
        return "application/octet-stream"
    except Exception as e:
        logger.error(f"Error checking file type: {str(e)}")
        return "unknown"

def fix_file_extensions():
    """
    Fix file extensions to match actual content
    
    Returns:
        dict: Results of the fix operation
    """
    screenshots = Screenshot.query.all()
    fixed_count = 0
    text_html_count = 0
    png_count = 0
    
    for screenshot in screenshots:
        if not screenshot.path or not os.path.exists(screenshot.path):
            continue
            
        # Check file type
        mime_type = check_file_type(screenshot.path)
        _, ext = os.path.splitext(screenshot.path)
        
        # Count file types
        if mime_type == "text/html":
            text_html_count += 1
            
            # If it's HTML content but has .png extension, fix it
            if ext.lower() == '.png':
                new_path = screenshot.path.rsplit('.', 1)[0] + '.txt'
                try:
                    os.rename(screenshot.path, new_path)
                    screenshot.path = new_path
                    fixed_count += 1
                    logger.info(f"Fixed file extension for {screenshot.lottery_type}: {screenshot.path} -> {new_path}")
                except Exception as e:
                    logger.error(f"Error renaming file: {str(e)}")
        elif mime_type == "image/png":
            png_count += 1
            
    # Commit changes to database
    try:
        db.session.commit()
    except Exception as e:
        logger.error(f"Error committing changes to database: {str(e)}")
        db.session.rollback()
        
    return {
        "total": len(screenshots),
        "html_files": text_html_count,
        "png_files": png_count,
        "fixed": fixed_count
    }

def update_screenshot_viewers():
    """
    Update screenshot viewer routes in main.py to handle MIME types correctly
    
    Returns:
        bool: Success status
    """
    # This part would normally modify main.py, but we've already done that
    return True
    
if __name__ == "__main__":
    # Create Flask app context
    app = Flask(__name__)
    app.config.from_object(Config)
    db.init_app(app)
    
    with app.app_context():
        logger.info("Starting simple screenshot download fix...")
        
        # Fix file extensions
        results = fix_file_extensions()
        logger.info(f"Fixed {results['fixed']} of {results['total']} files")
        logger.info(f"Found {results['html_files']} HTML files and {results['png_files']} PNG files")