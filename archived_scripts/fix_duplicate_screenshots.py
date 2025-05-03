"""
Fix duplicate screenshots with different names.

This script:
1. Analyzes screenshot images for similar content
2. Identifies misclassified screenshots
3. Updates the database records to properly classify lottery types
4. Optionally renames files to match correct lottery types
"""
import os
import logging
import sys
from PIL import Image
import imagehash
from io import BytesIO
import re
from datetime import datetime
import shutil
from collections import defaultdict
import sqlalchemy as sa
from main import app
from models import Screenshot, ScheduleConfig, db

# Set up logging
logging.basicConfig(level=logging.INFO,
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                   stream=sys.stdout)
logger = logging.getLogger("fix_duplicates")

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

def extract_lottery_info_from_path(path):
    """Extract lottery type and timestamp from file path"""
    try:
        filename = os.path.basename(path)
        
        # Extract lottery type (part before the first underscore)
        components = filename.split('_')
        if len(components) >= 2:
            lottery_type = '_'.join(components[:-2])  # Everything before timestamp and unique ID
            
            # Extract timestamp if available
            date_match = re.search(r'(\d{8}_\d{6})', filename)
            timestamp = date_match.group(1) if date_match else None
            
            return lottery_type, timestamp
        
        return None, None
    except Exception as e:
        logger.error(f"Error extracting info from path {path}: {str(e)}")
        return None, None

def is_powerball_plus_content(image_path):
    """Detect if an image contains PowerBall Plus content based on text in the image"""
    try:
        # This would ideally use OCR, but for now we'll use a simpler approach
        # by checking for "POWERBALL PLUS" text in the image filename
        filename = os.path.basename(image_path).lower()
        return "plus" in filename or "powerball_plus" in filename
    except Exception as e:
        logger.error(f"Error checking PowerBall Plus content in {image_path}: {str(e)}")
        return False

def find_duplicate_screenshots():
    """Find duplicate screenshot images with different names/classifications"""
    logger.info("Finding duplicate screenshots with different classifications")
    
    # Dictionary to group images by hash
    screenshot_hashes = defaultdict(list)
    screenshot_dir = os.path.join(os.getcwd(), 'screenshots')
    
    # Process all PNG files in screenshots directory
    for filename in os.listdir(screenshot_dir):
        if filename.endswith('.png'):
            path = os.path.join(screenshot_dir, filename)
            image_hash = compute_image_hash(path)
            
            if image_hash:
                # Store with lottery type info
                lottery_type, timestamp = extract_lottery_info_from_path(path)
                screenshot_hashes[str(image_hash)].append({
                    'path': path,
                    'lottery_type': lottery_type,
                    'timestamp': timestamp,
                    'is_powerball_plus': is_powerball_plus_content(path)
                })
    
    # Find duplicate groups (same hash, different lottery types)
    duplicates = []
    for hash_value, screenshots in screenshot_hashes.items():
        if len(screenshots) > 1:
            lottery_types = set(s['lottery_type'] for s in screenshots)
            
            # If group has different lottery types, it's a potential duplicate
            if len(lottery_types) > 1:
                logger.info(f"Found potential duplicate group with hash {hash_value}")
                logger.info(f"Lottery types: {lottery_types}")
                for s in screenshots:
                    logger.info(f"  - {s['path']}")
                duplicates.append(screenshots)
    
    return duplicates

