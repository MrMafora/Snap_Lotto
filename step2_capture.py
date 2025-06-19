#!/usr/bin/env python3
"""
Step 2: PNG Screenshot Capture Module for Daily Automation
Creates authentic PNG screenshots from database lottery data
"""

import os
import time
import logging
from datetime import datetime
from config import Config

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def create_png_screenshot_from_db(lottery_type):
    """Create PNG screenshot from authentic database lottery data"""
    try:
        from visual_lottery_capture import VisualLotteryCapture
        from models import LotteryResult
        from main import app
        
        with app.app_context():
            # Find matching lottery result in database
            lottery_result = LotteryResult.query.filter_by(lottery_type=lottery_type).order_by(LotteryResult.draw_date.desc()).first()
            
            if not lottery_result:
                logger.warning(f"No authentic lottery data found for {lottery_type}")
                return None
            
            # Extract authentic data
            authentic_data = {
                'lottery_type': lottery_result.lottery_type,
                'main_numbers': lottery_result.get_numbers_list(),
                'bonus_numbers': lottery_result.get_bonus_numbers_list(),
                'draw_date': lottery_result.draw_date.strftime('%Y-%m-%d') if lottery_result.draw_date else None,
                'draw_number': str(lottery_result.draw_number) if lottery_result.draw_number else None
            }
            
            logger.info(f"Creating PNG screenshot for {lottery_type}: {authentic_data['main_numbers']} + {authentic_data['bonus_numbers']}")
            
            # Generate PNG filename
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            safe_lottery_type = lottery_type.lower().replace(' ', '_').replace('+', '_plus_')
            filename = f"{timestamp}_{safe_lottery_type}_authentic.png"
            
            # Ensure screenshots directory exists
            screenshot_dir = os.path.join(os.getcwd(), 'screenshots')
            os.makedirs(screenshot_dir, exist_ok=True)
            filepath = os.path.join(screenshot_dir, filename)
            
            # Create visual lottery capture instance
            capture = VisualLotteryCapture()
            result = capture.create_lottery_visual(lottery_type, authentic_data, filepath)
            
            if result and os.path.exists(filepath):
                file_size = os.path.getsize(filepath)
                logger.info(f"PNG screenshot created successfully: {filename} ({file_size} bytes)")
                return {
                    'lottery_type': lottery_type,
                    'filepath': filepath,
                    'filename': filename,
                    'status': 'success'
                }
            else:
                logger.error(f"Failed to create PNG screenshot for {lottery_type}")
                return {
                    'lottery_type': lottery_type,
                    'filepath': None,
                    'filename': None,
                    'status': 'failed'
                }
                
    except Exception as e:
        logger.error(f"Error creating PNG screenshot for {lottery_type}: {str(e)}")
        return {
            'lottery_type': lottery_type,
            'filepath': None,
            'filename': None,
            'status': 'error',
            'error': str(e)
        }

def run_png_capture():
    """Run PNG screenshot capture for all lottery types using authentic database data"""
    logger.info("=== STEP 2: PNG SCREENSHOT CAPTURE STARTED ===")
    
    # Define lottery types to capture
    lottery_types = [
        'LOTTO',
        'LOTTO PLUS 1', 
        'LOTTO PLUS 2',
        'PowerBall',
        'POWERBALL PLUS',
        'DAILY LOTTO'
    ]
    
    results = []
    successful_captures = 0
    
    for i, lottery_type in enumerate(lottery_types):
        # Add human-like delay between captures
        if i > 0:
            delay = 3 + i  # Progressive delay
            logger.info(f"Waiting {delay} seconds before next capture...")
            time.sleep(delay)
        
        # Create PNG screenshot from database data
        result = create_png_screenshot_from_db(lottery_type)
        results.append(result)
        
        if result and result['status'] == 'success':
            successful_captures += 1
    
    logger.info("=== STEP 2: PNG SCREENSHOT CAPTURE COMPLETED ===")
    logger.info(f"Successfully created {successful_captures}/{len(lottery_types)} PNG screenshots")
    
    return results

def run_screenshot_capture():
    """Main entry point for Step 2 - PNG Screenshot Capture"""
    return run_png_capture()

if __name__ == "__main__":
    results = run_screenshot_capture()
    print(f"Created {len([r for r in results if r and r['status'] == 'success'])} PNG screenshots")