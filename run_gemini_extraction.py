#!/usr/bin/env python3
"""
Run Gemini extraction on existing screenshots to get current lottery data
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
        logger.info("Gemini 2.5 Pro configured successfully")
        return model
    except Exception as e:
        logger.error(f"Failed to setup Gemini: {str(e)}")
        return None

def extract_from_attached_assets():
    """Extract lottery data from the latest attached asset images"""
    logger.info("=== EXTRACTING FROM ATTACHED ASSETS ===")
    
    model = setup_gemini()
    if not model:
        return False
        
    # Use the images from attached_assets folder that contain current lottery data
    asset_files = [
        'attached_assets/20250620_190121_lotto_1750450127873.png',
        'attached_assets/20250620_190128_lotto_plus_1_1750450127873.png', 
        'attached_assets/20250620_190134_lotto_plus_2_1750450127873.png',
        'attached_assets/20250620_190139_powerball_1750450127874.png',
        'attached_assets/20250620_190146_powerball_plus_1750450127874.png',
        'attached_assets/20250620_190152_daily_lotto_1750450127874.png'
    ]
    
    extracted_data = []
    
    for filepath in asset_files:
        if os.path.exists(filepath):
            logger.info(f"Processing: {os.path.basename(filepath)}")
            
            try:
                with open(filepath, 'rb') as f:
                    image_data = f.read()
                    
                prompt = """
                Extract the South African lottery data from this screenshot with EXACT accuracy:

                Return ONLY valid JSON in this format:
                {
                    "lottery_type": "exact lottery name from image",
                    "draw_number": "exact draw number shown",
                    "draw_date": "YYYY-MM-DD format",
                    "main_numbers": [array of main numbers],
                    "bonus_numbers": [array of bonus numbers if any, empty array if none]
                }

                Be extremely precise with:
                - Lottery type name exactly as shown
                - Draw number exactly as displayed
                - Date in correct YYYY-MM-DD format
                - All numbers in correct order
                """
                
                response = model.generate_content([prompt, {"mime_type": "image/png", "data": image_data}])
                raw_response = response.text.strip()
                
                # Extract JSON
                import re
                json_match = re.search(r'\{.*\}', raw_response, re.DOTALL)
                if json_match:
                    json_text = json_match.group(0)
                    data = json.loads(json_text)
                    
                    if 'lottery_type' in data and 'draw_number' in data:
                        extracted_data.append(data)
                        logger.info(f"✓ {data['lottery_type']} - Draw {data['draw_number']}")
                    
            except Exception as e:
                logger.error(f"Failed to process {filepath}: {str(e)}")
                continue
    
    # Save extracted data
    if extracted_data:
        with open('gemini_extracted_data.json', 'w') as f:
            json.dump(extracted_data, f, indent=2)
        logger.info(f"Extracted {len(extracted_data)} lottery results")
        return True
    
    return False

def update_database_with_extracted():
    """Update database with Gemini extracted data"""
    try:
        if not os.path.exists('gemini_extracted_data.json'):
            logger.error("No extracted data file found")
            return False
            
        with open('gemini_extracted_data.json', 'r') as f:
            data = json.load(f)
            
        from sqlalchemy import create_engine
        from sqlalchemy.orm import sessionmaker
        from models import LotteryResult
        
        engine = create_engine(Config.SQLALCHEMY_DATABASE_URI)
        Session = sessionmaker(bind=engine)
        session = Session()
        
        updated_count = 0
        
        for lottery_data in data:
            try:
                # Parse date
                draw_date = datetime.strptime(lottery_data['draw_date'], '%Y-%m-%d').date()
                
                # Check if exists
                existing = session.query(LotteryResult).filter_by(
                    lottery_type=lottery_data['lottery_type'],
                    draw_number=lottery_data['draw_number']
                ).first()
                
                if existing:
                    # Update existing
                    existing.draw_date = draw_date
                    existing.numbers = json.dumps(lottery_data['main_numbers'])
                    existing.bonus_numbers = json.dumps(lottery_data.get('bonus_numbers', []))
                    logger.info(f"Updated: {lottery_data['lottery_type']} Draw {lottery_data['draw_number']}")
                else:
                    # Create new
                    result = LotteryResult()
                    result.lottery_type = lottery_data['lottery_type']
                    result.draw_number = lottery_data['draw_number']
                    result.draw_date = draw_date
                    result.numbers = json.dumps(lottery_data['main_numbers'])
                    result.bonus_numbers = json.dumps(lottery_data.get('bonus_numbers', []))
                    result.source_url = f"https://www.nationallottery.co.za/results/{lottery_data['lottery_type'].lower().replace(' ', '-')}"
                    session.add(result)
                    logger.info(f"Added: {lottery_data['lottery_type']} Draw {lottery_data['draw_number']}")
                
                updated_count += 1
                
            except Exception as e:
                logger.error(f"Failed to save {lottery_data.get('lottery_type', 'unknown')}: {str(e)}")
                continue
        
        session.commit()
        session.close()
        
        logger.info(f"Database updated with {updated_count} lottery results")
        return updated_count > 0
        
    except Exception as e:
        logger.error(f"Database update failed: {str(e)}")
        return False

if __name__ == "__main__":
    logger.info("Starting Gemini extraction and database update...")
    
    if extract_from_attached_assets():
        if update_database_with_extracted():
            logger.info("✓ Complete: Fresh lottery data extracted and saved")
        else:
            logger.error("✗ Failed to update database")
    else:
        logger.error("✗ Failed to extract lottery data")