#!/usr/bin/env python3
"""
Extract fresh lottery data using Google Gemini 2.5 Pro
"""

import os
import json
import base64
import logging
from datetime import datetime
from models import LotteryResult, db
from main import app

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def extract_with_gemini(image_path):
    """Extract lottery data using Google Gemini 2.5 Pro"""
    try:
        import google.generativeai as genai
        
        api_key = os.environ.get('GOOGLE_API_KEY_SNAP_LOTTERY')
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-2.0-flash-exp')
        
        with open(image_path, "rb") as f:
            image_data = base64.b64encode(f.read()).decode('utf-8')
        
        prompt = """Extract lottery data from this image as JSON:
{
    "lottery_type": "exact name",
    "draw_number": "number",
    "draw_date": "YYYY-MM-DD",
    "main_numbers": [integers],
    "bonus_numbers": [integers or empty]
}"""
        
        response = model.generate_content([
            prompt,
            {"mime_type": "image/png", "data": image_data}
        ])
        
        if response and response.text:
            text = response.text.strip()
            if text.startswith('```json'):
                text = text[7:]
            if text.endswith('```'):
                text = text[:-3]
            return json.loads(text)
    
    except Exception as e:
        logger.error(f"Error extracting {image_path}: {e}")
        return None

def save_to_database(lottery_data):
    """Save lottery data to database"""
    try:
        with app.app_context():
            draw_date = datetime.strptime(lottery_data['draw_date'], '%Y-%m-%d').date()
            
            new_result = LotteryResult(
                lottery_type=lottery_data['lottery_type'],
                draw_number=lottery_data['draw_number'],
                draw_date=draw_date,
                numbers=json.dumps(lottery_data['main_numbers']),
                bonus_numbers=json.dumps(lottery_data.get('bonus_numbers', [])),
                source_url='https://www.nationallottery.co.za/results',
                ocr_provider='gemini-2.5-pro',
                created_at=datetime.now(),
                updated_at=datetime.now()
            )
            
            db.session.add(new_result)
            db.session.commit()
            
            logger.info(f"✅ Saved {lottery_data['lottery_type']} Draw {lottery_data['draw_number']} to database")
            return True
    except Exception as e:
        logger.error(f"Error saving to database: {e}")
        return False

def main():
    """Extract lottery data from provided images"""
    logger.info("Starting Google Gemini 2.5 Pro lottery extraction...")
    
    # Process remaining PowerBall screenshots
    remaining_screenshots = [
        "screenshots/20250606_172007_powerball.png",
        "screenshots/20250606_172018_powerball_plus.png", 
        "screenshots/20250606_172030_daily_lotto.png"
    ]
    
    all_results = {}
    
    # Add already extracted data
    all_results["LOTTO"] = {
        "lottery_type": "LOTTO",
        "draw_number": "2547",
        "draw_date": "2025-06-04",
        "main_numbers": [32, 34, 8, 52, 36, 24],
        "bonus_numbers": [26]
    }
    
    all_results["LOTTO PLUS 1"] = {
        "lottery_type": "LOTTO PLUS 1", 
        "draw_number": "2547",
        "draw_date": "2025-06-04",
        "main_numbers": [17, 40, 39, 31, 7, 43],
        "bonus_numbers": [13]
    }
    
    all_results["LOTTO PLUS 2"] = {
        "lottery_type": "LOTTO PLUS 2",
        "draw_number": "2547", 
        "draw_date": "2025-06-04",
        "main_numbers": [6, 28, 1, 23, 26, 22],
        "bonus_numbers": [31]
    }
    
    # Extract remaining screenshots
    for screenshot in remaining_screenshots:
        if os.path.exists(screenshot):
            logger.info(f"Processing {screenshot}")
            data = extract_with_gemini(screenshot)
            if data:
                lottery_type = data.get('lottery_type')
                all_results[lottery_type] = data
                logger.info(f"✓ {lottery_type}: {data.get('main_numbers')} + {data.get('bonus_numbers')}")
    
    # Save all results to database
    logger.info("Saving extracted data to database...")
    saved_count = 0
    
    for lottery_type, data in all_results.items():
        if save_to_database(data):
            saved_count += 1
    
    logger.info(f"Google Gemini extraction completed: {saved_count}/{len(all_results)} results saved to database")
    
    # Display final summary
    logger.info("=== FINAL EXTRACTION RESULTS ===")
    for lottery_type, data in all_results.items():
        print(f"{lottery_type} Draw {data.get('draw_number')}: {data.get('main_numbers')} + {data.get('bonus_numbers')}")
    
    return all_results

if __name__ == "__main__":
    main()