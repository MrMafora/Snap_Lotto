#!/usr/bin/env python3
"""
Process the latest fresh screenshots captured on August 26, 2025.
Extract and save new lottery results to the database.
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
            logging.FileHandler('process_latest_fresh_results.log'),
            logging.StreamHandler()
        ]
    )

def main():
    """Main function to process fresh screenshots."""
    setup_logging()
    logger = logging.getLogger(__name__)
    
    logger.info("=== PROCESSING FRESH AUGUST 26 LOTTERY SCREENSHOTS ===")
    
    # Fresh screenshots captured on August 26, 2025 at 20:39
    fresh_screenshots = [
        ("screenshots/20250826_203900_lotto.png", "LOTTO"),
        ("screenshots/20250826_203900_lotto_plus_1.png", "LOTTO PLUS 1"),
        ("screenshots/20250826_203900_lotto_plus_2.png", "LOTTO PLUS 2"),
        ("screenshots/20250826_203900_powerball.png", "POWERBALL"),
        ("screenshots/20250826_203900_powerball_plus.png", "POWERBALL PLUS"),
        ("screenshots/20250826_203900_daily_lotto.png", "DAILY LOTTO")
    ]
    
    # Initialize AI processor
    try:
        processor = CompleteLotteryProcessor()
        logger.info("AI Lottery Processor initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize AI processor: {e}")
        return False
    
    processed_count = 0
    new_results = []
    
    # Process each fresh screenshot
    for screenshot_path, lottery_type in fresh_screenshots:
        logger.info(f"Processing {lottery_type}: {screenshot_path}")
        
        if not os.path.exists(screenshot_path):
            logger.error(f"Screenshot not found: {screenshot_path}")
            continue
            
        try:
            # Connect to database first
            processor.connect_database()
            
            # Process screenshot with AI
            result = processor.process_single_image(screenshot_path, lottery_type)
            
            if result:
                # Save to database
                saved_id = processor.save_to_database(result)
                
                logger.info(f"✅ Successfully processed {lottery_type}")
                logger.info(f"Draw: {result.get('draw_id')}, Date: {result.get('draw_date')}")
                logger.info(f"Numbers: {result.get('winning_numbers')}, Bonus: {result.get('bonus_numbers')}")
                logger.info(f"Confidence: {result.get('extraction_confidence', 'N/A')}%")
                
                if saved_id:
                    new_results.append({
                        'type': lottery_type,
                        'draw': result.get('draw_id'),
                        'date': result.get('draw_date'),
                        'numbers': result.get('winning_numbers'),
                        'bonus': result.get('bonus_numbers')
                    })
                    
                processed_count += 1
            else:
                logger.warning(f"❌ No data extracted from {lottery_type}")
                
        except Exception as e:
            logger.error(f"Error processing {lottery_type}: {e}")
            continue
    
    logger.info(f"=== PROCESSING COMPLETE ===")
    logger.info(f"Successfully processed {processed_count} out of {len(fresh_screenshots)} lottery results")
    
    if new_results:
        logger.info("=== NEW RESULTS FOUND ===")
        for result in new_results:
            logger.info(f"{result['type']}: Draw {result['draw']} ({result['date']}) - {result['numbers']} + {result['bonus']}")
    
    return processed_count > 0

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)