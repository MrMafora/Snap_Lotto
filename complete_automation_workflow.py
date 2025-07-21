#!/usr/bin/env python3
"""
Complete Automated Lottery Workflow System
Captures fresh screenshots, processes with AI, and updates database automatically
"""

import logging
import sys
import os
import time
from datetime import datetime

# Add current directory to path
sys.path.append('.')

def setup_logging():
    """Configure logging for automation workflow"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('automation_workflow.log'),
            logging.StreamHandler(sys.stdout)
        ]
    )
    return logging.getLogger(__name__)

def run_complete_automation():
    """Run the complete automated lottery workflow"""
    logger = setup_logging()
    
    logger.info("=== STARTING COMPLETE AUTOMATED LOTTERY WORKFLOW ===")
    start_time = datetime.now()
    
    try:
        # Step 1: Capture fresh screenshots
        logger.info("Step 1: Capturing fresh lottery screenshots...")
        from screenshot_capture import main as capture_screenshots
        capture_result = capture_screenshots()
        logger.info(f"Screenshot capture completed: {capture_result}")
        
        # Step 2: Process screenshots with AI
        logger.info("Step 2: Processing screenshots with Google Gemini AI...")
        
        from app import app
        from ai_lottery_processor import CompleteLotteryProcessor
        
        with app.app_context():
            processor = CompleteLotteryProcessor()
            
            # Get all screenshots from today
            screenshot_dir = 'screenshots'
            today = datetime.now().strftime('%Y%m%d')
            
            screenshots = [f for f in os.listdir(screenshot_dir) 
                          if f.startswith(today) and f.endswith('.png')]
            
            logger.info(f"Found {len(screenshots)} screenshots from today")
            
            new_results = 0
            for screenshot in screenshots:
                screenshot_path = os.path.join(screenshot_dir, screenshot)
                
                # Determine lottery type from filename
                lottery_type = None
                if 'lotto_plus_1' in screenshot:
                    lottery_type = 'LOTTO PLUS 1'
                elif 'lotto_plus_2' in screenshot:
                    lottery_type = 'LOTTO PLUS 2'
                elif 'powerball_plus' in screenshot:
                    lottery_type = 'POWERBALL PLUS'
                elif 'daily_lotto' in screenshot:
                    lottery_type = 'DAILY LOTTO'
                elif 'powerball' in screenshot:
                    lottery_type = 'POWERBALL'
                elif 'lotto' in screenshot:
                    lottery_type = 'LOTTO'
                
                if lottery_type:
                    logger.info(f"Processing {lottery_type}: {screenshot}")
                    
                    try:
                        result = processor.process_single_image(screenshot_path, lottery_type)
                        
                        if result and 'extracted_data' in result:
                            data = result['extracted_data']
                            confidence = result.get('confidence', 0)
                            
                            logger.info(f"AI extracted {lottery_type} - Draw {data.get('draw_number')} "
                                      f"({data.get('draw_date')}) with {confidence}% confidence")
                            
                            # Save to database
                            success = processor.save_to_database(data, lottery_type)
                            if success:
                                new_results += 1
                                logger.info(f"✅ NEW {lottery_type} result saved to database")
                            else:
                                logger.info(f"⚠️ {lottery_type} result already exists (not duplicate)")
                                
                    except Exception as e:
                        logger.error(f"Error processing {lottery_type}: {str(e)}")
        
        # Step 3: Summary
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        
        logger.info("=== AUTOMATION WORKFLOW COMPLETE ===")
        logger.info(f"Duration: {duration:.1f} seconds")
        logger.info(f"Screenshots processed: {len(screenshots)}")
        logger.info(f"New results added: {new_results}")
        
        if new_results > 0:
            logger.info("🎯 NEW LOTTERY RESULTS DETECTED AND SAVED!")
        else:
            logger.info("ℹ️ No new lottery results found (all current)")
            
        return {
            'success': True,
            'duration': duration,
            'screenshots_processed': len(screenshots),
            'new_results': new_results,
            'message': f"Processed {len(screenshots)} screenshots, found {new_results} new results"
        }
        
    except Exception as e:
        logger.error(f"Automation workflow failed: {str(e)}")
        return {
            'success': False,
            'error': str(e),
            'message': f"Workflow failed: {str(e)}"
        }

if __name__ == "__main__":
    result = run_complete_automation()
    print(f"\n=== FINAL RESULT ===")
    print(f"Success: {result['success']}")
    print(f"Message: {result['message']}")
    
    if result['success']:
        sys.exit(0)
    else:
        sys.exit(1)