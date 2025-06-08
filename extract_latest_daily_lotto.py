#!/usr/bin/env python3
"""
Extract June 8th Daily Lotto results from latest screenshots using Google Gemini
"""
import os
import sys
import json
import logging
from datetime import datetime
import PIL.Image
import google.generativeai as genai

# Add the current directory to Python path
sys.path.insert(0, os.getcwd())

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def extract_from_recent_screenshots():
    """Process the most recent screenshot images to find June 8th Daily Lotto"""
    try:
        # Configure Gemini API
        api_key = os.environ.get('GOOGLE_API_KEY_SNAP_LOTTERY')
        if not api_key:
            logger.error("Google API key not found")
            return None
            
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-1.5-pro')
        
        # Check attached_assets for recent images
        assets_dir = "attached_assets"
        recent_images = [
            "IMG_8555_1749420155583.png",
            "IMG_8555_1749420320277.png",
            "IMG_8554_1749418860338.png",
            "IMG_8553_1749418397984.png",
            "IMG_8552_1749418223421.png"
        ]
        
        for image_name in recent_images:
            image_path = os.path.join(assets_dir, image_name)
            if not os.path.exists(image_path):
                continue
                
            logger.info(f"Processing: {image_name}")
            
            # Load image
            image = PIL.Image.open(image_path)
            
            # Detailed prompt for lottery data extraction
            prompt = """Look at this South African lottery screenshot and extract ANY Daily Lotto results visible. Return ONLY valid JSON with this exact structure:

{
  "lottery_type": "DAILY LOTTO",
  "draw_number": "draw number as integer",
  "draw_date": "YYYY-MM-DD format",
  "main_numbers": [array of 5 main winning numbers as integers],
  "bonus_numbers": []
}

CRITICAL RULES:
1. Look for ANY Daily Lotto section in the image
2. Extract EXACT numbers shown for Daily Lotto
3. Daily Lotto has 5 main numbers only (no bonus)
4. Return null if no Daily Lotto data is visible
5. Return only the JSON object, no other text"""

            response = model.generate_content([image, prompt])
            response_text = response.text.strip() if response and response.text else ""
            
            if not response_text or response_text.lower() == 'null':
                logger.info(f"No Daily Lotto data found in {image_name}")
                continue
                
            # Extract JSON from response
            import re
            json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
            if json_match:
                json_text = json_match.group()
                lottery_data = json.loads(json_text)
                
                # Check if this is June 8th data or newer than what we have
                draw_date = lottery_data.get('draw_date', '')
                if draw_date >= '2025-06-08':
                    logger.info(f"Found June 8th+ Daily Lotto: {lottery_data}")
                    return lottery_data
                else:
                    logger.info(f"Found older Daily Lotto from {draw_date}")
                    
        logger.info("No June 8th Daily Lotto results found in recent screenshots")
        return None
        
    except Exception as e:
        logger.error(f"Error processing screenshots: {e}")
        return None

def save_to_database(lottery_data):
    """Save extracted lottery data to database"""
    try:
        from main import app
        from models import db, LotteryResult
        
        with app.app_context():
            # Check if this result already exists
            existing = LotteryResult.query.filter_by(
                lottery_type=lottery_data['lottery_type'],
                draw_number=lottery_data['draw_number']
            ).first()
            
            if existing:
                logger.info(f"Result already exists: {lottery_data['lottery_type']} Draw {lottery_data['draw_number']}")
                return False
                
            # Create new lottery result
            new_result = LotteryResult(
                lottery_type=lottery_data['lottery_type'],
                draw_number=lottery_data['draw_number'],
                draw_date=datetime.strptime(lottery_data['draw_date'], '%Y-%m-%d'),
                main_numbers=json.dumps(lottery_data['main_numbers']),
                bonus_numbers=json.dumps(lottery_data['bonus_numbers'])
            )
            
            db.session.add(new_result)
            db.session.commit()
            
            logger.info(f"Successfully saved: {lottery_data['lottery_type']} Draw {lottery_data['draw_number']}")
            return True
            
    except Exception as e:
        logger.error(f"Database error: {e}")
        return False

if __name__ == "__main__":
    logger.info("Searching for June 8th Daily Lotto results in recent screenshots...")
    
    lottery_data = extract_from_recent_screenshots()
    
    if lottery_data:
        success = save_to_database(lottery_data)
        if success:
            logger.info("June 8th Daily Lotto results successfully added to database")
        else:
            logger.info("Data already exists in database")
    else:
        logger.info("No June 8th Daily Lotto results found - database remains with June 7th data")