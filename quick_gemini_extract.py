#!/usr/bin/env python3
"""
Quick extraction of lottery data using Gemini 2.5 Pro - focusing on missing data
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

def extract_specific_lottery(lottery_type, expected_draw_date="2025-07-08"):
    """Extract specific lottery type from latest screenshots"""
    
    # Setup Gemini
    api_key = os.environ.get('GEMINI_API_KEY')
    if not api_key:
        logger.error("GEMINI_API_KEY not found")
        return None
    
    client = genai.Client(api_key=api_key)
    
    # Map lottery type to filename pattern
    filename_patterns = {
        'LOTTO PLUS 2': 'lotto_plus_2',
        'POWERBALL': 'powerball',
        'POWERBALL PLUS': 'powerball_plus', 
        'DAILY LOTTO': 'daily_lotto'
    }
    
    pattern = filename_patterns.get(lottery_type)
    if not pattern:
        logger.error(f"Unknown lottery type: {lottery_type}")
        return None
    
    # Find latest screenshot
    screenshots_dir = 'screenshots'
    matching_files = []
    for f in os.listdir(screenshots_dir):
        if pattern in f.lower() and f.endswith('.png'):
            matching_files.append(f)
    
    if not matching_files:
        logger.error(f"No screenshots found for {lottery_type}")
        return None
    
    # Use the most recent one
    matching_files.sort(reverse=True)
    screenshot_file = matching_files[0]
    image_path = os.path.join(screenshots_dir, screenshot_file)
    
    logger.info(f"Processing {lottery_type} from {screenshot_file}")
    
    # Read image
    with open(image_path, 'rb') as f:
        image_bytes = f.read()
    
    # Specific prompts for each lottery type
    if lottery_type == 'DAILY LOTTO':
        prompt = f"""Extract the Daily Lotto results from this official South African lottery screenshot.
        
        Look for:
        - Draw number (4 digits, around 4524)
        - Draw date (should be {expected_draw_date})
        - 5 main winning numbers
        - 4 prize divisions with winners and prizes
        
        Return ONLY a JSON object with this exact structure:
        {{
            "draw_number": <number>,
            "draw_date": "{expected_draw_date}",
            "main_numbers": [<5 numbers>],
            "divisions": [
                {{"division": 1, "winners": <count>, "prize": "<amount>"}},
                {{"division": 2, "winners": <count>, "prize": "<amount>"}},
                {{"division": 3, "winners": <count>, "prize": "<amount>"}},
                {{"division": 4, "winners": <count>, "prize": "<amount>"}}
            ]
        }}"""
    elif 'POWERBALL' in lottery_type:
        prompt = f"""Extract the {lottery_type} results from this official South African lottery screenshot.
        
        Look for:
        - Draw number (4 digits, around 1631) 
        - Draw date (should be {expected_draw_date})
        - 5 main winning numbers
        - 1 Powerball number
        - 9 prize divisions with winners and prizes
        
        Return ONLY a JSON object with this exact structure:
        {{
            "draw_number": <number>,
            "draw_date": "{expected_draw_date}",
            "main_numbers": [<5 numbers>],
            "powerball": <powerball number>,
            "divisions": [
                {{"division": 1, "winners": <count>, "prize": "<amount>"}},
                ... (9 divisions total)
            ]
        }}"""
    else:  # LOTTO PLUS 2
        prompt = f"""Extract the Lotto Plus 2 results from this official South African lottery screenshot.
        
        Look for:
        - Draw number (4 digits, around 2556)
        - Draw date (should be around 2025-07-05)
        - 6 main winning numbers
        - 1 bonus number
        - 8 prize divisions with winners and prizes
        
        Return ONLY a JSON object with this exact structure:
        {{
            "draw_number": <number>,
            "draw_date": "YYYY-MM-DD",
            "main_numbers": [<6 numbers>],
            "bonus_number": <bonus>,
            "divisions": [
                {{"division": 1, "winners": <count>, "prize": "<amount>"}},
                ... (8 divisions total)
            ]
        }}"""
    
    try:
        response = client.models.generate_content(
            model="gemini-2.5-pro",
            contents=[
                types.Part.from_bytes(
                    data=image_bytes,
                    mime_type="image/png"
                ),
                prompt
            ]
        )
        
        if response and response.text:
            # Clean the response text
            text = response.text.strip()
            if text.startswith('```json'):
                text = text[7:]
            if text.endswith('```'):
                text = text[:-3]
            
            result = json.loads(text)
            logger.info(f"Extracted {lottery_type}: Draw {result.get('draw_number')}")
            return result
        
    except Exception as e:
        logger.error(f"Failed to extract {lottery_type}: {e}")
    
    return None

def update_lottery_result(lottery_type, data):
    """Update specific lottery result in database"""
    
    with app.app_context():
        try:
            # Find existing record
            existing = db.session.query(LotteryResult).filter_by(
                lottery_type=lottery_type,
                draw_number=data['draw_number']
            ).first()
            
            # Prepare numbers
            main_numbers = data['main_numbers']
            bonus_numbers = []
            if 'powerball' in data:
                bonus_numbers = [data['powerball']]
            elif 'bonus_number' in data:
                bonus_numbers = [data['bonus_number']]
            
            if existing:
                # Update existing
                existing.draw_date = datetime.strptime(data['draw_date'], '%Y-%m-%d').date()
                existing.main_numbers = main_numbers
                existing.bonus_numbers = bonus_numbers
                existing.divisions = json.dumps(data.get('divisions', []))
                logger.info(f"Updated {lottery_type} draw {data['draw_number']}")
            else:
                # Create new
                new_result = LotteryResult(
                    lottery_type=lottery_type,
                    draw_number=data['draw_number'],
                    draw_date=datetime.strptime(data['draw_date'], '%Y-%m-%d').date(),
                    main_numbers=main_numbers,
                    bonus_numbers=bonus_numbers,
                    divisions=json.dumps(data.get('divisions', []))
                )
                db.session.add(new_result)
                logger.info(f"Added new {lottery_type} draw {data['draw_number']}")
            
            db.session.commit()
            return True
            
        except Exception as e:
            logger.error(f"Database update failed: {e}")
            db.session.rollback()
            return False

def main():
    """Extract and update missing lottery data"""
    
    # Focus on the incorrect/missing data
    lotteries_to_fix = ['LOTTO PLUS 2', 'POWERBALL', 'POWERBALL PLUS', 'DAILY LOTTO']
    
    success_count = 0
    for lottery_type in lotteries_to_fix:
        logger.info(f"\nExtracting {lottery_type}...")
        
        data = extract_specific_lottery(lottery_type)
        if data:
            if update_lottery_result(lottery_type, data):
                success_count += 1
            else:
                logger.error(f"Failed to save {lottery_type}")
        else:
            logger.error(f"Failed to extract {lottery_type}")
    
    # Clear cache
    cache.clear()
    logger.info(f"\nCompleted: {success_count}/{len(lotteries_to_fix)} successful")

if __name__ == "__main__":
    logger.info("=== QUICK GEMINI EXTRACTION STARTED ===")
    main()
    logger.info("=== EXTRACTION COMPLETED ===")