#!/usr/bin/env python3
"""
Script to register the Powerball Plus screenshot in the database.
"""
import os
import sys
import logging
from main import app
from models import db, Screenshot

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger("register_powerball_plus")

SCREENSHOT_DIR = os.path.join(os.getcwd(), 'screenshots')

def register_powerball_plus():
    """Register the Powerball Plus screenshot in the database."""
    with app.app_context():
        # Look for the Powerball Plus file
        powerball_plus_file = None
        for filename in os.listdir(SCREENSHOT_DIR):
            if "Powerball_Plus" in filename and filename.endswith(".html"):
                powerball_plus_file = filename
                break
        
        if not powerball_plus_file:
            logger.error("No Powerball Plus screenshot found")
            return False
        
        filepath = os.path.join(SCREENSHOT_DIR, powerball_plus_file)
        url = "https://www.nationallottery.co.za/results/powerball-plus"
        lottery_type = "Powerball Plus"
        
        # Check if it's already in the database
        existing = Screenshot.query.filter_by(path=filepath).first()
        if existing:
            logger.info(f"Screenshot already in database with ID {existing.id}")
            return True
        
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
            logger.info(f"Successfully registered Powerball Plus with ID {screenshot.id}")
            return True
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error registering Powerball Plus: {str(e)}")
            return False

if __name__ == "__main__":
    logger.info("Starting Powerball Plus registration")
    success = register_powerball_plus()
    if success:
        logger.info("✅ Powerball Plus registration complete")
    else:
        logger.error("❌ Failed to register Powerball Plus")
    logger.info("Process complete")