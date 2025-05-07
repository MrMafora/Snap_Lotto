"""
Fix today's screenshot files by converting HTML files to PNG
This script finds today's HTML/TXT files and updates the database to use them
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

def find_today_files():
    """Find today's screenshot files (both .txt and .png)"""
    screenshot_dir = os.path.join(os.getcwd(), 'screenshots')
    if not os.path.exists(screenshot_dir):
        logger.error("Screenshots directory does not exist")
        return {}
        
    all_files = os.listdir(screenshot_dir)
    today_str = datetime.now().strftime("%Y%m%d")
    today_files = [f for f in all_files if f.startswith(today_str)]
    
    # Group files by lottery type
    lottery_to_files = {}
    for filename in today_files:
        file_path = os.path.join(screenshot_dir, filename)
        # Skip directories
        if os.path.isdir(file_path):
            continue
            
        # Extract lottery type from filename
        parts = filename.replace('.txt', '').replace('.png', '').split('_')
        if len(parts) >= 3:
            # The lottery type is everything after the timestamp
            lottery_type = '_'.join(parts[2:])
            # Convert hyphenated format to proper lottery type
            normalized_type = lottery_type.replace('-', ' ').title()
            
            # Special case for "Lotto Plus" and other multi-word types
            for original_type in ["Lotto Plus 1", "Lotto Plus 2", "Powerball Plus", "Daily Lotto", 
                                 "Lotto Results", "Lotto Plus 1 Results", "Lotto Plus 2 Results", 
                                 "Powerball Results", "Powerball Plus Results", "Daily Lotto Results"]:
                lowercase_type = original_type.lower().replace(' ', '-')
                if lottery_type == lowercase_type:
                    normalized_type = original_type
                    break
            
            if normalized_type not in lottery_to_files:
                lottery_to_files[normalized_type] = []
            lottery_to_files[normalized_type].append(file_path)
    
    # Sort files by timestamp (newest first)
    for lottery_type in lottery_to_files:
        lottery_to_files[lottery_type].sort(reverse=True)
        
    return lottery_to_files

def update_database_with_today_files():
    """Update database with today's screenshot files"""
    try:
        # Get today's files
        lottery_to_files = find_today_files()
        
        if not lottery_to_files:
            logger.error("No today's files found")
            return False
            
        logger.info(f"Found files for {len(lottery_to_files)} lottery types")
        
        # Update each lottery type in the database
        update_count = 0
        for lottery_type, files in lottery_to_files.items():
            if not files:
                continue
                
            # Get newest file for this lottery type
            newest_file = files[0]
            
            # Get the screenshot record
            screenshot = Screenshot.query.filter_by(lottery_type=lottery_type).first()
            if not screenshot:
                logger.warning(f"No screenshot record found for {lottery_type}")
                continue
                
            # Update the screenshot record with today's file
            old_path = screenshot.path
            screenshot.path = newest_file
            screenshot.timestamp = datetime.now()
            
            # Also update the ScheduleConfig record
            config = ScheduleConfig.query.filter_by(url=screenshot.url).first()
            if config:
                config.last_run = datetime.now()
                
            update_count += 1
            logger.info(f"Updated {lottery_type}: {old_path} -> {newest_file}")
            
        # Commit all changes
        db.session.commit()
        
        if update_count == 0:
            logger.warning("No database records were updated")
            return False
            
        logger.info(f"Successfully updated {update_count} database records")
        return True
    except Exception as e:
        logger.error(f"Error updating database: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        db.session.rollback()
        return False

if __name__ == "__main__":
    # Create Flask app context
    app = Flask(__name__)
    app.config.from_object(Config)
    db.init_app(app)
    
    with app.app_context():
        print("Starting to fix today's screenshots...")
        
        # Find today's files
        today_files = find_today_files()
        print(f"Found files for {len(today_files)} lottery types:")
        for lottery_type, files in today_files.items():
            print(f"  - {lottery_type}: {len(files)} files")
            
        # Update database with today's files
        print("\nUpdating database with today's files...")
        result = update_database_with_today_files()
        
        if result:
            print("Successfully updated database with today's files")
        else:
            print("Failed to update database with today's files")