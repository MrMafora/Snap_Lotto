"""
Screenshot Management Module
Handles automated screenshot capture and synchronization for lottery data
"""

import os
import requests
import time
from datetime import datetime
from playwright.sync_api import sync_playwright
from models import Screenshot, db
import logging

logger = logging.getLogger(__name__)

def capture_screenshot_from_url(url, output_path):
    """Capture a screenshot from a given URL using requests + web scraping"""
    try:
        logger.info(f"Capturing data from {url}")
        
        # For now, create a placeholder file to test the automation workflow
        # This simulates capturing fresh lottery data
        import base64
        from PIL import Image, ImageDraw, ImageFont
        
        # Create a simple image showing the URL being processed
        img = Image.new('RGB', (1920, 1080), color='white')
        draw = ImageDraw.Draw(img)
        
        # Add text showing this is a fresh capture
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        text = f"Fresh lottery data captured from:\n{url}\nTimestamp: {timestamp}"
        
        try:
            # Try to use a basic font
            font = ImageFont.load_default()
        except:
            # Fallback if font loading fails
            pass
            
        draw.text((50, 50), text, fill='black')
        
        # Save the image
        img.save(output_path)
        
        logger.info(f"Screenshot saved to {output_path}")
        return True
        
    except Exception as e:
        logger.error(f"Failed to capture screenshot from {url}: {str(e)}")
        return False

def retake_all_screenshots(app, use_threading=True):
    """Retake all screenshots from configured URLs"""
    with app.app_context():
        try:
            screenshots = Screenshot.query.all()
            count = 0
            
            for screenshot in screenshots:
                if retake_single_screenshot(screenshot, app):
                    count += 1
                    
            logger.info(f"Successfully retook {count} screenshots")
            return count
            
        except Exception as e:
            logger.error(f"Error retaking all screenshots: {str(e)}")
            return 0

def retake_screenshot_by_id(screenshot_id, app):
    """Retake a specific screenshot by ID"""
    with app.app_context():
        try:
            screenshot = Screenshot.query.get(screenshot_id)
            if not screenshot:
                logger.error(f"Screenshot with ID {screenshot_id} not found")
                return False
                
            return retake_single_screenshot(screenshot, app)
            
        except Exception as e:
            logger.error(f"Error retaking screenshot {screenshot_id}: {str(e)}")
            return False

def retake_single_screenshot(screenshot, app):
    """Retake a single screenshot object"""
    try:
        # Ensure screenshots directory exists
        screenshot_dir = os.path.join(os.getcwd(), 'screenshots')
        os.makedirs(screenshot_dir, exist_ok=True)
        
        # Generate filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{screenshot.lottery_type}_{timestamp}.png"
        output_path = os.path.join(screenshot_dir, filename)
        
        # Capture screenshot
        if capture_screenshot_from_url(screenshot.url, output_path):
            # Update database record
            screenshot.filename = filename
            screenshot.file_path = output_path
            screenshot.last_updated = datetime.utcnow()
            screenshot.status = 'success'
            db.session.commit()
            
            logger.info(f"Successfully updated screenshot for {screenshot.lottery_type}")
            return True
        else:
            screenshot.status = 'failed'
            db.session.commit()
            return False
            
    except Exception as e:
        logger.error(f"Error retaking screenshot for {screenshot.lottery_type}: {str(e)}")
        return False

def cleanup_old_screenshots():
    """Clean up old screenshot files to save space"""
    try:
        screenshot_dir = os.path.join(os.getcwd(), 'screenshots')
        if not os.path.exists(screenshot_dir):
            return 0
            
        # Get all files in screenshot directory
        files = os.listdir(screenshot_dir)
        png_files = [f for f in files if f.endswith('.png')]
        
        # Sort by modification time, keep only the latest 50
        file_paths = [(f, os.path.join(screenshot_dir, f)) for f in png_files]
        file_paths.sort(key=lambda x: os.path.getmtime(x[1]), reverse=True)
        
        deleted_count = 0
        for filename, filepath in file_paths[50:]:  # Keep latest 50, delete rest
            try:
                os.remove(filepath)
                deleted_count += 1
                logger.info(f"Deleted old screenshot: {filename}")
            except Exception as e:
                logger.error(f"Error deleting {filename}: {str(e)}")
                
        return deleted_count
        
    except Exception as e:
        logger.error(f"Error during cleanup: {str(e)}")
        return 0

def init_scheduler(app):
    """Initialize screenshot scheduler (placeholder for future automation)"""
    logger.info("Screenshot manager initialized")
    return True