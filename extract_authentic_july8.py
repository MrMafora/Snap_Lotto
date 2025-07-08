#!/usr/bin/env python3
"""
Extract authentic lottery data from July 8, 2025 screenshots using Google Gemini 2.5 Pro
"""

import os
import json
import logging
from datetime import datetime
from google import genai
from google.genai import types
from PIL import Image
from models import db, LotteryResult
from main import app

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def setup_gemini():
    """Configure Google Gemini 2.5 Pro API"""
    api_key = os.environ.get('GEMINI_API_KEY')
    if not api_key:
        raise ValueError("GEMINI_API_KEY not found in environment variables")
    
    client = genai.Client(api_key=api_key)
    return client

def extract_lottery_data_from_screenshot(client, image_path):
    """Extract lottery data using Gemini 2.5 Pro"""
    
    # Read image
    with open(image_path, 'rb') as f:
        image_bytes = f.read()
    
    # Determine lottery type from filename
    filename = os.path.basename(image_path).lower()
    if 'daily_lotto' in filename:
        lottery_type = 'DAILY LOTTO'
    elif 'powerball_plus' in filename:
        lottery_type = 'POWERBALL PLUS'
    elif 'powerball' in filename:
        lottery_type = 'POWERBALL'
    elif 'lotto_plus_2' in filename:
        lottery_type = 'LOTTO PLUS 2'
    elif 'lotto_plus_1' in filename:
        lottery_type = 'LOTTO PLUS 1'
    elif 'lotto' in filename:
        lottery_type = 'LOTTO'
    else:
        logger.warning(f"Unknown lottery type for {filename}")
        return None
    
    prompt = f"""Extract the lottery results from this South African {lottery_type} screenshot.

Return a JSON object with EXACTLY this structure:
{{
    "lottery_type": "{lottery_type}",
    "draw_number": <number>,
    "draw_date": "YYYY-MM-DD",
    "main_numbers": [<list of main winning numbers>],
    "bonus_numbers": [<list of bonus/powerball numbers if any>],
    "jackpot": "<jackpot amount>",
    "divisions": [
        {{"division": 1, "winners": <count>, "prize": "<amount>"}},
        {{"division": 2, "winners": <count>, "prize": "<amount>"}},
        ...
    ]
}}

IMPORTANT:
- For LOTTO types: 6 main numbers + 1 bonus number, 8 divisions
- For POWERBALL types: 5 main numbers + 1 powerball, 9 divisions  
- For DAILY LOTTO: 5 main numbers, no bonus, 4 divisions
- Extract ALL visible prize divisions
- Use exact numbers from the screenshot"""

    try:
        response = client.models.generate_content(
            model="gemini-2.5-pro",
            contents=[
                types.Part.from_bytes(
                    data=image_bytes,
                    mime_type="image/png"
                ),
                prompt
            ],
            config=types.GenerateContentConfig(
                response_mime_type="application/json"
            )
        )
        
        if response and response.text:
            result = json.loads(response.text)
            logger.info(f"Extracted {lottery_type}: Draw {result.get('draw_number')}")
            return result
        
    except Exception as e:
        logger.error(f"Failed to extract from {image_path}: {e}")
    
    return None

def update_database_with_authentic_data(lottery_data):
    """Update database with authentic extracted data"""
    
    with app.app_context():
        try:
            # Check if result already exists
            existing = db.session.query(LotteryResult).filter_by(
                lottery_type=lottery_data['lottery_type'],
                draw_number=lottery_data['draw_number']
            ).first()
            
            if existing:
                # Update existing record
                existing.draw_date = datetime.strptime(lottery_data['draw_date'], '%Y-%m-%d').date()
                existing.main_numbers = lottery_data['main_numbers']
                existing.bonus_numbers = lottery_data.get('bonus_numbers', [])
                existing.divisions = json.dumps(lottery_data.get('divisions', []))
                logger.info(f"Updated {lottery_data['lottery_type']} draw {lottery_data['draw_number']}")
            else:
                # Create new record
                new_result = LotteryResult(
                    lottery_type=lottery_data['lottery_type'],
                    draw_number=lottery_data['draw_number'],
                    draw_date=datetime.strptime(lottery_data['draw_date'], '%Y-%m-%d').date(),
                    main_numbers=lottery_data['main_numbers'],
                    bonus_numbers=lottery_data.get('bonus_numbers', []),
                    divisions=json.dumps(lottery_data.get('divisions', []))
                )
                db.session.add(new_result)
                logger.info(f"Added new {lottery_data['lottery_type']} draw {lottery_data['draw_number']}")
            
            db.session.commit()
            return True
            
        except Exception as e:
            logger.error(f"Database update failed: {e}")
            db.session.rollback()
            return False

def main():
    """Extract authentic lottery data from screenshots"""
    
    client = setup_gemini()
    
    # Look for July 8 screenshots
    screenshots_dir = 'screenshots'
    screenshot_files = [
        f for f in os.listdir(screenshots_dir) 
        if f.startswith('20250708') and f.endswith('.png')
    ]
    
    if not screenshot_files:
        logger.error("No July 8 screenshots found")
        return
    
    logger.info(f"Found {len(screenshot_files)} screenshots to process")
    
    success_count = 0
    for screenshot in screenshot_files:
        image_path = os.path.join(screenshots_dir, screenshot)
        logger.info(f"Processing {screenshot}...")
        
        # Extract data using Gemini
        lottery_data = extract_lottery_data_from_screenshot(client, image_path)
        
        if lottery_data:
            # Update database
            if update_database_with_authentic_data(lottery_data):
                success_count += 1
            else:
                logger.error(f"Failed to save {screenshot} to database")
        else:
            logger.error(f"Failed to extract data from {screenshot}")
    
    logger.info(f"\nExtraction complete: {success_count}/{len(screenshot_files)} successful")
    
    # Clear cache to ensure fresh data loads
    from cache_manager import cache
    cache.clear()
    logger.info("Cache cleared")

if __name__ == "__main__":
    logger.info("=== AUTHENTIC LOTTERY DATA EXTRACTION STARTED ===")
    main()
    logger.info("=== EXTRACTION COMPLETED ===")