#!/usr/bin/env python3
"""
Update current lottery draws with authentic data from screenshots
Focus on the 4 lottery types that need updating
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

def process_lottery_screenshot(image_path, lottery_type, draw_number):
    """Process a single lottery screenshot"""
    
    api_key = os.environ.get('GEMINI_API_KEY')
    if not api_key:
        logger.error("GEMINI_API_KEY not found")
        return None
    
    client = genai.Client(api_key=api_key)
    
    with open(image_path, 'rb') as f:
        image_bytes = f.read()
    
    # Specific extraction prompt
    prompt = f"""Extract the {lottery_type} lottery results from this official South African screenshot.
    
    Expected draw number: {draw_number}
    
    Return a JSON object with these exact fields:
    - draw_number: {draw_number}
    - draw_date: The date in YYYY-MM-DD format
    - main_numbers: Array of winning numbers
    - bonus_numbers: Array with bonus/powerball if applicable
    - divisions: Array of prize divisions
    
    Extract ONLY the authentic numbers visible in the screenshot."""
    
    try:
        response = client.models.generate_content(
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
            logger.info(f"Extracted {lottery_type}: {result}")
            return result
            
    except Exception as e:
        logger.error(f"Failed to extract {lottery_type}: {e}")
    
    return None

def update_single_lottery(lottery_type, draw_number, data):
    """Update a single lottery result"""
    
    with app.app_context():
        try:
            # Find the specific record
            existing = db.session.query(LotteryResult).filter_by(
                lottery_type=lottery_type,
                draw_number=draw_number
            ).first()
            
            if existing:
                # Update with authentic data
                existing.draw_date = datetime.strptime(data['draw_date'], '%Y-%m-%d').date()
                existing.main_numbers = data['main_numbers']
                existing.bonus_numbers = data.get('bonus_numbers', [])
                existing.divisions = json.dumps(data.get('divisions', []))
                
                db.session.commit()
                logger.info(f"Updated {lottery_type} draw {draw_number} with authentic data")
                return True
            else:
                logger.warning(f"No existing record for {lottery_type} draw {draw_number}")
                
        except Exception as e:
            logger.error(f"Database update failed: {e}")
            db.session.rollback()
    
    return False

def main():
    """Update the 4 lottery types that need authentic data"""
    
    # Specific updates needed based on database analysis
    updates_needed = [
        {
            'image': 'attached_assets/20250620_190134_lotto_plus_2_1750456254489.png',
            'lottery_type': 'LOTTO PLUS 2',
            'draw_number': 2556
        },
        {
            'image': 'attached_assets/20250620_190139_powerball_1750456254489.png', 
            'lottery_type': 'POWERBALL',
            'draw_number': 1631
        },
        {
            'image': 'attached_assets/20250620_190146_powerball_plus_1750456254489.png',
            'lottery_type': 'POWERBALL PLUS',
            'draw_number': 1631
        },
        {
            'image': 'attached_assets/20250620_190152_daily_lotto_1750456254490.png',
            'lottery_type': 'DAILY LOTTO',
            'draw_number': 4524
        }
    ]
    
    success_count = 0
    
    for update in updates_needed:
        if os.path.exists(update['image']):
            logger.info(f"\n--- Processing {update['lottery_type']} ---")
            
            # Extract data
            data = process_lottery_screenshot(
                update['image'], 
                update['lottery_type'], 
                update['draw_number']
            )
            
            if data:
                # Update database
                if update_single_lottery(update['lottery_type'], update['draw_number'], data):
                    success_count += 1
            else:
                logger.error(f"Failed to extract data for {update['lottery_type']}")
        else:
            logger.error(f"Image not found: {update['image']}")
    
    # Clear cache
    cache.clear()
    logger.info(f"\n=== Completed: {success_count}/4 lottery types updated ===")

if __name__ == "__main__":
    logger.info("=== UPDATING CURRENT LOTTERY DRAWS WITH AUTHENTIC DATA ===")
    main()