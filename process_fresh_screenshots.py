#!/usr/bin/env python3
"""
Process fresh lottery screenshots with Google Gemini 2.5 Pro
Extract data from the 6 new lottery images provided by user
"""

import os
import sys
import logging
from datetime import datetime
from gemini_lottery_extractor import GeminiLotteryExtractor
from models import LotteryResult, db
from main import app

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def process_fresh_lottery_screenshots():
    """Process the 6 fresh lottery screenshots with Google Gemini 2.5 Pro"""
    logger.info("=== PROCESSING FRESH LOTTERY SCREENSHOTS WITH GOOGLE GEMINI 2.5 PRO ===")
    
    # Initialize Google Gemini extractor
    extractor = GeminiLotteryExtractor()
    
    # Screenshots to process
    screenshot_files = [
        "20250606_171929_lotto.png",
        "20250606_171942_lotto_plus_1_results.png", 
        "20250606_171954_lotto_plus_2_results.png",
        "20250606_172007_powerball.png",
        "20250606_172018_powerball_plus.png",
        "20250606_172030_daily_lotto.png"
    ]
    
    screenshots_dir = "screenshots"
    processed_count = 0
    success_count = 0
    
    for screenshot_file in screenshot_files:
        screenshot_path = os.path.join(screenshots_dir, screenshot_file)
        
        if not os.path.exists(screenshot_path):
            logger.warning(f"Screenshot not found: {screenshot_path}")
            continue
            
        logger.info(f"Processing: {screenshot_file}")
        processed_count += 1
        
        try:
            # Extract lottery data using Google Gemini 2.5 Pro
            result = extractor.process_single_image(screenshot_path)
            
            if result and result.get('success'):
                success_count += 1
                logger.info(f"✓ Successfully processed {screenshot_file}")
                logger.info(f"  Lottery Type: {result.get('lottery_type')}")
                logger.info(f"  Draw Number: {result.get('draw_number')}")
                logger.info(f"  Numbers: {result.get('main_numbers')}")
                logger.info(f"  Bonus: {result.get('bonus_numbers')}")
            else:
                logger.error(f"✗ Failed to process {screenshot_file}")
                if result:
                    logger.error(f"  Error: {result.get('error', 'Unknown error')}")
                    
        except Exception as e:
            logger.error(f"Exception processing {screenshot_file}: {str(e)}")
    
    logger.info(f"Processing complete: {success_count}/{processed_count} screenshots successfully processed")
    return success_count, processed_count

def verify_new_data_in_database():
    """Verify that new lottery data has been added to the database"""
    logger.info("=== VERIFYING NEW LOTTERY DATA IN DATABASE ===")
    
    with app.app_context():
        # Check for recent lottery results
        recent_results = LotteryResult.query.filter(
            LotteryResult.created_at >= datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        ).order_by(LotteryResult.created_at.desc()).all()
        
        logger.info(f"Found {len(recent_results)} recent lottery results:")
        
        gemini_results = 0
        for result in recent_results:
            if result.ocr_provider == 'gemini-2.5-pro':
                gemini_results += 1
                numbers = result.get_numbers_list() if hasattr(result, 'get_numbers_list') else result.numbers
                bonus = result.get_bonus_numbers_list() if hasattr(result, 'get_bonus_numbers_list') else result.bonus_numbers
                
                logger.info(f"  {result.lottery_type} Draw {result.draw_number}: {numbers} + {bonus}")
                logger.info(f"    Date: {result.draw_date}, Created: {result.created_at}")
        
        logger.info(f"Google Gemini 2.5 Pro results: {gemini_results}/{len(recent_results)}")
        
        return len(recent_results), gemini_results

