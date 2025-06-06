#!/usr/bin/env python3
"""
Quick Google Gemini extraction on all lottery screenshots
"""

import os
import json
import base64
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def extract_with_gemini(image_path):
    """Extract lottery data using Google Gemini 2.5 Pro"""
    try:
        import google.generativeai as genai
        
        api_key = os.environ.get('GOOGLE_API_KEY_SNAP_LOTTERY')
        if not api_key:
            return None
            
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

def main():
    screenshots = [
        "screenshots/20250606_171929_lotto.png",
        "screenshots/20250606_171942_lotto_plus_1_results.png", 
        "screenshots/20250606_171954_lotto_plus_2_results.png",
        "screenshots/20250606_172007_powerball.png",
        "screenshots/20250606_172018_powerball_plus.png",
        "screenshots/20250606_172030_daily_lotto.png"
    ]
    
    results = {}
    
    for screenshot in screenshots:
        if os.path.exists(screenshot):
            logger.info(f"Processing {screenshot}")
            data = extract_with_gemini(screenshot)
            if data:
                lottery_type = data.get('lottery_type', 'Unknown')
                results[lottery_type] = data
                logger.info(f"✓ {lottery_type}: {data.get('main_numbers')} + {data.get('bonus_numbers')}")
    
    logger.info("=== FINAL RESULTS ===")
    for lottery_type, data in results.items():
        print(f"{lottery_type} Draw {data.get('draw_number')}: {data.get('main_numbers')} + {data.get('bonus_numbers')}")
    
    return results

if __name__ == "__main__":
    main()