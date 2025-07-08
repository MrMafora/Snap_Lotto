#!/usr/bin/env python3
"""
Quick update of July 8, 2025 official lottery data
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

def extract_and_update(image_path, lottery_type, expected_draw):
    """Extract and immediately update lottery data"""
    
    api_key = os.environ.get('GEMINI_API_KEY')
    if not api_key:
        return False
    
    client = genai.Client(api_key=api_key)
    
    with open(image_path, 'rb') as f:
        image_bytes = f.read()
    
    # Simple extraction prompt
    prompt = f"""Extract {lottery_type} results from this screenshot.
    Return JSON with: draw_number, draw_date, main_numbers array, bonus_numbers array (if any), divisions array.
    Extract authentic visible data only."""
    
    try:
        response = client.models.generate_content(
            model="gemini-2.5-pro",
            contents=[
                types.Part.from_bytes(data=image_bytes, mime_type="image/png"),
                prompt
            ]
        )
        
        if response and response.text:
            # Parse response
            text = response.text.strip()
            if text.startswith('```json'):
                text = text[7:-3]
            
            data = json.loads(text)
            
            # Update database immediately
            with app.app_context():
                existing = db.session.query(LotteryResult).filter_by(
                    lottery_type=lottery_type,
                    draw_number=expected_draw
                ).first()
                
                if existing:
                    existing.draw_date = datetime.strptime(data['draw_date'], '%Y-%m-%d').date()
                    existing.main_numbers = data['main_numbers']
                    existing.bonus_numbers = data.get('bonus_numbers', [])
                    existing.divisions = json.dumps(data.get('divisions', []))
                    db.session.commit()
                    logger.info(f"Updated {lottery_type} draw {expected_draw}")
                    return True
                else:
                    new_result = LotteryResult(
                        lottery_type=lottery_type,
                        draw_number=expected_draw,
                        draw_date=datetime.strptime(data['draw_date'], '%Y-%m-%d').date(),
                        main_numbers=data['main_numbers'],
                        bonus_numbers=data.get('bonus_numbers', []),
                        divisions=json.dumps(data.get('divisions', []))
                    )
                    db.session.add(new_result)
                    db.session.commit()
                    logger.info(f"Added {lottery_type} draw {expected_draw}")
                    return True
                    
    except Exception as e:
        logger.error(f"Failed to process {lottery_type}: {e}")
    
    return False

def main():
    """Quick update of lottery data"""
    
    updates = [
        ('attached_assets/20250708_025148_lotto_1752010352070.png', 'LOTTO', 2556),
        ('attached_assets/20250708_025154_lotto_plus_1_1752010352070.png', 'LOTTO PLUS 1', 2556),
        ('attached_assets/20250708_025200_lotto_plus_2_1752010352070.png', 'LOTTO PLUS 2', 2556),
        ('attached_assets/20250708_025205_powerball_1752010352070.png', 'POWERBALL', 1632),
        ('attached_assets/20250708_025211_powerball_plus_1752010352070.png', 'POWERBALL PLUS', 1632),
        ('attached_assets/20250708_025217_daily_lotto_1752010352071.png', 'DAILY LOTTO', 4524)
    ]
    
    success = 0
    for img, lottery, draw in updates:
        if os.path.exists(img):
            logger.info(f"Processing {lottery}...")
            if extract_and_update(img, lottery, draw):
                success += 1
                cache.clear()  # Clear cache after each update
    
    logger.info(f"Updated {success}/{len(updates)} lottery types")

if __name__ == "__main__":
    main()