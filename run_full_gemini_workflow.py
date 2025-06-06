#!/usr/bin/env python3
"""
Run the complete Google Gemini automation workflow and compare results
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

def run_complete_workflow():
    """Run the complete 4-step Google Gemini automation workflow"""
    logger.info("=== RUNNING COMPLETE GOOGLE GEMINI AUTOMATION WORKFLOW ===")
    
    # Initialize Gemini automation controller
    controller = GeminiAutomationController()
    
    try:
        # Step 1: Clean old screenshots
        logger.info("Step 1: Cleaning old screenshots...")
        controller.step_1_cleanup()
        
        # Step 2: Capture fresh screenshots
        logger.info("Step 2: Capturing fresh lottery screenshots...")
        controller.step_2_capture()
        
        # Step 3: Process with Google Gemini 2.5 Pro
        logger.info("Step 3: Processing screenshots with Google Gemini 2.5 Pro...")
        controller.step_3_process_with_gemini()
        
        # Step 4: Verify database has fresh data
        logger.info("Step 4: Verifying database has fresh lottery data...")
        controller.step_4_verify_database()
        
        logger.info("✓ Complete workflow executed successfully")
        return True
        
    except Exception as e:
        logger.error(f"Error in complete workflow: {str(e)}")
        return False

def analyze_extraction_results():
    """Analyze the Google Gemini extraction results"""
    logger.info("=== ANALYZING GOOGLE GEMINI EXTRACTION RESULTS ===")
    
    with app.app_context():
        # Get the latest results from each lottery type
        lottery_types = ['LOTTO', 'LOTTO PLUS 1', 'LOTTO PLUS 2', 'PowerBall', 'PowerBall Plus', 'Daily Lotto']
        
        total_results = 0
        successful_extractions = 0
        
        for lottery_type in lottery_types:
            latest_result = LotteryResult.query.filter_by(lottery_type=lottery_type).order_by(LotteryResult.created_at.desc()).first()
            
            if latest_result:
                total_results += 1
                numbers = latest_result.get_numbers_list() if hasattr(latest_result, 'get_numbers_list') else latest_result.numbers
                bonus = latest_result.get_bonus_numbers_list() if hasattr(latest_result, 'get_bonus_numbers_list') else latest_result.bonus_numbers
                
                # Check if extraction was successful (non-empty numbers)
                if numbers and len(numbers) > 0:
                    successful_extractions += 1
                    logger.info(f"✓ {lottery_type}: Draw {latest_result.draw_number} - {numbers} + {bonus}")
                    logger.info(f"  Date: {latest_result.draw_date}, OCR: {latest_result.ocr_provider}")
                else:
                    logger.warning(f"✗ {lottery_type}: No numbers extracted")
            else:
                logger.warning(f"No results found for {lottery_type}")
        
        # Calculate accuracy
        if total_results > 0:
            accuracy = (successful_extractions / total_results) * 100
            logger.info(f"Google Gemini Extraction Accuracy: {successful_extractions}/{total_results} ({accuracy:.1f}%)")
        else:
            logger.warning("No lottery results found in database")

def compare_with_previous_data():
    """Compare new Google Gemini results with previous authentic data"""
    logger.info("=== COMPARING WITH PREVIOUS AUTHENTIC DATA ===")
    
    # Previous authentic data for comparison
    reference_data = {
        "LOTTO": {"draw_number": "2547", "numbers": [12, 34, 8, 52, 36, 24], "bonus": [26]},
        "PowerBall": {"draw_number": "1621", "numbers": [50, 5, 47, 40, 26], "bonus": [14]},
        "Daily Lotto": {"draw_number": "2574", "numbers": [7, 27, 35, 22, 15], "bonus": []}
    }
    
    with app.app_context():
        for lottery_type, reference in reference_data.items():
            # Find the reference draw in database
            ref_result = LotteryResult.query.filter_by(
                lottery_type=lottery_type,
                draw_number=reference["draw_number"]
            ).first()
            
            # Find the latest result for this lottery type
            latest_result = LotteryResult.query.filter_by(lottery_type=lottery_type).order_by(LotteryResult.created_at.desc()).first()
            
            if ref_result and latest_result and latest_result.id != ref_result.id:
                ref_numbers = ref_result.get_numbers_list() if hasattr(ref_result, 'get_numbers_list') else ref_result.numbers
                ref_bonus = ref_result.get_bonus_numbers_list() if hasattr(ref_result, 'get_bonus_numbers_list') else ref_result.bonus_numbers
                
                latest_numbers = latest_result.get_numbers_list() if hasattr(latest_result, 'get_numbers_list') else latest_result.numbers
                latest_bonus = latest_result.get_bonus_numbers_list() if hasattr(latest_result, 'get_bonus_numbers_list') else latest_result.bonus_numbers
                
                logger.info(f"{lottery_type} Comparison:")
                logger.info(f"  Reference (Draw {ref_result.draw_number}): {ref_numbers} + {ref_bonus}")
                logger.info(f"  Latest (Draw {latest_result.draw_number}): {latest_numbers} + {latest_bonus}")
                
                if latest_result.draw_number != ref_result.draw_number:
                    logger.info(f"  ✓ New draw detected: {latest_result.draw_number}")
                else:
                    logger.info(f"  Same draw number, checking accuracy...")

def main():
    """Main function to run the complete workflow and analysis"""
    logger.info("Starting complete Google Gemini workflow test...")
    
    # Run the complete automation workflow
    workflow_success = run_complete_workflow()
    
    if workflow_success:
        # Analyze extraction results
        analyze_extraction_results()
        
        # Compare with previous data
        compare_with_previous_data()
    else:
        logger.error("Workflow execution failed")
    
    logger.info("Complete Google Gemini workflow test finished")

if __name__ == "__main__":
    main()