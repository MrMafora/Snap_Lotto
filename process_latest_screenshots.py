#!/usr/bin/env python3
"""
Process latest screenshot images to extract and update lottery data
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

def extract_lottery_data_from_image(image_path):
    """Extract lottery data from a screenshot using Google Gemini"""
    try:
        # Configure Gemini API
        api_key = os.environ.get('GOOGLE_API_KEY_SNAP_LOTTERY')
        if not api_key:
            logger.error("Google API key not found")
            return None
            
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-1.5-pro')
        
        # Load image
        image = PIL.Image.open(image_path)
        
        # Detailed prompt for lottery data extraction
        prompt = """Extract lottery results from this South African lottery screenshot. Return ONLY valid JSON with this exact structure:

{
  "lottery_type": "LOTTO|LOTTO PLUS 1|LOTTO PLUS 2|POWERBALL|POWERBALL PLUS|DAILY LOTTO",
  "draw_number": "draw number as integer",
  "draw_date": "YYYY-MM-DD format",
  "main_numbers": [array of main winning numbers as integers],
  "bonus_numbers": [array of bonus/powerball numbers as integers, empty array if none]
}

CRITICAL RULES:
1. Extract EXACT numbers shown in the winning numbers section
2. For LOTTO/LOTTO PLUS: 6 main numbers + 1 bonus ball
3. For POWERBALL/POWERBALL PLUS: 5 main numbers + 1 powerball
4. For DAILY LOTTO: 5 main numbers only (no bonus)
5. Return only the JSON object, no other text"""

        response = model.generate_content([image, prompt])
        response_text = response.text.strip() if response and response.text else ""
        
        if not response_text:
            logger.error(f"Empty response from Gemini for {image_path}")
            return None
            
        # Extract JSON from response
        import re
        json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
        if json_match:
            json_text = json_match.group()
            return json.loads(json_text)
        else:
            logger.error(f"No valid JSON found in response for {image_path}")
            return None
            
    except Exception as e:
        logger.error(f"Error processing {image_path}: {e}")
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
                draw_date=datetime.strptime(lottery_data['draw_date'], '%Y-%m-%d').date(),
                main_numbers=json.dumps(lottery_data['main_numbers']),
                bonus_numbers=json.dumps(lottery_data['bonus_numbers']),
                ocr_provider='google_gemini_2_5_pro'
            )
            
            db.session.add(new_result)
            db.session.commit()
            
            logger.info(f"Successfully saved: {lottery_data['lottery_type']} Draw {lottery_data['draw_number']}")
            return True
            
    except Exception as e:
        logger.error(f"Database error: {e}")
        return False

def process_latest_screenshots():
    """Process all screenshots in the screenshots directory"""
    screenshots_dir = "screenshots"
    
    if not os.path.exists(screenshots_dir):
        logger.error("Screenshots directory not found")
        return False
        
    # Get all PNG files in screenshots directory
    screenshot_files = [f for f in os.listdir(screenshots_dir) if f.endswith('.png')]
    screenshot_files.sort()  # Process in order
    
    processed_count = 0
    new_results_count = 0
    
    for filename in screenshot_files:
        filepath = os.path.join(screenshots_dir, filename)
        logger.info(f"Processing: {filename}")
        
        # Extract lottery data
        lottery_data = extract_lottery_data_from_image(filepath)
        
        if lottery_data:
            logger.info(f"Extracted: {lottery_data['lottery_type']} Draw {lottery_data['draw_number']}")
            
            # Save to database
            if save_to_database(lottery_data):
                new_results_count += 1
                
            processed_count += 1
        else:
            logger.warning(f"Failed to extract data from {filename}")
    
    logger.info(f"Processing complete: {processed_count} processed, {new_results_count} new results added")
    return new_results_count > 0

if __name__ == "__main__":
    success = process_latest_screenshots()
    sys.exit(0 if success else 1)