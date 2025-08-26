#!/usr/bin/env python3
"""
Process missing lottery results from August 25, 2025 automation run.
The automation captured 6 screenshots but only processed Daily Lotto.
This script will process the remaining 5 screenshots.
"""

import os
import sys
import logging
from datetime import datetime

# Add the current directory to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from ai_lottery_processor import CompleteLotteryProcessor

def setup_logging():
    """Setup logging for the extraction process."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('process_missing_august25_results.log'),
            logging.StreamHandler()
        ]
    )

def main():
    """Main function to process missing screenshots."""
    setup_logging()
    logger = logging.getLogger(__name__)
    
    logger.info("=== PROCESSING MISSING AUGUST 25 LOTTERY RESULTS ===")
    
    # Screenshots captured on August 25, 2025 at 23:45:35
    missing_screenshots = [
        ("screenshots/20250825_234535_lotto.png", "LOTTO"),
        ("screenshots/20250825_234535_lotto_plus_1.png", "LOTTO PLUS 1"),
        ("screenshots/20250825_234535_lotto_plus_2.png", "LOTTO PLUS 2"),
        ("screenshots/20250825_234535_powerball.png", "POWERBALL"),
        ("screenshots/20250825_234535_powerball_plus.png", "POWERBALL PLUS")
    ]
    
    # Initialize AI processor
    try:
        processor = CompleteLotteryProcessor()
        logger.info("AI Lottery Processor initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize AI processor: {e}")
        return False
    
    processed_count = 0
    
    # Process each missing screenshot
    for screenshot_path, lottery_type in missing_screenshots:
        logger.info(f"Processing {lottery_type}: {screenshot_path}")
        
        if not os.path.exists(screenshot_path):
            logger.error(f"Screenshot not found: {screenshot_path}")
            continue
            
        try:
            # Connect to database first
            processor.connect_database()
            
            # Process screenshot with AI
            result = processor.process_single_image(screenshot_path, lottery_type)
            
            # Save to database if extraction was successful
            if result:
                processor.save_to_database(result)
            
            if result:
                logger.info(f"✅ Successfully processed {lottery_type}")
                logger.info(f"Draw: {result.get('draw_id')}, Date: {result.get('draw_date')}")
                logger.info(f"Numbers: {result.get('winning_numbers')}, Bonus: {result.get('bonus_numbers')}")
                logger.info(f"Confidence: {result.get('extraction_confidence', 'N/A')}%")
                processed_count += 1
            else:
                logger.warning(f"❌ No data extracted from {lottery_type}")
                
        except Exception as e:
            logger.error(f"Error processing {lottery_type}: {e}")
            continue
    
    logger.info(f"=== PROCESSING COMPLETE ===")
    logger.info(f"Successfully processed {processed_count} out of {len(missing_screenshots)} lottery results")
    
    return processed_count > 0

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)