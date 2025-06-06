#!/usr/bin/env python3
"""
Test Google Gemini workflow and compare extraction results with existing data
"""

import os
import sys
import logging
from datetime import datetime
from gemini_automation_controller import GeminiAutomationController
from models import LotteryResult, db
from main import app

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def get_existing_lottery_data():
    """Get current authentic lottery data from database"""
    with app.app_context():
        results = LotteryResult.query.order_by(LotteryResult.created_at.desc()).limit(10).all()
        
        logger.info(f"Found {len(results)} existing lottery results in database:")
        for result in results:
            numbers = result.get_numbers_list() if hasattr(result, 'get_numbers_list') else result.numbers
            bonus = result.get_bonus_numbers_list() if hasattr(result, 'get_bonus_numbers_list') else result.bonus_numbers
            logger.info(f"  {result.lottery_type}: Draw {result.draw_number} - {numbers} + {bonus}")
        
        return results

def test_gemini_extraction():
    """Test Google Gemini extraction on available screenshots"""
    logger.info("=== TESTING GOOGLE GEMINI EXTRACTION ===")
    
    # Check if we have screenshots to process
    screenshot_dir = "screenshots"
    if not os.path.exists(screenshot_dir):
        logger.warning(f"Screenshot directory {screenshot_dir} not found")
        return
    
    screenshot_files = [f for f in os.listdir(screenshot_dir) if f.endswith(('.png', '.jpg', '.jpeg'))]
    if not screenshot_files:
        logger.warning("No screenshot files found for testing")
        return
    
    logger.info(f"Found {len(screenshot_files)} screenshot files:")
    for file in screenshot_files[:5]:  # Show first 5
        logger.info(f"  {file}")
    
    # Initialize Gemini automation controller
    controller = GeminiAutomationController()
    
    # Test step 3: Process screenshots with Google Gemini
    logger.info("Testing Google Gemini processing on existing screenshots...")
    try:
        controller.step_3_process_with_gemini()
        logger.info("Google Gemini processing completed successfully")
    except Exception as e:
        logger.error(f"Error in Google Gemini processing: {str(e)}")
        return
    
    # Get new results after processing
    logger.info("Checking for new extraction results...")
    with app.app_context():
        new_results = LotteryResult.query.order_by(LotteryResult.created_at.desc()).limit(5).all()
        
        logger.info(f"Latest {len(new_results)} results after Gemini processing:")
        for result in new_results:
            numbers = result.get_numbers_list() if hasattr(result, 'get_numbers_list') else result.numbers
            bonus = result.get_bonus_numbers_list() if hasattr(result, 'get_bonus_numbers_list') else result.bonus_numbers
            logger.info(f"  {result.lottery_type}: Draw {result.draw_number} - {numbers} + {bonus}")
            logger.info(f"    Date: {result.draw_date}, Source: {result.source_url}")

def compare_extraction_accuracy():
    """Compare Google Gemini extraction results with known authentic data"""
    logger.info("=== COMPARING EXTRACTION ACCURACY ===")
    
    # Known authentic lottery data from our database
    authentic_data = {
        "LOTTO": {
            "draw_number": "2547",
            "numbers": [12, 34, 8, 52, 36, 24],
            "bonus_numbers": [26]
        },
        "PowerBall": {
            "draw_number": "1621", 
            "numbers": [50, 5, 47, 40, 26],
            "bonus_numbers": [20]
        },
        "Daily Lotto": {
            "draw_number": "2574",
            "numbers": [7, 27, 35, 22, 15],
            "bonus_numbers": []
        }
    }
    
    with app.app_context():
        for lottery_type, expected in authentic_data.items():
            # Find matching result in database
            result = LotteryResult.query.filter_by(
                lottery_type=lottery_type,
                draw_number=expected["draw_number"]
            ).first()
            
            if result:
                # Get numbers from database result
                db_numbers = result.get_numbers_list() if hasattr(result, 'get_numbers_list') else result.numbers
                db_bonus = result.get_bonus_numbers_list() if hasattr(result, 'get_bonus_numbers_list') else result.bonus_numbers
                
                # Compare numbers
                numbers_match = db_numbers == expected["numbers"]
                bonus_match = db_bonus == expected["bonus_numbers"]
                
                logger.info(f"{lottery_type} Draw {expected['draw_number']}:")
                logger.info(f"  Expected: {expected['numbers']} + {expected['bonus_numbers']}")
                logger.info(f"  Database: {db_numbers} + {db_bonus}")
                logger.info(f"  Accuracy: Numbers={numbers_match}, Bonus={bonus_match}")
                
                if numbers_match and bonus_match:
                    logger.info(f"  ✓ PERFECT MATCH for {lottery_type}")
                else:
                    logger.warning(f"  ✗ MISMATCH for {lottery_type}")
            else:
                logger.warning(f"No result found for {lottery_type} draw {expected['draw_number']}")

def main():
    """Main test function"""
    logger.info("Starting Google Gemini workflow test...")
    
    # Get existing data for comparison
    existing_data = get_existing_lottery_data()
    
    # Test Google Gemini extraction
    test_gemini_extraction()
    
    # Compare accuracy
    compare_extraction_accuracy()
    
    logger.info("Google Gemini workflow test completed")

if __name__ == "__main__":
    main()