#!/usr/bin/env python3
"""
Script to update URLs in the database and verify they are correctly configured
for the National Lottery website. This script will also test each URL to ensure
we can successfully capture screenshots.

This script:
1. Verifies all URLs in the database are from nationallottery.co.za
2. Updates any incorrect URLs to use the correct domain
3. Tests each URL with the specialized National Lottery capture function
4. Reports on the success of each capture attempt
"""
import os
import sys
import logging
import time
from datetime import datetime
import random

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# Import required modules
try:
    from flask import Flask
    from models import db, Screenshot, ScheduleConfig
    from sqlalchemy import and_, or_, not_
    # Import the specialized National Lottery capture function
    from national_lottery_capture import capture_national_lottery_url
except ImportError as e:
    logger.error(f"Import error: {str(e)}")
    sys.exit(1)

# Define the correct URLs for the National Lottery website
CORRECT_URLS = {
    # Historical data URLs
    'Lotto': 'https://www.nationallottery.co.za/lotto-history',
    'Lotto Plus 1': 'https://www.nationallottery.co.za/lotto-plus-1-history',
    'Lotto Plus 2': 'https://www.nationallottery.co.za/lotto-plus-2-history',
    'Powerball': 'https://www.nationallottery.co.za/powerball-history',
    'Powerball Plus': 'https://www.nationallottery.co.za/powerball-plus-history',
    'Daily Lotto': 'https://www.nationallottery.co.za/daily-lotto-history',
    
    # Current results URLs
    'Lotto Results': 'https://www.nationallottery.co.za/results/lotto',
    'Lotto Plus 1 Results': 'https://www.nationallottery.co.za/results/lotto-plus-1-results',
    'Lotto Plus 2 Results': 'https://www.nationallottery.co.za/results/lotto-plus-2-results',
    'Powerball Results': 'https://www.nationallottery.co.za/results/powerball',
    'Powerball Plus Results': 'https://www.nationallottery.co.za/results/powerball-plus',
    'Daily Lotto Results': 'https://www.nationallottery.co.za/results/daily-lotto'
}

def create_app_context():
    """Create and return a Flask app context."""
    try:
        from main import app
        return app.app_context()
    except Exception as e:
        logger.error(f"Error creating app context: {str(e)}")
        return None

def verify_and_update_urls():
    """
    Verify that all URLs in the database are from the National Lottery website,
    and update any incorrect URLs.
    
    Returns:
        int: Number of URLs updated
    """
    with create_app_context():
        # Get all schedule configs
        all_configs = db.session.query(ScheduleConfig).all()
        logger.info(f"Found {len(all_configs)} scheduled configurations")
        
        updated_count = 0
        for config in all_configs:
            lottery_type = config.lottery_type
            
            # Check if this is a known lottery type
            if lottery_type in CORRECT_URLS:
                correct_url = CORRECT_URLS[lottery_type]
                
                # Check if the URL is already correct
                if config.url != correct_url:
                    # Update the URL
                    old_url = config.url
                    config.url = correct_url
                    logger.info(f"Updated URL for {lottery_type}: {old_url} -> {correct_url}")
                    updated_count += 1
            else:
                logger.warning(f"Unknown lottery type: {lottery_type}")
        
        # Commit changes if any were made
        if updated_count > 0:
            db.session.commit()
            logger.info(f"Successfully updated {updated_count} URLs")
        else:
            logger.info("No URLs needed updating")
        
        return updated_count

def test_all_urls():
    """
    Test all URLs with the specialized National Lottery capture function.
    
    Returns:
        tuple: (success_count, total_count)
    """
    with create_app_context():
        # Get all schedule configs
        all_configs = db.session.query(ScheduleConfig).all()
        logger.info(f"Testing {len(all_configs)} URLs...")
        
        success_count = 0
        total_count = len(all_configs)
        
        # Test each URL
        for config in all_configs:
            lottery_type = config.lottery_type
            url = config.url
            
            logger.info(f"Testing URL for {lottery_type}: {url}")
            
            # Try to capture the URL
            success, html_path, img_path = capture_national_lottery_url(url, lottery_type)
            
            if success:
                logger.info(f"Successfully captured {lottery_type}")
                success_count += 1
            else:
                logger.error(f"Failed to capture {lottery_type}")
            
            # Add a delay between captures to avoid detection
            if config != all_configs[-1]:  # Skip delay after the last URL
                delay = random.uniform(10, 15)
                logger.info(f"Waiting {delay:.1f} seconds before next capture...")
                time.sleep(delay)
        
        logger.info(f"Successfully captured {success_count} out of {total_count} URLs")
        return success_count, total_count

def clear_all_screenshots():
    """
    Clear all screenshot records from the database.
    
    Returns:
        int: Number of screenshots deleted
    """
    with create_app_context():
        # Get count of all screenshots
        count = db.session.query(Screenshot).count()
        logger.info(f"Found {count} screenshots to delete")
        
        # Delete all screenshots
        db.session.query(Screenshot).delete()
        db.session.commit()
        logger.info(f"Successfully deleted {count} screenshots")
        return count

def main():
    """Main function."""
    import argparse
    
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='Update and test URLs for National Lottery website')
    parser.add_argument('--verify-only', action='store_true', help='Only verify URLs, skip interactive prompts')
    parser.add_argument('--clear-all', action='store_true', help='Clear all existing screenshots')
    parser.add_argument('--test-all', action='store_true', help='Test all URLs with capture function')
    args = parser.parse_args()
    
    logger.info("Starting URL verification and testing")
    
    # Verify and update URLs
    updated_count = verify_and_update_urls()
    logger.info(f"Updated {updated_count} URLs")
    
    # Only proceed with interactive prompts if verify-only not set
    if args.verify_only:
        logger.info("Verify-only mode: skipping screenshot clearing and testing")
        return
        
    # Handle screenshot clearing
    if args.clear_all:
        clear_all_screenshots()
    else:
        # Ask if we should clear all screenshots
        response = input("Do you want to clear all existing screenshots? (y/n): ")
        if response.lower() == 'y':
            clear_all_screenshots()
    
    # Handle URL testing
    if args.test_all:
        success_count, total_count = test_all_urls()
        logger.info(f"Successfully captured {success_count} out of {total_count} URLs")
    else:
        # Ask if we should test all URLs
        response = input("Do you want to test all URLs with the specialized capture function? (y/n): ")
        if response.lower() == 'y':
            success_count, total_count = test_all_urls()
            logger.info(f"Successfully captured {success_count} out of {total_count} URLs")
    
    logger.info("URL verification and testing complete")

if __name__ == "__main__":
    main()