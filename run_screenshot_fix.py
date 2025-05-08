"""
Run Screenshot Fix

This script:
1. Loads all screenshot records from the database
2. Creates placeholder images for all missing screenshots
3. Updates the database with the correct paths
"""
import os
import sys
import logging
from datetime import datetime
from PIL import Image, ImageDraw, ImageFont

# Set up logging
logging.basicConfig(level=logging.INFO,
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Constants
SCREENSHOT_DIR = 'screenshots'

def ensure_directory_exists(directory):
    """Ensure a directory exists"""
    try:
        os.makedirs(directory, exist_ok=True)
        return True
    except Exception as e:
        logger.error(f"Error creating directory {directory}: {str(e)}")
        return False

def create_placeholder_image(lottery_type, output_path, timestamp=None, width=800, height=600):
    """Create a placeholder image with lottery information"""
    try:
        # Make sure directory exists
        dir_path = os.path.dirname(output_path)
        ensure_directory_exists(dir_path)
        
        # Use timestamp or current time
        ts = timestamp or datetime.now()
        
        # Create a white image
        image = Image.new('RGB', (width, height), color=(255, 255, 255))
        draw = ImageDraw.Draw(image)
        
        # Load default font
        font = ImageFont.load_default()
        small_font = font
        
        # Draw header with lottery-themed colors
        draw.rectangle(((0, 0), (width, 60)), fill=(0, 51, 102))
        draw.text((20, 15), f"{lottery_type} Screenshot", fill=(255, 255, 255), font=font)
        
        # Draw timestamp
        timestamp_str = ts.strftime("%Y-%m-%d %H:%M:%S")
        draw.text((20, 70), f"Generated: {timestamp_str}", fill=(0, 0, 0), font=small_font)
        
        # Draw message
        draw.text((20, 120), "This is a placeholder image.", fill=(0, 0, 0), font=small_font)
        draw.text((20, 140), "The original screenshot was not available.", fill=(0, 0, 0), font=small_font)
        
        # Draw lottery-colored dots at the bottom
        draw.ellipse(((100, 500), (130, 530)), fill=(204, 0, 0))  # Red
        draw.ellipse(((150, 500), (180, 530)), fill=(0, 102, 204))  # Blue
        draw.ellipse(((200, 500), (230, 530)), fill=(0, 153, 0))  # Green
        draw.ellipse(((250, 500), (280, 530)), fill=(255, 204, 0))  # Yellow
        draw.ellipse(((300, 500), (330, 530)), fill=(102, 0, 204))  # Purple
        draw.ellipse(((350, 500), (380, 530)), fill=(255, 102, 0))  # Orange
        
        # Save the image
        image.save(output_path, format="PNG")
        logger.info(f"Created placeholder image at {output_path}")
        return True
        
    except Exception as e:
        logger.error(f"Error creating placeholder image: {str(e)}")
        return False

def fix_all_screenshots():
    """Fix all screenshot records in the database"""
    try:
        from main import app
        from models import Screenshot, db
        
        # Ensure screenshots directory exists
        ensure_directory_exists(SCREENSHOT_DIR)
        
        results = {
            'total': 0,
            'fixed': 0,
            'failed': 0,
            'skipped': 0
        }
        
        with app.app_context():
            # Get all screenshots
            screenshots = Screenshot.query.all()
            results['total'] = len(screenshots)
            logger.info(f"Found {len(screenshots)} screenshot records in database")
            
            for screenshot in screenshots:
                # Generate new path in the screenshots directory
                timestamp_str = screenshot.timestamp.strftime('%Y%m%d_%H%M%S')
                filename = f"{timestamp_str}_{screenshot.lottery_type.replace(' ', '_').lower()}.png"
                new_path = os.path.join(SCREENSHOT_DIR, filename)
                
                if os.path.exists(new_path) and os.path.getsize(new_path) > 0:
                    # If a valid file already exists, update the path and skip creation
                    logger.info(f"Screenshot already exists at {new_path}")
                    screenshot.path = new_path
                    results['skipped'] += 1
                else:
                    # Create a new placeholder image
                    success = create_placeholder_image(
                        screenshot.lottery_type,
                        new_path,
                        screenshot.timestamp
                    )
                    
                    if success:
                        # Update the database with the new path
                        screenshot.path = new_path
                        results['fixed'] += 1
                    else:
                        results['failed'] += 1
            
            # Commit all changes
            db.session.commit()
            logger.info(f"Database updated successfully")
            
        return results
    
    except Exception as e:
        logger.error(f"Error fixing screenshots: {str(e)}")
        import traceback
        traceback.print_exc()
        return {
            'total': 0,
            'fixed': 0,
            'failed': 0,
            'skipped': 0,
            'error': str(e)
        }

if __name__ == "__main__":
    logger.info("Starting screenshot fix...")
    
    try:
        # Ensure screenshots directory exists
        ensure_directory_exists(SCREENSHOT_DIR)
        
        # Fix all screenshots
        results = fix_all_screenshots()
        
        # Print results
        logger.info(f"Screenshot fix completed:")
        logger.info(f"  Total: {results['total']}")
        logger.info(f"  Fixed: {results['fixed']}")
        logger.info(f"  Failed: {results['failed']}")
        logger.info(f"  Skipped: {results['skipped']}")
        
        print(f"Screenshot fix completed:")
        print(f"  Total: {results['total']}")
        print(f"  Fixed: {results['fixed']}")
        print(f"  Failed: {results['failed']}")
        print(f"  Skipped: {results['skipped']}")
        
        # Exit with success
        sys.exit(0)
    
    except Exception as e:
        logger.error(f"Unhandled error: {str(e)}")
        print(f"Error: {str(e)}")
        sys.exit(1)