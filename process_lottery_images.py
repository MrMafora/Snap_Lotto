"""
Process lottery images with Claude 3 Opus to extract lottery data

This script processes all unprocessed screenshots in the database using 
Claude 3 Opus for image analysis, then saves the extracted data to the database.
"""
import os
import sys
import logging
import argparse
from datetime import datetime, timedelta
import time

# Set up logging
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Ensure we're in the correct working directory
os.chdir(os.path.dirname(os.path.abspath(__file__)))

# Add the current directory to the path so we can import modules
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import modules after setting up path
from flask import Flask
from config import Config
from models import db, Screenshot, LotteryResult, APIRequestLog
import ocr_processor
import data_aggregator

def create_app():
    """Create a Flask app for database access"""
    app = Flask(__name__)
    app.config.from_object(Config)
    db.init_app(app)
    return app

def get_unprocessed_screenshots(app, limit=None, days=None):
    """
    Get all unprocessed screenshots from the database
    
    Args:
        app: Flask app
        limit (int, optional): Maximum number of screenshots to process
        days (int, optional): Only process screenshots from the last N days
        
    Returns:
        list: List of Screenshot objects
    """
    with app.app_context():
        query = db.session.query(Screenshot).filter(Screenshot.processed == False)
        
        # Add date filter if specified
        if days:
            cutoff_date = datetime.utcnow() - timedelta(days=days)
            query = query.filter(Screenshot.timestamp >= cutoff_date)
            
        # Order by timestamp (oldest first)
        query = query.order_by(Screenshot.timestamp.asc())
        
        # Add limit if specified
        if limit:
            query = query.limit(limit)
            
        return query.all()

def process_screenshots(app, screenshots):
    """
    Process a list of screenshots with Claude 3 Opus
    
    Args:
        app: Flask app
        screenshots (list): List of Screenshot objects
        
    Returns:
        dict: Statistics about processing
    """
    stats = {
        "total": len(screenshots),
        "success": 0,
        "error": 0,
        "processed_ids": [],
        "error_ids": []
    }
    
    with app.app_context():
        for idx, screenshot in enumerate(screenshots):
            logger.info(f"Processing screenshot {idx+1}/{stats['total']}: ID {screenshot.id}, URL: {screenshot.url}")
            
            # Check if the screenshot file exists
            if not os.path.exists(screenshot.path):
                logger.error(f"Screenshot file not found: {screenshot.path}")
                stats["error"] += 1
                stats["error_ids"].append(screenshot.id)
                continue
                
            try:
                # Process the screenshot with Claude 3 Opus
                result = ocr_processor.process_screenshot(
                    screenshot_path=screenshot.path,
                    lottery_type=screenshot.lottery_type
                )
                
                # Check if we got a valid result
                if not result or "error" in result:
                    logger.error(f"Error processing screenshot {screenshot.id}: {result.get('error', 'Unknown error')}")
                    stats["error"] += 1
                    stats["error_ids"].append(screenshot.id)
                    continue
                    
                # Save results to database
                saved_records = data_aggregator.aggregate_data(
                    extracted_data=result,
                    lottery_type=screenshot.lottery_type,
                    source_url=screenshot.url
                )
                
                if saved_records:
                    # Mark screenshot as processed
                    screenshot.processed = True
                    db.session.commit()
                    
                    logger.info(f"Successfully processed screenshot {screenshot.id} and saved {len(saved_records)} records")
                    stats["success"] += 1
                    stats["processed_ids"].append(screenshot.id)
                else:
                    logger.warning(f"No records saved for screenshot {screenshot.id}")
                    stats["error"] += 1
                    stats["error_ids"].append(screenshot.id)
                    
                # Add a small delay to avoid rate limiting
                time.sleep(1)
                
            except Exception as e:
                logger.error(f"Exception processing screenshot {screenshot.id}: {str(e)}")
                stats["error"] += 1
                stats["error_ids"].append(screenshot.id)
                
    return stats

def main():
    """Main function"""
    parser = argparse.ArgumentParser(description='Process lottery screenshots with Claude 3 Opus')
    parser.add_argument('--limit', type=int, help='Maximum number of screenshots to process')
    parser.add_argument('--days', type=int, help='Only process screenshots from the last N days')
    args = parser.parse_args()
    
    # Make sure we have the API key
    api_key = os.environ.get('ANTHROPIC_API_KEY')
    if not api_key:
        logger.error("ANTHROPIC_API_KEY environment variable not set. Cannot proceed.")
        sys.exit(1)
        
    # Create Flask app
    app = create_app()
    
    # Get unprocessed screenshots
    screenshots = get_unprocessed_screenshots(app, limit=args.limit, days=args.days)
    if not screenshots:
        logger.info("No unprocessed screenshots found.")
        return
        
    logger.info(f"Found {len(screenshots)} unprocessed screenshots")
    
    # Process screenshots
    stats = process_screenshots(app, screenshots)
    
    # Log results
    logger.info(f"Processing complete. Results: {stats['success']} successful, {stats['error']} failed")
    logger.info(f"Successfully processed IDs: {stats['processed_ids']}")
    if stats["error_ids"]:
        logger.info(f"Failed IDs: {stats['error_ids']}")
        
if __name__ == "__main__":
    main()