#!/usr/bin/env python3
"""
Process existing screenshots with Gemini 2.5 Pro to extract authentic lottery data
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
    """Configure Google Gemini 2.5 Pro API"""
    api_key = os.environ.get('GEMINI_API_KEY')
    if not api_key:
        raise ValueError("GEMINI_API_KEY not found")
    
    return genai.Client(api_key=api_key)

def extract_from_screenshot(client, image_path):
    """Extract lottery data from a screenshot using Gemini 2.5 Pro"""
    
    with open(image_path, 'rb') as f:
        image_bytes = f.read()
    
    # Determine lottery type from filename
    filename = os.path.basename(image_path).lower()
    
    # Map filename patterns to lottery types
    if 'daily_lotto' in filename:
        lottery_type = 'DAILY LOTTO'
        num_main = 5
        num_bonus = 0
        num_divisions = 4
    elif 'powerball_plus' in filename:
        lottery_type = 'POWERBALL PLUS'
        num_main = 5
        num_bonus = 1
        num_divisions = 9
    elif 'powerball' in filename and 'plus' not in filename:
        lottery_type = 'POWERBALL'
        num_main = 5
        num_bonus = 1
        num_divisions = 9
    elif 'lotto_plus_2' in filename:
        lottery_type = 'LOTTO PLUS 2'
        num_main = 6
        num_bonus = 1
        num_divisions = 8
    elif 'lotto_plus_1' in filename:
        lottery_type = 'LOTTO PLUS 1'
        num_main = 6
        num_bonus = 1
        num_divisions = 8
    elif 'lotto' in filename:
        lottery_type = 'LOTTO'
        num_main = 6
        num_bonus = 1
        num_divisions = 8
    else:
        logger.warning(f"Unknown lottery type for {filename}")
        return None
    
    bonus_line = '"bonus_numbers": [<bonus/powerball number>],' if num_bonus > 0 else ""
    bonus_instruction = "4. Bonus/Powerball number (1 number)" if num_bonus > 0 else ""
    
    prompt = f"""You are extracting lottery results from an official South African {lottery_type} screenshot.

CRITICAL: Extract ONLY the actual numbers visible in the screenshot. NO placeholder data.

Look for and extract:
1. Draw number (usually 4 digits)
2. Draw date
3. Main winning numbers ({num_main} numbers)
{bonus_instruction}
5. Prize divisions ({num_divisions} divisions) with winners and prize amounts

Return a JSON object with this exact structure:
{{
    "lottery_type": "{lottery_type}",
    "draw_number": <actual draw number from screenshot>,
    "draw_date": "YYYY-MM-DD",
    "main_numbers": [<exactly {num_main} numbers from screenshot>],
    {bonus_line}
    "divisions": [
        {{"division": 1, "winners": <count>, "prize": "<amount>"}},
        ... ({num_divisions} divisions total)
    ]
}}

IMPORTANT: Only extract numbers that are clearly visible in the screenshot."""

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
            logger.info(f"Extracted {lottery_type}: Draw {result.get('draw_number')}, Date: {result.get('draw_date')}")
            return result
        
    except Exception as e:
        logger.error(f"Failed to extract from {image_path}: {e}")
    
    return None

def save_to_database(data):
    """Save extracted lottery data to database"""
    
    with app.app_context():
        try:
            lottery_type = data['lottery_type']
            draw_number = data['draw_number']
            
            # Check if exists
            existing = db.session.query(LotteryResult).filter_by(
                lottery_type=lottery_type,
                draw_number=draw_number
            ).first()
            
            if existing:
                # Update existing
                existing.draw_date = datetime.strptime(data['draw_date'], '%Y-%m-%d').date()
                existing.main_numbers = data['main_numbers']
                existing.bonus_numbers = data.get('bonus_numbers', [])
                existing.divisions = json.dumps(data.get('divisions', []))
                logger.info(f"Updated {lottery_type} draw {draw_number}")
            else:
                # Create new
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
            logger.error(f"Database save failed: {e}")
            db.session.rollback()
            return False

def main():
    """Process all available screenshots"""
    
    client = setup_gemini()
    screenshots_dir = 'screenshots'
    
    # Find all lottery screenshots
    screenshot_files = []
    for f in os.listdir(screenshots_dir):
        if f.endswith('.png') and any(x in f.lower() for x in ['lotto', 'powerball', 'daily']):
            screenshot_files.append(f)
    
    # Sort by date (newest first)
    screenshot_files.sort(reverse=True)
    
    # Process only the most recent screenshot for each lottery type
    processed_types = set()
    success_count = 0
    
    for screenshot in screenshot_files:
        # Determine lottery type
        filename_lower = screenshot.lower()
        if 'daily_lotto' in filename_lower:
            lottery_type = 'DAILY LOTTO'
        elif 'powerball_plus' in filename_lower:
            lottery_type = 'POWERBALL PLUS'
        elif 'powerball' in filename_lower and 'plus' not in filename_lower:
            lottery_type = 'POWERBALL'
        elif 'lotto_plus_2' in filename_lower:
            lottery_type = 'LOTTO PLUS 2'
        elif 'lotto_plus_1' in filename_lower:
            lottery_type = 'LOTTO PLUS 1'
        elif 'lotto' in filename_lower:
            lottery_type = 'LOTTO'
        else:
            continue
        
        # Skip if already processed
        if lottery_type in processed_types:
            continue
        
        processed_types.add(lottery_type)
        
        logger.info(f"\nProcessing {lottery_type} from {screenshot}...")
        image_path = os.path.join(screenshots_dir, screenshot)
        
        # Extract data
        data = extract_from_screenshot(client, image_path)
        if data:
            if save_to_database(data):
                success_count += 1
        else:
            logger.error(f"Failed to extract data from {screenshot}")
    
    # Clear cache
    cache.clear()
    logger.info(f"\nProcessed {len(processed_types)} lottery types, {success_count} successful")
    logger.info("Cache cleared for fresh data")

if __name__ == "__main__":
    logger.info("=== PROCESSING EXISTING SCREENSHOTS WITH GEMINI 2.5 PRO ===")
    main()