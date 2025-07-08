#!/usr/bin/env python3
"""
Extract current authentic South African lottery data from June 20, 2025 screenshots
"""

import os
import json
import logging
from datetime import datetime
from google import genai
from google.genai import types
from models import db, LotteryResult
from main import app
from cache_manager import cache

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def setup_gemini():
    """Configure Google Gemini API"""
    api_key = os.environ.get('GEMINI_API_KEY')
    if not api_key:
        raise ValueError("GEMINI_API_KEY not found")
    
    return genai.Client(api_key=api_key)

def extract_lottery_data(model, image_path, expected_type):
    """Extract lottery data from screenshot"""
    
    with open(image_path, 'rb') as f:
        image_bytes = f.read()
    
    prompt = f"""Extract the {expected_type} lottery results from this official South African screenshot.
    
    Return a JSON object with:
    - lottery_type: "{expected_type}"
    - draw_number: The actual draw number visible
    - draw_date: The draw date in YYYY-MM-DD format
    - main_numbers: Array of main winning numbers
    - bonus_numbers: Array with bonus/powerball number (if applicable)
    - divisions: Array of prize divisions with division number, winners, and prize
    
    Extract ONLY authentic numbers visible in the screenshot."""
    
    try:
        response = model.models.generate_content(
            model="gemini-2.5-pro",
            contents=[
                types.Part.from_bytes(data=image_bytes, mime_type="image/png"),
                prompt
            ],
            config=types.GenerateContentConfig(
                response_mime_type="application/json"
            )
        )
        
        if response and response.text:
            result = json.loads(response.text)
            logger.info(f"Extracted {expected_type}: Draw {result.get('draw_number')}, Date: {result.get('draw_date')}")
            return result
            
    except Exception as e:
        logger.error(f"Failed to extract {expected_type}: {e}")
    
    return None

def save_authentic_data(lottery_data):
    """Save authentic lottery data to database"""
    
    with app.app_context():
        try:
            lottery_type = lottery_data['lottery_type']
            draw_number = lottery_data['draw_number']
            
            existing = db.session.query(LotteryResult).filter_by(
                lottery_type=lottery_type,
                draw_number=draw_number
            ).first()
            
            if existing:
                # Update existing
                existing.draw_date = datetime.strptime(lottery_data['draw_date'], '%Y-%m-%d').date()
                existing.main_numbers = lottery_data['main_numbers']
                existing.bonus_numbers = lottery_data.get('bonus_numbers', [])
                existing.divisions = json.dumps(lottery_data.get('divisions', []))
                logger.info(f"Updated {lottery_type} draw {draw_number}")
            else:
                # Create new
                new_result = LotteryResult(
                    lottery_type=lottery_type,
                    draw_number=draw_number,
                    draw_date=datetime.strptime(lottery_data['draw_date'], '%Y-%m-%d').date(),
                    main_numbers=lottery_data['main_numbers'],
                    bonus_numbers=lottery_data.get('bonus_numbers', []),
                    divisions=json.dumps(lottery_data.get('divisions', []))
                )
                db.session.add(new_result)
                logger.info(f"Added new {lottery_type} draw {draw_number}")
            
            db.session.commit()
            return True
            
        except Exception as e:
            logger.error(f"Database save failed: {e}")
            db.session.rollback()
            return False

def main():
    """Extract all current authentic lottery data"""
    
    client = setup_gemini()
    
    # Map of June 20 screenshots to lottery types
    screenshots = [
        ('attached_assets/20250620_190121_lotto_1750456254489.png', 'LOTTO'),
        ('attached_assets/20250620_190128_lotto_plus_1_1750456254489.png', 'LOTTO PLUS 1'),
        ('attached_assets/20250620_190134_lotto_plus_2_1750456254489.png', 'LOTTO PLUS 2'),
        ('attached_assets/20250620_190139_powerball_1750456254489.png', 'POWERBALL'),
        ('attached_assets/20250620_190146_powerball_plus_1750456254489.png', 'POWERBALL PLUS'),
        ('attached_assets/20250620_190152_daily_lotto_1750456254490.png', 'DAILY LOTTO')
    ]
    
    success_count = 0
    
    for image_path, lottery_type in screenshots:
        if os.path.exists(image_path):
            logger.info(f"\nProcessing {lottery_type} from {image_path}...")
            
            data = extract_lottery_data(client, image_path, lottery_type)
            if data:
                if save_authentic_data(data):
                    success_count += 1
            else:
                logger.error(f"Failed to extract {lottery_type}")
        else:
            logger.warning(f"Screenshot not found: {image_path}")
    
    # Clear cache
    cache.clear()
    logger.info(f"\nCompleted: {success_count}/{len(screenshots)} successful")
    logger.info("Cache cleared for fresh authentic data")

if __name__ == "__main__":
    logger.info("=== EXTRACTING CURRENT AUTHENTIC LOTTERY DATA ===")
    main()