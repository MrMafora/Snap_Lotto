#!/usr/bin/env python3
"""
Quick extraction of authentic South African lottery data from official screenshots
"""

import os
import json
import logging
from datetime import datetime
import google.generativeai as genai
from config import Config

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def setup_gemini():
    """Configure Google Gemini API"""
    try:
        api_key = Config.GOOGLE_API_KEY
        if not api_key:
            logger.error("Google API key not found")
            return None
            
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-2.0-flash-exp')
        logger.info("Gemini configured successfully")
        return model
    except Exception as e:
        logger.error(f"Failed to setup Gemini: {str(e)}")
        return None

def extract_from_screenshot(model, image_path, lottery_type):
    """Extract lottery data from a single screenshot"""
    try:
        if not os.path.exists(image_path):
            logger.warning(f"Image not found: {image_path}")
            return None
            
        logger.info(f"Processing {lottery_type}: {os.path.basename(image_path)}")
        
        # Upload image
        image_file = genai.upload_file(image_path)
        
        # Enhanced prompt for accurate extraction
        prompt = f"""
        Extract the EXACT lottery data from this {lottery_type} screenshot.
        
        Return ONLY a JSON object with this format:
        {{
            "lottery_type": "{lottery_type}",
            "draw_number": actual_draw_number_as_integer,
            "draw_date": "YYYY-MM-DD",
            "main_numbers": [list of main numbers as integers],
            "bonus_numbers": [list of bonus numbers as integers, empty array if none]
        }}
        
        CRITICAL: Extract the EXACT numbers shown in the image. Do not modify or generate any numbers.
        """
        
        # Get response from Gemini
        response = model.generate_content([prompt, image_file])
        
        if response and response.text:
            # Clean up response text
            response_text = response.text.strip()
            if response_text.startswith('```json'):
                response_text = response_text[7:]
            if response_text.endswith('```'):
                response_text = response_text[:-3]
            response_text = response_text.strip()
            
            # Parse JSON
            data = json.loads(response_text)
            logger.info(f"✓ {lottery_type} - Draw {data.get('draw_number')}")
            return data
            
    except Exception as e:
        logger.error(f"Failed to extract from {lottery_type}: {str(e)}")
        return None

def save_to_database(lottery_data):
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
            
            db.session.add(result)
            db.session.commit()
            
            logger.info(f"✓ Saved {lottery_data['lottery_type']} to database")
            return True
        
    except Exception as e:
        logger.error(f"Failed to save to database: {str(e)}")
        return False

def main():
    """Main extraction process"""
    logger.info("=== EXTRACTING AUTHENTIC SOUTH AFRICAN LOTTERY DATA ===")
    
    model = setup_gemini()
    if not model:
        return False
        
    # Define lottery screenshots with current authentic data
    lottery_files = [
        ('attached_assets/20250620_190121_lotto_1750450127873.png', 'LOTTO'),
        ('attached_assets/20250620_190128_lotto_plus_1_1750450127873.png', 'LOTTO PLUS 1'),
        ('attached_assets/20250620_190134_lotto_plus_2_1750450127873.png', 'LOTTO PLUS 2'),
        ('attached_assets/20250620_190139_powerball_1750450127874.png', 'PowerBall'),
        ('attached_assets/20250620_190146_powerball_plus_1750450127874.png', 'POWERBALL PLUS'),
        ('attached_assets/20250620_190152_daily_lotto_1750450127874.png', 'DAILY LOTTO')
    ]
    
    extracted_count = 0
    
    for image_path, lottery_type in lottery_files:
        data = extract_from_screenshot(model, image_path, lottery_type)
        if data and save_to_database(data):
            extracted_count += 1
    
    logger.info(f"Successfully extracted and saved {extracted_count} authentic lottery results")
    return extracted_count > 0

if __name__ == "__main__":
    main()