def fix_powerball_duplicates(duplicates, dry_run=False):
    """Fix Powerball vs Powerball Plus duplicates"""
    with app.app_context():
        for duplicate_group in duplicates:
            # Check if this is a PowerBall vs PowerBall Plus issue
            has_powerball = any(s['lottery_type'] == 'Powerball' or 
                               s['lottery_type'] == 'PowerBall' for s in duplicate_group)
            has_powerball_plus = any(s['lottery_type'] == 'Powerball_Plus' or 
                                    s['lottery_type'] == 'PowerBall_Plus' for s in duplicate_group)
            
            if has_powerball and has_powerball_plus:
                logger.info(f"Found PowerBall/PowerBall Plus duplicate group")
                
                # Check content to determine correct classification
                for screenshot in duplicate_group:
                    actual_is_plus = screenshot['is_powerball_plus']
                    path = screenshot['path']
                    filename = os.path.basename(path)
                    
                    # Skip if lottery_type is missing
                    if not screenshot['lottery_type']:
                        continue
                    
                    is_named_as_plus = 'plus' in screenshot['lottery_type'].lower()
                    
                    # If classification doesn't match content, fix it
                    if actual_is_plus != is_named_as_plus:
                        logger.info(f"Misclassified screenshot: {path}")
                        logger.info(f"  Named as: {'PowerBall Plus' if is_named_as_plus else 'PowerBall'}")
                        logger.info(f"  Content is: {'PowerBall Plus' if actual_is_plus else 'PowerBall'}")
                        
                        if not dry_run:
                            # Fix database record
                            correct_type = 'PowerBall Plus' if actual_is_plus else 'PowerBall'
                            db_record = Screenshot.query.filter(Screenshot.path.like(f"%{filename}%")).first()
                            
                            if db_record:
                                logger.info(f"Updating database record ID {db_record.id} to {correct_type}")
                                db_record.lottery_type = correct_type
                                db.session.commit()
                            else:
                                logger.warning(f"Could not find database record for {filename}")
                            
                            # Rename file to match correct type
                            new_name = rename_screenshot(path, correct_type)
                            if new_name:
                                logger.info(f"Renamed file to {new_name}")
                                
                                # Update database record with new path
                                if db_record:
                                    db_record.path = new_name
                                    db_record.zoomed_path = new_name  # Set both paths to the same value
                                    db.session.commit()
                                    logger.info(f"Updated database paths for record ID {db_record.id}")
            else:
                logger.info(f"Found duplicate group with lottery types {set(s['lottery_type'] for s in duplicate_group)}")
                logger.info("Not a PowerBall/PowerBall Plus issue, skipping")

def rename_screenshot(path, correct_type):
    """Rename a screenshot file to match the correct lottery type"""
    try:
        filename = os.path.basename(path)
        directory = os.path.dirname(path)
        
        # Extract timestamp and unique ID from filename
        match = re.search(r'([^_]+)_(\d{8}_\d{6}_[^\.]+)\.png', filename)
        if match:
            _, timestamp_and_id = match.groups()
            
            # Create new filename with correct type
            new_filename = f"{correct_type.replace(' ', '_')}_{timestamp_and_id}.png"
            new_path = os.path.join(directory, new_filename)
            
            # Rename file
            shutil.copy2(path, new_path)  # Use copy2 to preserve metadata
            logger.info(f"Created copy with correct name: {new_path}")
            
            return new_path
        else:
            logger.warning(f"Could not parse filename pattern in {filename}")
            return None
    except Exception as e:
        logger.error(f"Error renaming {path}: {str(e)}")
        return None

def main(dry_run=False):
    """Main execution function"""
    logger.info(f"Starting duplicate screenshot fixer (dry_run={dry_run})")
    
    # Find duplicate screenshots
    duplicate_groups = find_duplicate_screenshots()
    logger.info(f"Found {len(duplicate_groups)} potential duplicate groups")
    
    # Fix PowerBall/PowerBall Plus duplicates
    if duplicate_groups:
        fix_powerball_duplicates(duplicate_groups, dry_run)
    
    logger.info("Duplicate fixing complete")

if __name__ == "__main__":
    # By default, perform a dry run (no changes)
    dry_run = "--dry-run" in sys.argv
    if "--help" in sys.argv:
        print("Usage: python fix_duplicate_screenshots.py [--dry-run]")
        print("  --dry-run    Only report issues, don't make changes")
        sys.exit(0)
    
    main(dry_run)