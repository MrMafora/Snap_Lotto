#!/usr/bin/env python3
"""
Extract authentic lottery data from July 8, 2025 official screenshots
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

def extract_lottery_from_screenshot(image_path, lottery_type):
    """Extract lottery data from official screenshot using Gemini 2.5 Pro"""
    
    api_key = os.environ.get('GEMINI_API_KEY')
    if not api_key:
        logger.error("GEMINI_API_KEY not found")
        return None
    
    client = genai.Client(api_key=api_key)
    
    with open(image_path, 'rb') as f:
        image_bytes = f.read()
    
    # Specific prompt for accurate extraction
    prompt = f"""Extract the {lottery_type} lottery results from this official South African National Lottery screenshot.

Extract ALL the following information:
1. Draw number (shown as "DRAW DATE" with number)
2. Draw date (in YYYY-MM-DD format)
3. Main winning numbers (in the yellow circles)
4. Bonus/Powerball number (if applicable, usually in a different colored circle)
5. ALL prize divisions with:
   - Division number
   - Number of winners
   - Prize amount per winner

Return a JSON object with this exact structure:
{{
    "lottery_type": "{lottery_type}",
    "draw_number": <number>,
    "draw_date": "YYYY-MM-DD",
    "main_numbers": [list of main numbers],
    "bonus_numbers": [list with bonus/powerball if any],
    "divisions": [
        {{"division": 1, "winners": <count>, "prize": "<amount with R symbol>"}},
        ... (all divisions)
    ]
}}

Extract ONLY the authentic data visible in the screenshot."""
    
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
            logger.info(f"Extracted {lottery_type}: Draw {result.get('draw_number')}, Date: {result.get('draw_date')}")
            logger.info(f"Numbers: {result.get('main_numbers')}, Bonus: {result.get('bonus_numbers')}")
            return result
            
    except Exception as e:
        logger.error(f"Failed to extract {lottery_type}: {e}")
    
    return None

def update_lottery_database(data):
    """Update database with authentic lottery data"""
    
    with app.app_context():
        try:
            lottery_type = data['lottery_type']
            draw_number = data['draw_number']
            
            # Find existing record
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
                logger.info(f"Updated {lottery_type} draw {draw_number}")
            else:
                # Create new record
                new_result = LotteryResult(
                    lottery_type=lottery_type,
                    draw_number=draw_number,
                    draw_date=datetime.strptime(data['draw_date'], '%Y-%m-%d').date(),
                    main_numbers=data['main_numbers'],
                    bonus_numbers=data.get('bonus_numbers', []),
                    divisions=json.dumps(data.get('divisions', []))
                )
                db.session.add(new_result)
                logger.info(f"Added new {lottery_type} draw {draw_number}")
            
            db.session.commit()
            return True
            
        except Exception as e:
            logger.error(f"Database update failed: {e}")
            db.session.rollback()
            return False

def main():
    """Process July 8, 2025 official lottery screenshots"""
    
    # Map screenshots to lottery types
    screenshots = [
        ('attached_assets/20250708_025148_lotto_1752010352070.png', 'LOTTO'),
        ('attached_assets/20250708_025154_lotto_plus_1_1752010352070.png', 'LOTTO PLUS 1'),
        ('attached_assets/20250708_025200_lotto_plus_2_1752010352070.png', 'LOTTO PLUS 2'),
        ('attached_assets/20250708_025205_powerball_1752010352070.png', 'POWERBALL'),
        ('attached_assets/20250708_025211_powerball_plus_1752010352070.png', 'POWERBALL PLUS'),
        ('attached_assets/20250708_025217_daily_lotto_1752010352071.png', 'DAILY LOTTO')
    ]
    
    success_count = 0
    
    for image_path, lottery_type in screenshots:
        if os.path.exists(image_path):
            logger.info(f"\n=== Processing {lottery_type} ===")
            
            # Extract data
            data = extract_lottery_from_screenshot(image_path, lottery_type)
            
            if data:
                # Update database
                if update_lottery_database(data):
                    success_count += 1
                else:
                    logger.error(f"Failed to save {lottery_type} to database")
            else:
                logger.error(f"Failed to extract data from {lottery_type}")
        else:
            logger.error(f"Screenshot not found: {image_path}")
    
    # Clear cache for fresh data
    cache.clear()
    logger.info(f"\n=== Completed: {success_count}/{len(screenshots)} lottery types updated ===")
    logger.info("Cache cleared - fresh authentic data will now be displayed")

if __name__ == "__main__":
    logger.info("=== EXTRACTING JULY 8, 2025 OFFICIAL LOTTERY DATA ===")
    main()