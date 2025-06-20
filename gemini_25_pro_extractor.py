#!/usr/bin/env python3
"""
Google Gemini 2.5 Pro Lottery Data Extractor
Accurately extracts South African lottery data from official screenshots
"""

import os
import json
import logging
from datetime import datetime
from google import genai
from google.genai import types

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def setup_gemini_25_pro():
    """Configure Google Gemini 2.5 Pro API"""
    try:
        api_key = os.environ.get('GOOGLE_API_KEY_SNAP_LOTTERY')
        if not api_key:
            logger.error("GOOGLE_API_KEY_SNAP_LOTTERY not found in environment")
            return None
            
        client = genai.Client(api_key=api_key)
        logger.info("Google Gemini 2.5 Pro configured successfully")
        return client
    except Exception as e:
        logger.error(f"Failed to setup Gemini 2.5 Pro: {str(e)}")
        return None

def extract_lottery_data_with_gemini(client, image_path, lottery_type):
    """Extract lottery data using Gemini 2.5 Pro"""
    try:
        if not os.path.exists(image_path):
            logger.warning(f"Image not found: {image_path}")
            return None
            
        logger.info(f"Processing {lottery_type}: {os.path.basename(image_path)}")
        
        # Read image file
        with open(image_path, "rb") as f:
            image_bytes = f.read()
        
        # Enhanced prompt for accurate extraction
        prompt = f"""
        Extract the exact lottery data from this {lottery_type} screenshot from the South African National Lottery website.
        
        Look for:
        1. Draw number (usually 4 digits)
        2. Draw date (format: YYYY-MM-DD)
        3. Main winning numbers (6 numbers for LOTTO types, 5 for PowerBall types, 5 for Daily Lotto)
        4. Bonus/PowerBall number (if applicable)
        
        Return ONLY a JSON object with this exact format:
        {{
            "lottery_type": "{lottery_type}",
            "draw_number": draw_number_as_integer,
            "draw_date": "YYYY-MM-DD",
            "main_numbers": [list of main numbers as integers],
            "bonus_numbers": [bonus number as integer in array, empty array if none]
        }}
        
        CRITICAL: Extract ONLY the exact numbers visible in the image. Do not modify or generate any numbers.
        """
        
        # Generate content with Gemini 2.5 Pro with timeout handling
        response = client.models.generate_content(
            model="gemini-2.5-pro",
            contents=[
                types.Part.from_bytes(
                    data=image_bytes,
                    mime_type="image/png",
                ),
                prompt
            ],
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                temperature=0.1,
                max_output_tokens=1000,
            ),
        )
        
        if response and response.text:
            response_text = response.text.strip()
            
            # Clean JSON response
            if response_text.startswith('```json'):
                response_text = response_text[7:]
            if response_text.endswith('```'):
                response_text = response_text[:-3]
            response_text = response_text.strip()
            
            # Parse JSON
            data = json.loads(response_text)
            logger.info(f"✓ {lottery_type} - Draw {data.get('draw_number')} extracted successfully")
            return data
            
    except Exception as e:
        logger.error(f"Failed to extract {lottery_type}: {str(e)}")
        return None

def save_extracted_data(lottery_data):
    """Save extracted lottery data to database"""
    try:
        from main import app, db
        from models import LotteryResult
        
        with app.app_context():
            # Create new lottery result
            result = LotteryResult()
            result.lottery_type = lottery_data['lottery_type']
            result.draw_number = lottery_data['draw_number']
            result.draw_date = datetime.strptime(lottery_data['draw_date'], '%Y-%m-%d')
            result.numbers = json.dumps(lottery_data['main_numbers'])
            result.bonus_numbers = json.dumps(lottery_data['bonus_numbers']) if lottery_data['bonus_numbers'] else None
            result.created_at = datetime.now()
            result.source_url = f"https://www.nationallottery.co.za/results/{lottery_data['lottery_type'].lower().replace(' ', '-')}"
            
            db.session.add(result)
            db.session.commit()
            
            logger.info(f"✓ Saved {lottery_data['lottery_type']} to database")
            return True
        
    except Exception as e:
        logger.error(f"Failed to save {lottery_data['lottery_type']}: {str(e)}")
        return False

def extract_all_lottery_data():
    """Extract all lottery data using Gemini 2.5 Pro"""
    logger.info("=== GEMINI 2.5 PRO LOTTERY EXTRACTION ===")
    
    client = setup_gemini_25_pro()
    if not client:
        return False
        
    # Latest lottery screenshots
    lottery_files = [
        ('attached_assets/20250620_190121_lotto_1750456254489.png', 'LOTTO'),
        ('attached_assets/20250620_190128_lotto_plus_1_1750456254489.png', 'LOTTO PLUS 1'),
        ('attached_assets/20250620_190134_lotto_plus_2_1750456254489.png', 'LOTTO PLUS 2'),
        ('attached_assets/20250620_190139_powerball_1750456254489.png', 'PowerBall'),
        ('attached_assets/20250620_190146_powerball_plus_1750456254489.png', 'POWERBALL PLUS'),
        ('attached_assets/20250620_190152_daily_lotto_1750456254490.png', 'DAILY LOTTO')
    ]
    
    success_count = 0
    
    # Clear existing data first
    try:
        from main import app, db
        with app.app_context():
            db.session.execute(db.text("DELETE FROM lottery_result"))
            db.session.commit()
            logger.info("Cleared existing lottery data")
    except Exception as e:
        logger.error(f"Failed to clear existing data: {str(e)}")
    
    # Extract and save each lottery type - ONE IMAGE AT A TIME for better accuracy
    for image_path, lottery_type in lottery_files:
        logger.info(f"=== PROCESSING SINGLE IMAGE: {lottery_type} ===")
        logger.info(f"Image: {os.path.basename(image_path)}")
        
        data = extract_lottery_data_with_gemini(client, image_path, lottery_type)
        if data and save_extracted_data(data):
            success_count += 1
            logger.info(f"✓ Successfully processed {lottery_type}")
        else:
            logger.error(f"✗ Failed to process {lottery_type}")
        
        # Brief pause between single image processing
        import time
        time.sleep(0.5)
    
    logger.info(f"Successfully extracted and saved {success_count}/6 authentic lottery results")
    return success_count == 6

if __name__ == "__main__":
    extract_all_lottery_data()