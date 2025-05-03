#!/usr/bin/env python3
"""
Script to register captured screenshots in the database.
"""
import os
import sys
import logging
from main import app
from models import db, Screenshot
from data_aggregator import normalize_lottery_type

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger("register_screenshots")

SCREENSHOT_DIR = os.path.join(os.getcwd(), 'screenshots')

def register_screenshots():
    """Register all HTML screenshots in the directory to the database."""
    with app.app_context():
        # Get all HTML files in the screenshots directory
        html_files = [f for f in os.listdir(SCREENSHOT_DIR) if f.endswith('.html')]
        logger.info(f"Found {len(html_files)} HTML files in {SCREENSHOT_DIR}")
        
        # Get the paths of screenshots already in the database
        existing_paths = [row[0] for row in db.session.query(Screenshot.path).all()]
        logger.info(f"Found {len(existing_paths)} existing screenshot records in database")
        
        # Map lottery types to URLs
        lottery_urls = {
            "Lotto": "https://www.nationallottery.co.za/results/lotto",
            "Lotto Plus 1": "https://www.nationallottery.co.za/results/lotto-plus-1-results",
            "Lotto Plus 2": "https://www.nationallottery.co.za/results/lotto-plus-2-results",
            "Powerball": "https://www.nationallottery.co.za/results/powerball",
            "Powerball Plus": "https://www.nationallottery.co.za/results/powerball-plus", 
            "Daily Lotto": "https://www.nationallottery.co.za/results/daily-lotto"
        }
        
        # Register new screenshots
        new_count = 0
        for filename in html_files:
            # Construct full path
            filepath = os.path.join(SCREENSHOT_DIR, filename)
            
            # Skip if already in database
            if filepath in existing_paths:
                logger.info(f"Skipping {filename} - already in database")
                continue
            
            # Determine lottery type from filename
            lottery_type = None
            for lt in lottery_urls.keys():
                if lt.replace(" ", "_") in filename:
                    lottery_type = lt
                    break
            
            if not lottery_type:
                logger.warning(f"Could not determine lottery type for {filename}, skipping")
                continue
            
            # Determine URL based on lottery type
            url = lottery_urls.get(lottery_type)
            if not url:
                logger.warning(f"No URL found for lottery type {lottery_type}, skipping")
                continue
            
            logger.info(f"Registering {filename} as {lottery_type} from {url}")
            
            try:
                # Create database record
                screenshot = Screenshot(
                    lottery_type=lottery_type,
                    url=url,
                    path=filepath,
                    processed=False
                )
                db.session.add(screenshot)
                db.session.commit()
                new_count += 1
                logger.info(f"Successfully registered {filename} with ID {screenshot.id}")
            except Exception as e:
                db.session.rollback()
                logger.error(f"Error registering {filename}: {str(e)}")
        
        logger.info(f"Registered {new_count} new screenshots")
        
        # Check if we have one screenshot for each normalized lottery type
        normalized_types = set()
        for row in db.session.query(Screenshot.lottery_type).all():
            normalized_types.add(normalize_lottery_type(row[0]))
        
        all_normalized = {"Lottery", "Lottery Plus 1", "Lottery Plus 2", "Powerball", "Powerball Plus", "Daily Lottery"}
        missing = all_normalized - normalized_types
        
        if missing:
            logger.warning(f"Still missing normalized lottery types: {missing}")
        else:
            logger.info("✅ Have all required normalized lottery types!")

if __name__ == "__main__":
    logger.info("Starting screenshot registration")
    register_screenshots()
    logger.info("Registration complete")