def compare_with_image_data():
    """Compare extracted data with what's visible in the images"""
    logger.info("=== COMPARING EXTRACTED DATA WITH IMAGE CONTENT ===")
    
    # Expected data from the images (manually verified)
    expected_data = {
        "LOTTO": {
            "draw_number": "2547",
            "draw_date": "2025-06-04",
            "numbers": [10, 15, 24, 28, 35, 49],
            "bonus": [26]
        },
        "LOTTO PLUS 1": {
            "draw_number": "2547", 
            "draw_date": "2025-06-04",
            "numbers": [17, 40, 39, 31, 7, 43],
            "bonus": [13]
        },
        "LOTTO PLUS 2": {
            "draw_number": "2547",
            "draw_date": "2025-06-04", 
            "numbers": [6, 28, 1, 23, 26, 22],
            "bonus": [31]
        },
        "PowerBall": {
            "draw_number": "1622",
            "draw_date": "2025-06-03",
            "numbers": [30, 33, 47, 49, 26],
            "bonus": [14]
        },
        "PowerBall Plus": {
            "draw_number": "1622",
            "draw_date": "2025-06-03",
            "numbers": [14, 37, 37, 38, 30],
            "bonus": [4]
        },
        "Daily Lotto": {
            "draw_number": "2274",
            "draw_date": "2025-06-05",
            "numbers": [7, 27, 35, 22, 15],
            "bonus": []
        }
    }
    
    with app.app_context():
        accuracy_results = {}
        
        for lottery_type, expected in expected_data.items():
            # Find the latest result for this lottery type
            latest_result = LotteryResult.query.filter_by(
                lottery_type=lottery_type
            ).order_by(LotteryResult.created_at.desc()).first()
            
            if latest_result:
                db_numbers = latest_result.get_numbers_list() if hasattr(latest_result, 'get_numbers_list') else latest_result.numbers
                db_bonus = latest_result.get_bonus_numbers_list() if hasattr(latest_result, 'get_bonus_numbers_list') else latest_result.bonus_numbers
                
                numbers_match = sorted(db_numbers) == sorted(expected["numbers"])
                bonus_match = sorted(db_bonus) == sorted(expected["bonus"])
                draw_match = latest_result.draw_number == expected["draw_number"]
                
                accuracy_results[lottery_type] = {
                    'numbers_match': numbers_match,
                    'bonus_match': bonus_match,
                    'draw_match': draw_match,
                    'overall_match': numbers_match and bonus_match and draw_match
                }
                
                status = "✓ PERFECT" if accuracy_results[lottery_type]['overall_match'] else "✗ MISMATCH"
                logger.info(f"{status} - {lottery_type}:")
                logger.info(f"  Expected: Draw {expected['draw_number']} - {expected['numbers']} + {expected['bonus']}")
                logger.info(f"  Database: Draw {latest_result.draw_number} - {db_numbers} + {db_bonus}")
                logger.info(f"  Match: Numbers={numbers_match}, Bonus={bonus_match}, Draw={draw_match}")
            else:
                logger.warning(f"No database result found for {lottery_type}")
                accuracy_results[lottery_type] = {'overall_match': False}
        
        # Calculate overall accuracy
        total_lotteries = len(expected_data)
        perfect_matches = sum(1 for result in accuracy_results.values() if result.get('overall_match', False))
        overall_accuracy = (perfect_matches / total_lotteries) * 100
        
        logger.info(f"Google Gemini 2.5 Pro Overall Accuracy: {perfect_matches}/{total_lotteries} ({overall_accuracy:.1f}%)")
        
        return accuracy_results

def main():
    """Main function to process fresh screenshots and verify results"""
    logger.info("Starting Google Gemini 2.5 Pro processing of fresh lottery screenshots...")
    
    # Process fresh screenshots
    success_count, total_count = process_fresh_lottery_screenshots()
    
    # Verify new data in database
    total_results, gemini_results = verify_new_data_in_database()
    
    # Compare with expected image data
    accuracy_results = compare_with_image_data()
    
    logger.info("=== FINAL SUMMARY ===")
    logger.info(f"Screenshots processed: {success_count}/{total_count}")
    logger.info(f"Database results: {total_results} total, {gemini_results} from Google Gemini")
    
    perfect_matches = sum(1 for result in accuracy_results.values() if result.get('overall_match', False))
    logger.info(f"Accuracy verification: {perfect_matches}/{len(accuracy_results)} perfect matches")
    
    logger.info("Fresh lottery screenshot processing completed")

if __name__ == "__main__":
    main()