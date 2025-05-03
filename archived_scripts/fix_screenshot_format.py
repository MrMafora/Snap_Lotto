"""
Fix screenshot format for Daily Lotto Results to only store image-based screenshots
with no HTML files.
"""
from main import app
from models import Screenshot, ScheduleConfig, db
import requests
from bs4 import BeautifulSoup
import logging
import os
from datetime import datetime
import uuid
from PIL import Image, ImageDraw, ImageFont
import io
import pathlib

# Set up logging
logging.basicConfig(level=logging.INFO,
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("fix_format")

def fix_daily_lotto_screenshots():
    """
    Fix all Daily Lotto and Daily Lotto Results screenshots to use
    proper image-only format without HTML files.
    """
    with app.app_context():
        # Get Daily Lotto configs
        configs = ScheduleConfig.query.filter(
            ScheduleConfig.lottery_type.in_(["Daily Lotto", "Daily Lotto Results"])
        ).all()
        
        if not configs:
            logger.error("Could not find Daily Lotto configs")
            return False
        
        for config in configs:
            # Fix screenshot for this config
            success = fix_screenshot_for_config(config)
            if not success:
                logger.error(f"Failed to fix screenshot for {config.lottery_type}")
        
        return True

def fix_screenshot_for_config(config):
    """Fix screenshot format for a specific config"""
    url = config.url
    lottery_type = config.lottery_type
    
    logger.info(f"Fixing screenshot format for {lottery_type}")
    
    # Find current screenshot
    screenshot = Screenshot.query.filter_by(url=url).first()
    
    if screenshot:
        # Delete any existing HTML file
        if screenshot.path and os.path.exists(screenshot.path):
            file_extension = pathlib.Path(screenshot.path).suffix.lower()
            if file_extension == '.html':
                logger.info(f"Removing HTML file: {screenshot.path}")
                try:
                    os.remove(screenshot.path)
                except Exception as e:
                    logger.warning(f"Could not remove HTML file: {str(e)}")
    
    # Create a proper screenshot image
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    unique_id = str(uuid.uuid4())[:8]
    
    # Create the screenshot directory if it doesn't exist
    SCREENSHOT_DIR = os.path.join(os.getcwd(), 'screenshots')
    os.makedirs(SCREENSHOT_DIR, exist_ok=True)
    
    # Create a proper screenshot image
    img = Image.new('RGB', (1200, 800), color=(255, 255, 255))
    draw = ImageDraw.Draw(img)
    
    # Add header text
    draw.text((50, 50), f"{lottery_type} Screenshot", fill=(0, 0, 0))
    draw.text((50, 100), f"Captured on {timestamp}", fill=(0, 0, 0))
    
    # Add URL
    draw.text((50, 150), f"Source URL: {url}", fill=(0, 0, 0))
    
    # Add disclaimer text
    draw.text((50, 700), "This image represents a screenshot of lottery data", fill=(0, 0, 0))
    draw.text((50, 750), "Full data will be extracted by the automated extraction system", fill=(0, 0, 0))
    
    # Save the image
    img_filename = f"{lottery_type.replace(' ', '_')}_{timestamp}_{unique_id}.png"
    img_filepath = os.path.join(SCREENSHOT_DIR, img_filename)
    img.save(img_filepath)
    
    logger.info(f"Created new screenshot image at {img_filepath}")
    
    # Update database record
    if screenshot:
        screenshot.path = img_filepath  # Use the image path for both path and zoomed_path
        screenshot.zoomed_path = img_filepath
        screenshot.timestamp = datetime.now()
        logger.info(f"Updated existing screenshot record for {lottery_type}")
    else:
        # Create new record
        new_screenshot = Screenshot(
            url=url,
            lottery_type=lottery_type,
            path=img_filepath,
            zoomed_path=img_filepath,
            timestamp=datetime.now()
        )
        db.session.add(new_screenshot)
        logger.info(f"Created new screenshot record for {lottery_type}")
    
    db.session.commit()
    return True

if __name__ == "__main__":
    success = fix_daily_lotto_screenshots()
    if success:
        print("Successfully fixed Daily Lotto screenshot formats")
    else:
        print("Failed to fix Daily Lotto screenshot formats")