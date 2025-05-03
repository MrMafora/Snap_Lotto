"""
Check for duplicate lottery screenshots in the attached_assets folder.

This script:
1. Analyzes the similarity of lottery screenshots in attached_assets
2. Identifies images that contain the same content but have different filenames
3. Makes recommendations for filename standardization
"""
import os
import logging
import sys
from PIL import Image
import imagehash
import re
from collections import defaultdict

# Set up logging
logging.basicConfig(level=logging.INFO,
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                   stream=sys.stdout)
logger = logging.getLogger("check_duplicates")

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

def extract_lottery_type(filename):
    """Extract lottery type from filename"""
    # Pattern matching for common lottery type names in filenames
    patterns = [
        (r'powerball_plus', 'PowerBall Plus'),
        (r'powerball', 'PowerBall'),
        (r'daily_lotto', 'Daily Lotto'),
        (r'lotto_plus_1', 'Lotto Plus 1'),
        (r'lotto_plus_2', 'Lotto Plus 2'),
        (r'lotto', 'Lotto')
    ]
    
    filename_lower = filename.lower()
    
    for pattern, lottery_type in patterns:
        if re.search(pattern, filename_lower):
            return lottery_type
    
    return None

def analyze_attached_assets():
    """Analyze images in attached_assets folder for duplicates"""
    logger.info("Analyzing attached_assets for duplicate screenshots")
    
    # Dictionary to group images by hash
    image_hashes = defaultdict(list)
    assets_dir = os.path.join(os.getcwd(), 'attached_assets')
    
    # Valid image extensions
    image_extensions = ('.png', '.jpg', '.jpeg', '.gif')
    
    # Process all image files in attached_assets directory
    count = 0
    for filename in os.listdir(assets_dir):
        if filename.lower().endswith(image_extensions):
            path = os.path.join(assets_dir, filename)
            image_hash = compute_image_hash(path)
            
            if image_hash:
                count += 1
                # Get lottery type from filename
                lottery_type = extract_lottery_type(filename)
                
                image_hashes[str(image_hash)].append({
                    'path': path,
                    'filename': filename,
                    'lottery_type': lottery_type
                })
    
    logger.info(f"Processed {count} images in attached_assets")
    
    # Find duplicate groups (same hash, different filenames)
    duplicates = []
    for hash_value, images in image_hashes.items():
        if len(images) > 1:
            logger.info(f"Found potential duplicate group with hash {hash_value}")
            logger.info(f"Images: {[img['filename'] for img in images]}")
            duplicates.append(images)
    
    return duplicates

def analyze_powerball_duplicates(duplicates):
    """Analyze PowerBall vs PowerBall Plus duplicates"""
    for duplicate_group in duplicates:
        # Extract lottery types in this group
        lottery_types = set(image.get('lottery_type') for image in duplicate_group 
                           if image.get('lottery_type'))
        
        # Check if both PowerBall and PowerBall Plus exist in the group
        if 'PowerBall' in lottery_types and 'PowerBall Plus' in lottery_types:
            logger.info(f"Found PowerBall/PowerBall Plus duplicate group:")
            
            # List all files in the group
            for image in duplicate_group:
                logger.info(f"  {image['filename']} - Type: {image['lottery_type']}")
            
            # Check image content to determine if it's truly PowerBall or PowerBall Plus
            logger.info("ACTION: Review these images as they may be miscategorized")
            logger.info("Look for 'POWERBALL PLUS' text in the screenshot to determine if it's Plus or not")

def main():
    """Main execution function"""
    logger.info("Starting duplicate screenshot checker")
    
    # Find duplicate screenshots
    duplicate_groups = analyze_attached_assets()
    logger.info(f"Found {len(duplicate_groups)} potential duplicate groups")
    
    # Analyze PowerBall/PowerBall Plus duplicates
    if duplicate_groups:
        analyze_powerball_duplicates(duplicate_groups)
    
    logger.info("Analysis complete")

if __name__ == "__main__":
    main()