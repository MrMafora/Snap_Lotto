#!/usr/bin/env python3
"""
Run cleanup for screenshot files.
This script ensures the cleanup function runs with a proper application context.
Performs comprehensive verification of the cleanup results.
"""
import os
import sys
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

if __name__ == "__main__":
    try:
        # Import app from main to get application context
        from main import app
        from screenshot_manager import cleanup_old_screenshots
        from models import Screenshot, db
        from data_aggregator import normalize_lottery_type
        
        # Count files before cleanup (exclude README.md)
        screenshot_dir = os.path.join(os.getcwd(), 'screenshots')
        files_before = [f for f in os.listdir(screenshot_dir) 
                         if os.path.isfile(os.path.join(screenshot_dir, f)) and f != 'README.md']
        before_count = len(files_before)
        logger.info(f"Files in screenshots directory before cleanup: {before_count}")
        
        # Print all file patterns
        html_files = len([f for f in files_before if f.endswith('.html')])
        png_files = len([f for f in files_before if f.endswith('.png')])
        logger.info(f"Before cleanup: {html_files} HTML files, {png_files} PNG files")
        
        # Run cleanup within app context
        with app.app_context():
            # Log current state of the database
            db_screenshots = Screenshot.query.all()
            logger.info(f"Database contains {len(db_screenshots)} screenshot records before cleanup")
            
            # Check unique lottery types after normalization
            norm_types = {}
            for screenshot in db_screenshots:
                norm_type = normalize_lottery_type(screenshot.lottery_type)
                if norm_type not in norm_types:
                    norm_types[norm_type] = []
                norm_types[norm_type].append(screenshot.lottery_type)
            
            logger.info(f"Found {len(norm_types)} unique normalized lottery types")
            for norm_type, types in norm_types.items():
                logger.info(f"  {norm_type}: {len(types)} variations - {', '.join(set(types))}")
            
            # Run the cleanup
            logger.info("Running screenshot cleanup...")
            cleanup_old_screenshots()
            
            # Verify we have exactly one screenshot per normalized lottery type
            db_screenshots_after = Screenshot.query.all()
            logger.info(f"Database contains {len(db_screenshots_after)} screenshot records after cleanup")
            
            # Verify distribution by normalized type
            norm_types_after = {}
            for screenshot in db_screenshots_after:
                norm_type = normalize_lottery_type(screenshot.lottery_type)
                if norm_type not in norm_types_after:
                    norm_types_after[norm_type] = []
                norm_types_after[norm_type].append(screenshot.id)
                
            # Check for duplicates
            for norm_type, ids in norm_types_after.items():
                if len(ids) > 1:
                    logger.warning(f"Found {len(ids)} screenshots for normalized type '{norm_type}' - should be exactly 1")
                else:
                    logger.info(f"Verified: exactly 1 screenshot for '{norm_type}'")
        
        # Count files after cleanup (exclude README.md)
        files_after = [f for f in os.listdir(screenshot_dir) 
                       if os.path.isfile(os.path.join(screenshot_dir, f)) and f != 'README.md']
        after_count = len(files_after)
        logger.info(f"Files in screenshots directory after cleanup: {after_count}")
        logger.info(f"Removed {before_count - after_count} files")
        
        # Check file types after cleanup
        html_files_after = len([f for f in files_after if f.endswith('.html')])
        png_files_after = len([f for f in files_after if f.endswith('.png')])
        logger.info(f"After cleanup: {html_files_after} HTML files, {png_files_after} PNG files")
        
        # Verify correct total number of files
        with app.app_context():
            # Each database record should have one HTML file and one PNG file
            expected_file_count = Screenshot.query.count() * 2
            if after_count == expected_file_count:
                logger.info(f"SUCCESS: Final count of {after_count} files matches expected count of {expected_file_count}")
            else:
                logger.warning(f"File count mismatch: {after_count} files on disk, expected {expected_file_count}")
        
    except Exception as e:
        logger.error(f"Error running cleanup: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        sys.exit(1)