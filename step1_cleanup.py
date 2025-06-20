#!/usr/bin/env python3
"""
Step 1: Cleanup Module for Daily Automation
Cleans old screenshots and temporary files from the system
"""

import os
import glob
import logging
from datetime import datetime, timedelta

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def cleanup_old_screenshots(days_to_keep=7):
    """Clean up old screenshots older than specified days"""
    try:
        screenshot_dir = os.path.join(os.getcwd(), 'screenshots')
        if not os.path.exists(screenshot_dir):
            logger.info("Screenshots directory does not exist, nothing to clean")
            return True
            
        cutoff_date = datetime.now() - timedelta(days=days_to_keep)
        cleaned_count = 0
        total_files = 0
        
        # Find all screenshot files
        pattern = os.path.join(screenshot_dir, '*.png')
        screenshot_files = glob.glob(pattern)
        total_files = len(screenshot_files)
        
        for file_path in screenshot_files:
            try:
                file_time = datetime.fromtimestamp(os.path.getmtime(file_path))
                if file_time < cutoff_date:
                    os.remove(file_path)
                    cleaned_count += 1
                    logger.info(f"Removed old screenshot: {os.path.basename(file_path)}")
            except Exception as e:
                logger.warning(f"Failed to remove {file_path}: {str(e)}")
                continue
                
        logger.info(f"Cleanup completed: {cleaned_count} old screenshots removed out of {total_files} total files")
        logger.info(f"Keeping files newer than {days_to_keep} days (cutoff: {cutoff_date.strftime('%Y-%m-%d %H:%M:%S')})")
        return True
        
    except Exception as e:
        logger.error(f"Cleanup failed: {str(e)}")
        return False

def cleanup_all_screenshots():
    """Clean up ALL screenshots regardless of age"""
    try:
        screenshot_dir = os.path.join(os.getcwd(), 'screenshots')
        if not os.path.exists(screenshot_dir):
            logger.info("Screenshots directory does not exist, nothing to clean")
            return True
            
        cleaned_count = 0
        
        # Find all screenshot files
        pattern = os.path.join(screenshot_dir, '*.png')
        screenshot_files = glob.glob(pattern)
        
        for file_path in screenshot_files:
            try:
                os.remove(file_path)
                cleaned_count += 1
                logger.info(f"Removed screenshot: {os.path.basename(file_path)}")
            except Exception as e:
                logger.warning(f"Failed to remove {file_path}: {str(e)}")
                continue
                
        logger.info(f"Complete cleanup: {cleaned_count} screenshots removed")
        return True
        
    except Exception as e:
        logger.error(f"Complete cleanup failed: {str(e)}")
        return False

def cleanup_temp_files():
    """Clean up temporary files"""
    try:
        temp_patterns = [
            os.path.join(os.getcwd(), '*.tmp'),
            os.path.join(os.getcwd(), 'temp_*'),
            os.path.join(os.getcwd(), '*.log.old')
        ]
        
        cleaned_count = 0
        for pattern in temp_patterns:
            temp_files = glob.glob(pattern)
            for file_path in temp_files:
                try:
                    os.remove(file_path)
                    cleaned_count += 1
                    logger.info(f"Removed temp file: {os.path.basename(file_path)}")
                except Exception as e:
                    logger.warning(f"Failed to remove {file_path}: {str(e)}")
                    continue
                    
        logger.info(f"Temp cleanup completed: {cleaned_count} files removed")
        return True
        
    except Exception as e:
        logger.error(f"Temp cleanup failed: {str(e)}")
        return False

def run_cleanup():
    """Run the complete cleanup process - removes ALL screenshots"""
    logger.info("=== STEP 1: CLEANUP STARTED ===")
    
    success = True
    
    # Clean ALL screenshots (no age preservation)
    if not cleanup_all_screenshots():
        success = False
        
    # Clean temp files
    if not cleanup_temp_files():
        success = False
        
    if success:
        logger.info("=== STEP 1: CLEANUP COMPLETED SUCCESSFULLY ===")
    else:
        logger.error("=== STEP 1: CLEANUP COMPLETED WITH ERRORS ===")
        
    return success

if __name__ == "__main__":
    run_cleanup()