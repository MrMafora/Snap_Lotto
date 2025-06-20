#!/usr/bin/env python3
"""
Extract current authentic South African lottery data from June 20, 2025 screenshots
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

def extract_lottery_data(model, image_path, expected_type):
    """Extract lottery data from screenshot"""
    try:
        if not os.path.exists(image_path):
            logger.warning(f"Image not found: {image_path}")
            return None
            
        logger.info(f"Processing {expected_type}: {os.path.basename(image_path)}")
        
        # Upload image to Gemini
        image_file = genai.upload_file(image_path)
        
        prompt = f"""
        Extract the lottery data from this {expected_type} screenshot. 
        
        Return ONLY a JSON object with this exact format:
        {{
            "lottery_type": "{expected_type}",
            "draw_number": draw_number_as_integer,
            "draw_date": "YYYY-MM-DD",
            "main_numbers": [list of main numbers as integers],
            "bonus_numbers": [list of bonus numbers as integers, empty if none]
        }}
        
        Extract ONLY the exact numbers shown in the image. Do not modify any numbers.
        """
        
        response = model.generate_content([prompt, image_file])
        
        if response and response.text:
            response_text = response.text.strip()
            if response_text.startswith('```json'):
                response_text = response_text[7:]
            if response_text.endswith('```'):
                response_text = response_text[:-3]
            response_text = response_text.strip()
            
            data = json.loads(response_text)
            logger.info(f"✓ {expected_type} - Draw {data.get('draw_number')} extracted")
            return data
            
    except Exception as e:
        logger.error(f"Failed to extract {expected_type}: {str(e)}")
        return None

def save_authentic_data(lottery_data):
    """Save authentic lottery data to database"""
    try:
        from main import app, db
        from models import LotteryResult
        
        with app.app_context():
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

def main():
    """Extract all current authentic lottery data"""
    logger.info("=== EXTRACTING CURRENT AUTHENTIC SA LOTTERY DATA ===")
    
    model = setup_gemini()
    if not model:
        return False
        
    # Current lottery screenshots from June 20, 2025
    lottery_files = [
        ('attached_assets/20250620_190121_lotto_1750450127873.png', 'LOTTO'),
        ('attached_assets/20250620_190128_lotto_plus_1_1750450127873.png', 'LOTTO PLUS 1'),
        ('attached_assets/20250620_190134_lotto_plus_2_1750450127873.png', 'LOTTO PLUS 2'),
        ('attached_assets/20250620_190139_powerball_1750450127874.png', 'PowerBall'),
        ('attached_assets/20250620_190146_powerball_plus_1750450127874.png', 'POWERBALL PLUS'),
        ('attached_assets/20250620_190152_daily_lotto_1750450127874.png', 'DAILY LOTTO')
    ]
    
    success_count = 0
    
    for image_path, lottery_type in lottery_files:
        data = extract_lottery_data(model, image_path, lottery_type)
        if data and save_authentic_data(data):
            success_count += 1
    
    logger.info(f"Successfully extracted and saved {success_count} authentic lottery results")
    return success_count == 6

if __name__ == "__main__":
    main()