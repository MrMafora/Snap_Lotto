"""
Update screenshot database records to use PNG files instead of TXT files

This script:
1. Finds all the PNG files in the screenshots directory
2. Matches them to the appropriate lottery types
3. Updates the database to use the PNG files instead of TXT files
"""
import os
import sys
import logging
import re
from datetime import datetime
from flask import Flask
from config import Config
from models import db, Screenshot

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def extract_lottery_type_from_filename(filename):
    """Extract the lottery type from a filename"""
    if 'daily-lotto-history' in filename:
        return 'Daily Lotto'
    elif 'daily-lotto' in filename:
        return 'Daily Lotto Results'
    elif 'lotto-plus-1-history' in filename:
        return 'Lotto Plus 1'
    elif 'lotto-plus-1-results' in filename:
        return 'Lotto Plus 1 Results'
    elif 'lotto-plus-2-history' in filename:
        return 'Lotto Plus 2'
    elif 'lotto-plus-2-results' in filename:
        return 'Lotto Plus 2 Results'
    elif 'powerball-plus-history' in filename:
        return 'Powerball Plus'
    elif 'powerball-plus' in filename:
        return 'Powerball Plus Results'
    elif 'powerball-history' in filename:
        return 'Powerball'
    elif 'powerball' in filename:
        return 'Powerball Results'
    elif 'lotto-history' in filename:
        return 'Lotto'
    elif 'lotto' in filename:
        return 'Lotto Results'
    else:
        return None

def map_png_files_to_lottery_types():
    """Map PNG files to lottery types"""
    screenshot_dir = os.path.join(os.getcwd(), 'screenshots')
    png_files = [f for f in os.listdir(screenshot_dir) 
               if f.endswith('.png') and os.path.isfile(os.path.join(screenshot_dir, f))]
    
    # Sort by date (newest first)
    png_files.sort(reverse=True)
    
    # Create a mapping of lottery types to their newest PNG files
    lottery_type_to_png = {}
    
    for png_file in png_files:
        lottery_type = extract_lottery_type_from_filename(png_file)
        if lottery_type and lottery_type not in lottery_type_to_png:
            lottery_type_to_png[lottery_type] = os.path.join(screenshot_dir, png_file)
    
    return lottery_type_to_png

def update_screenshot_records():
    """Update screenshot records to use PNG files"""
    try:
        # Get mapping of lottery types to PNG files
        lottery_type_to_png = map_png_files_to_lottery_types()
        logger.info(f"Found {len(lottery_type_to_png)} lottery types with PNG files")
        
        # Get all screenshot records
        screenshots = Screenshot.query.all()
        logger.info(f"Found {len(screenshots)} screenshot records")
        
        updated_count = 0
        not_found_count = 0
        
        for screenshot in screenshots:
            if screenshot.lottery_type in lottery_type_to_png:
                # Save the old path for logging
                old_path = screenshot.path
                
                # Update to the new PNG path
                screenshot.path = lottery_type_to_png[screenshot.lottery_type]
                
                # Skip commenting as the model doesn't have a comments field
                timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                
                logger.info(f"Updated {screenshot.lottery_type}: {old_path} -> {screenshot.path}")
                updated_count += 1
            else:
                logger.warning(f"No matching PNG found for {screenshot.lottery_type}")
                not_found_count += 1
        
        # Commit all changes
        db.session.commit()
        
        return {
            'total_screenshots': len(screenshots),
            'updated_count': updated_count,
            'not_found_count': not_found_count
        }
        
    except Exception as e:
        logger.error(f"Error updating screenshot records: {str(e)}")
        db.session.rollback()
        return {
            'error': str(e)
        }

if __name__ == "__main__":
    # Create a Flask app context
    app = Flask(__name__)
    app.config.from_object(Config)
    db.init_app(app)
    
    with app.app_context():
        print("Starting update of screenshot records from TXT to PNG...")
        results = update_screenshot_records()
        print(f"Results: {results}")
        
        if results.get('updated_count', 0) > 0:
            print(f"Successfully updated {results['updated_count']} screenshot records to use PNG files.")
            print("Now when you download screenshots, you should get actual images.")
        else:
            print("No screenshot records were updated. Check the logs for details.")