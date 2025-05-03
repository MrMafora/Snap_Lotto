"""
Scheduled screenshot validation and correction.

This script:
1. Regularly checks for misclassified lottery screenshots
2. Fixes naming inconsistencies and duplicates
3. Can be scheduled to run after screenshot captures
4. Prevents errors in lottery data extraction due to misclassified images
"""
import os
import logging
import sys
from PIL import Image
import imagehash
import re
import shutil
from collections import defaultdict
from datetime import datetime
import time
from main import app
from models import Screenshot, ScheduleConfig, db
from apscheduler.schedulers.background import BackgroundScheduler

# Set up logging
logging.basicConfig(level=logging.INFO,
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                   stream=sys.stdout)
logger = logging.getLogger("validate_screenshots")

def compute_image_hash(image_path):
    """Compute perceptual hash of an image for similarity comparison"""
    try:
        img = Image.open(image_path)
        # Use perceptual hash for image similarity
        p_hash = imagehash.phash(img)
        return p_hash
    except Exception as e:
        logger.error(f"Error computing hash for {image_path}: {str(e)}")
        return None

def is_powerball_plus_content(image_path):
    """Detect if an image contains PowerBall Plus content based on image analysis"""
    try:
        # Check filename for clues
        filename = os.path.basename(image_path).lower()
        if "plus" in filename:
            return True
            
        # Basic image pattern check
        # For more robust detection, we would need proper OCR
        # But for now, we'll use a simple heuristic based on known PowerBall Plus screenshots
        known_plus_hashes = [
            "ac966d63c26cc696",  # Known hash of PowerBall Plus screenshot  
        ]
        
        image_hash = compute_image_hash(image_path)
        if str(image_hash) in known_plus_hashes:
            return True
            
        return False
    except Exception as e:
        logger.error(f"Error checking PowerBall Plus content in {image_path}: {str(e)}")
        return False

def find_duplicate_screenshots():
    """Find duplicate screenshot images with different names/classifications"""
    logger.info("Finding duplicate screenshots")
    
    # Dictionary to group images by hash
    screenshot_hashes = defaultdict(list)
    screenshot_dir = os.path.join(os.getcwd(), 'screenshots')
    
    if not os.path.exists(screenshot_dir):
        logger.warning(f"Screenshots directory not found: {screenshot_dir}")
        return []
    
    # Process all PNG files in screenshots directory
    for filename in os.listdir(screenshot_dir):
        if filename.endswith('.png'):
            path = os.path.join(screenshot_dir, filename)
            image_hash = compute_image_hash(path)
            
            if image_hash:
                # Get lottery type from database record
                with app.app_context():
                    screenshot = Screenshot.query.filter(Screenshot.path.like(f"%{filename}%")).first()
                    lottery_type = screenshot.lottery_type if screenshot else None
                    
                    screenshot_hashes[str(image_hash)].append({
                        'path': path,
                        'filename': filename,
                        'lottery_type': lottery_type,
                        'db_record': screenshot,
                        'is_powerball_plus': is_powerball_plus_content(path)
                    })
    
    # Find duplicate groups (same hash, different lottery types)
    duplicates = []
    for hash_value, screenshots in screenshot_hashes.items():
        if len(screenshots) > 1:
            lottery_types = set(s['lottery_type'] for s in screenshots if s['lottery_type'])
            
            # If group has different lottery types, it's a potential duplicate
            if len(lottery_types) > 1:
                logger.info(f"Found potential duplicate group with hash {hash_value}")
                logger.info(f"Lottery types: {lottery_types}")
                for s in screenshots:
                    logger.info(f"  - {s['filename']} ({s['lottery_type']})")
                duplicates.append(screenshots)
            # Also consider cases where one has a lottery type and the other doesn't
            elif None in [s['lottery_type'] for s in screenshots]:
                duplicates.append(screenshots)
    
    return duplicates

def fix_misclassified_screenshots(duplicates):
    """Fix misclassified screenshots"""
    with app.app_context():
        issues_fixed = 0
        
        for duplicate_group in duplicates:
            # Check if this is a PowerBall vs PowerBall Plus issue
            has_powerball = any(s['lottery_type'] == 'PowerBall' for s in duplicate_group)
            has_powerball_plus = any(s['lottery_type'] == 'PowerBall Plus' for s in duplicate_group)
            
            if has_powerball and has_powerball_plus:
                logger.info(f"Found PowerBall/PowerBall Plus duplicate group")
                
                # Check content to determine correct classification
                for screenshot in duplicate_group:
                    actual_is_plus = screenshot['is_powerball_plus']
                    is_named_as_plus = screenshot['lottery_type'] == 'PowerBall Plus' if screenshot['lottery_type'] else False
                    
                    # If classification doesn't match content, fix it
                    if actual_is_plus != is_named_as_plus and screenshot['db_record']:
                        logger.info(f"Fixing misclassified screenshot: {screenshot['filename']}")
                        
                        # Fix database record
                        correct_type = 'PowerBall Plus' if actual_is_plus else 'PowerBall'
                        screenshot['db_record'].lottery_type = correct_type
                        db.session.commit()
                        issues_fixed += 1
            
            # Handle case where screenshot has no classification but duplicate does
            unclassified = [s for s in duplicate_group if not s['lottery_type']]
            classified = [s for s in duplicate_group if s['lottery_type']]
            
            if unclassified and classified:
                # Use classification from the classified screenshot
                for unclass_shot in unclassified:
                    if unclass_shot['db_record']:
                        # Pick first classified lottery type
                        correct_type = classified[0]['lottery_type']
                        logger.info(f"Assigning lottery type {correct_type} to unclassified screenshot {unclass_shot['filename']}")
                        unclass_shot['db_record'].lottery_type = correct_type
                        db.session.commit()
                        issues_fixed += 1
        
        return issues_fixed

def validate_all_screenshots():
    """Validate all screenshots and fix any issues"""
    logger.info("Starting screenshot validation")
    
    # Find duplicate screenshots
    duplicate_groups = find_duplicate_screenshots()
    logger.info(f"Found {len(duplicate_groups)} potential duplicate groups")
    
    # Fix misclassified screenshots
    if duplicate_groups:
        issues_fixed = fix_misclassified_screenshots(duplicate_groups)
        logger.info(f"Fixed {issues_fixed} misclassified screenshots")
    else:
        logger.info("No duplicate screenshots found")
    
    logger.info("Screenshot validation complete")

def schedule_validation():
    """Schedule regular screenshot validation"""
    scheduler = BackgroundScheduler()
    
    # Run validation every day at 3:00 AM (after screenshots are captured at 2:00 AM)
    scheduler.add_job(validate_all_screenshots, 'cron', hour=3, minute=0, id='screenshot_validation')
    
    # Also run validation immediately
    scheduler.add_job(validate_all_screenshots, 'date', run_date=datetime.now() + timedelta(seconds=10), id='immediate_validation')
    
    scheduler.start()
    logger.info("Scheduled screenshot validation to run daily at 3:00 AM")
    
    try:
        # Keep the main thread alive
        while True:
            time.sleep(60)
    except (KeyboardInterrupt, SystemExit):
        scheduler.shutdown()

if __name__ == "__main__":
    # If run directly, validate screenshots immediately
    validate_all_screenshots()
    
    # If --schedule parameter is provided, schedule regular validation
    if "--schedule" in sys.argv:
        from datetime import timedelta
        schedule_validation()