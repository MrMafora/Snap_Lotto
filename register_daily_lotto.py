#!/usr/bin/env python3
"""
Script to register the Daily Lotto screenshot in the database.
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
logger = logging.getLogger("register_daily_lotto")

SCREENSHOT_DIR = os.path.join(os.getcwd(), 'screenshots')

def register_daily_lotto():
    """Register the Daily Lotto screenshot in the database."""
    with app.app_context():
        # Look for the Daily Lotto file
        daily_lotto_file = None
        for filename in os.listdir(SCREENSHOT_DIR):
            if "Daily_Lotto" in filename and filename.endswith(".html"):
                daily_lotto_file = filename
                break
        
        if not daily_lotto_file:
            logger.error("No Daily Lotto screenshot found")
            return False
        
        filepath = os.path.join(SCREENSHOT_DIR, daily_lotto_file)
        url = "https://www.nationallottery.co.za/results/daily-lotto"
        lottery_type = "Daily Lotto"
        
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
            logger.info(f"Successfully registered Daily Lotto with ID {screenshot.id}")
            return True
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error registering Daily Lotto: {str(e)}")
            return False

if __name__ == "__main__":
    logger.info("Starting Daily Lotto registration")
    success = register_daily_lotto()
    if success:
        logger.info("✅ Daily Lotto registration complete")
    else:
        logger.error("❌ Failed to register Daily Lotto")
    logger.info("Process complete")