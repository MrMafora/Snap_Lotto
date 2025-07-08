#!/usr/bin/env python3
"""
Quick extraction of authentic lottery data from available screenshots
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

def extract_single_lottery(image_path, lottery_type):
    """Extract single lottery result"""
    
    api_key = os.environ.get('GEMINI_API_KEY')
    if not api_key:
        logger.error("GEMINI_API_KEY not found")
        return None
    
    client = genai.Client(api_key=api_key)
    
    with open(image_path, 'rb') as f:
        image_bytes = f.read()
    
    # Simple prompt for extraction
    prompt = f"""Extract {lottery_type} lottery results from this screenshot.
    Return JSON with: lottery_type, draw_number, draw_date, main_numbers, bonus_numbers (if any), divisions array.
    Extract ONLY visible authentic numbers."""
    
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
            
            result = json.loads(text)
            result['lottery_type'] = lottery_type  # Ensure correct type
            logger.info(f"Extracted {lottery_type}: Draw {result.get('draw_number')}")
            return result
            
    except Exception as e:
        logger.error(f"Failed to extract {lottery_type}: {e}")
    
    return None

def update_database(data):
    """Update database with extracted data"""
    
    with app.app_context():
        try:
            lottery_type = data['lottery_type']
            draw_number = data['draw_number']
            
            # Update or create
            existing = db.session.query(LotteryResult).filter_by(
                lottery_type=lottery_type,
                draw_number=draw_number
            ).first()
            
            if existing:
                existing.draw_date = datetime.strptime(data['draw_date'], '%Y-%m-%d').date()
                existing.main_numbers = data['main_numbers']
                existing.bonus_numbers = data.get('bonus_numbers', [])
                existing.divisions = json.dumps(data.get('divisions', []))
                logger.info(f"Updated {lottery_type} draw {draw_number}")
            else:
                new_result = LotteryResult(
                    lottery_type=lottery_type,
                    draw_number=draw_number,
                    draw_date=datetime.strptime(data['draw_date'], '%Y-%m-%d').date(),
                    main_numbers=data['main_numbers'],
                    bonus_numbers=data.get('bonus_numbers', []),
                    divisions=json.dumps(data.get('divisions', []))
                )
                db.session.add(new_result)
                logger.info(f"Added {lottery_type} draw {draw_number}")
            
            db.session.commit()
            return True
            
        except Exception as e:
            logger.error(f"Database update failed: {e}")
            db.session.rollback()
            return False

def main():
    """Process priority lottery types"""
    
    # Check what needs updating
    with app.app_context():
        results = db.session.query(LotteryResult).all()
        logger.info("Current database state:")
        for r in results:
            logger.info(f"  {r.lottery_type}: Draw {r.draw_number} - {r.main_numbers}")
    
    # Priority screenshots to process
    priority_screenshots = [
        ('attached_assets/20250620_190134_lotto_plus_2_1750456254489.png', 'LOTTO PLUS 2'),
        ('attached_assets/20250620_190139_powerball_1750456254489.png', 'POWERBALL'),
        ('attached_assets/20250620_190146_powerball_plus_1750456254489.png', 'POWERBALL PLUS'),
        ('attached_assets/20250620_190152_daily_lotto_1750456254490.png', 'DAILY LOTTO')
    ]
    
    success_count = 0
    
    for image_path, lottery_type in priority_screenshots:
        if os.path.exists(image_path):
            logger.info(f"\nProcessing {lottery_type}...")
            
            data = extract_single_lottery(image_path, lottery_type)
            if data and update_database(data):
                success_count += 1
                # Clear cache after each successful update
                cache.clear()
        else:
            logger.warning(f"Screenshot not found: {image_path}")
    
    logger.info(f"\nCompleted: {success_count} lottery types updated")

if __name__ == "__main__":
    logger.info("=== QUICK AUTHENTIC EXTRACTION ===")
    main()