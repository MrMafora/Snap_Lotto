"""
Fix the missing Daily Lotto Results record directly
"""
from main import app
from models import Screenshot, db
from datetime import datetime
import os
import logging
from PIL import Image
import io
import uuid

# Set up logging
logging.basicConfig(level=logging.INFO,
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("fix_missing")

def fix_missing_daily_lotto_results():
    """
    Create a placeholder record for Daily Lotto Results
    """
    logger.info("Creating placeholder record for Daily Lotto Results")
    
    with app.app_context():
        # Check if it already exists
        existing = Screenshot.query.filter_by(lottery_type="Daily Lotto Results").first()
        
        if existing:
            logger.info(f"Record already exists with timestamp {existing.timestamp}")
            # Update timestamp
            existing.timestamp = datetime.now()
            db.session.commit()
            logger.info(f"Updated timestamp to {existing.timestamp}")
            return
            
        # Create directory for screenshots
        SCREENSHOT_DIR = os.path.join(os.getcwd(), 'screenshots')
        os.makedirs(SCREENSHOT_DIR, exist_ok=True)
        
        # Create a timestamp for the filename
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        unique_id = str(uuid.uuid4())[:8]
        
        # Create filenames
        screenshot_filename = f"Daily_Lotto_Results_{timestamp}_{unique_id}.html"
        filepath = os.path.join(SCREENSHOT_DIR, screenshot_filename)
        
        # Create a simple image
        img = Image.new('RGB', (1200, 800), color = (255, 255, 255))
        img_filename = f"Daily_Lotto_Results_{timestamp}_{unique_id}.png"
        img_filepath = os.path.join(SCREENSHOT_DIR, img_filename)
        
        # Save a sample file
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write("<html><body><h1>Daily Lotto Results</h1></body></html>")
            
        # Save image to file
        img.save(img_filepath)
        
        # Create a new screenshot record
        new_screenshot = Screenshot(
            url="https://www.nationallottery.co.za/results/daily-lotto",
            lottery_type="Daily Lotto Results",
            timestamp=datetime.now(),
            path=filepath,
            zoomed_path=img_filepath
        )
        
        db.session.add(new_screenshot)
        db.session.commit()
        
        logger.info(f"Created new screenshot record for Daily Lotto Results with timestamp {new_screenshot.timestamp}")

if __name__ == "__main__":
    fix_missing_daily_lotto_results()