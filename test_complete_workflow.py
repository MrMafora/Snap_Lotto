#!/usr/bin/env python3
"""
Test the complete automation workflow with proper Gemini extraction
"""

import os
import sys
import json
import logging
from datetime import datetime
import google.generativeai as genai
from config import Config

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def setup_gemini():
    """Configure Google Gemini API"""
    try:
        api_key = Config.GOOGLE_API_KEY
        if not api_key:
            logger.error("Google API key not found in environment")
            return None
            
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-2.0-flash-exp')
        logger.info("Gemini 2.0 Flash configured successfully")
        return model
    except Exception as e:
        logger.error(f"Failed to setup Gemini: {str(e)}")
        return None

def extract_from_screenshots():
    """Extract lottery data from current screenshots using Gemini"""
    logger.info("=== EXTRACTING LOTTERY DATA FROM SCREENSHOTS ===")
    
    model = setup_gemini()
    if not model:
        return []
        
    # Process the user's attached asset images that contain current lottery data
    screenshot_files = [
        'attached_assets/20250620_190121_lotto_1750450127873.png',
        'attached_assets/20250620_190128_lotto_plus_1_1750450127873.png',
        'attached_assets/20250620_190134_lotto_plus_2_1750450127873.png',
        'attached_assets/20250620_190139_powerball_1750450127874.png',
        'attached_assets/20250620_190146_powerball_plus_1750450127874.png',
        'attached_assets/20250620_190152_daily_lotto_1750450127874.png'
    ]
    
    extracted_results = []
    
    for filepath in screenshot_files:
        if not os.path.exists(filepath):
            logger.warning(f"Screenshot not found: {filepath}")
            continue
            
        logger.info(f"Processing: {os.path.basename(filepath)}")
        
        try:
            with open(filepath, 'rb') as f:
                image_data = f.read()
                
            # Enhanced prompt for accurate extraction
            prompt = """
            Extract South African lottery data from this screenshot with complete accuracy.
            
            Return ONLY valid JSON in this exact format:
            {
                "lottery_type": "exact lottery name as shown",
                "draw_number": "exact draw number from image",
                "draw_date": "YYYY-MM-DD format",
                "main_numbers": [list of main winning numbers],
                "bonus_numbers": [list of bonus numbers or empty array]
            }
            
            Critical requirements:
            - Extract the exact draw number shown in the image
            - Use precise lottery type name (LOTTO, LOTTO PLUS 1, LOTTO PLUS 2, PowerBall, POWERBALL PLUS, DAILY LOTTO)
            - Format date as YYYY-MM-DD
            - Include all visible numbers in correct order
            """
            
            response = model.generate_content([prompt, {"mime_type": "image/png", "data": image_data}])
            response_text = response.text.strip()
            
            # Extract JSON from response
            import re
            json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
            if json_match:
                json_text = json_match.group(0)
                data = json.loads(json_text)
                
                # Validate required fields
                if all(key in data for key in ['lottery_type', 'draw_number', 'draw_date', 'main_numbers']):
                    extracted_results.append(data)
                    logger.info(f"✓ Extracted: {data['lottery_type']} - Draw {data['draw_number']}")
                else:
                    logger.warning(f"Invalid data structure: {data}")
            else:
                logger.warning(f"No JSON found in response: {response_text[:200]}")
                
        except Exception as e:
            logger.error(f"Failed to process {filepath}: {str(e)}")
            continue
    
    return extracted_results

def update_database(lottery_results):
    """Update database with extracted lottery results"""
    logger.info("=== UPDATING DATABASE WITH EXTRACTED RESULTS ===")
    
    if not lottery_results:
        logger.error("No lottery results to update")
        return False
        
    try:
        from sqlalchemy import create_engine
        from sqlalchemy.orm import sessionmaker
        from models import LotteryResult
        
        engine = create_engine(Config.SQLALCHEMY_DATABASE_URI)
        Session = sessionmaker(bind=engine)
        session = Session()
        
        updated_count = 0
        
        for data in lottery_results:
            try:
                # Parse date
                draw_date = datetime.strptime(data['draw_date'], '%Y-%m-%d').date()
                
                # Find existing record or create new one
                existing = session.query(LotteryResult).filter_by(
                    lottery_type=data['lottery_type']
                ).order_by(LotteryResult.created_at.desc()).first()
                
                if existing:
                    # Update existing record with current draw data
                    existing.draw_number = int(data['draw_number'])
                    existing.draw_date = draw_date
                    existing.main_numbers = json.dumps(data['main_numbers'])
                    existing.bonus_numbers = json.dumps(data.get('bonus_numbers', []))
                    logger.info(f"Updated: {data['lottery_type']} - Draw {data['draw_number']}")
                else:
                    # Create new record
                    result = LotteryResult()
                    result.lottery_type = data['lottery_type']
                    result.draw_number = int(data['draw_number'])
                    result.draw_date = draw_date
                    result.main_numbers = json.dumps(data['main_numbers'])
                    result.bonus_numbers = json.dumps(data.get('bonus_numbers', []))
                    session.add(result)
                    logger.info(f"Created: {data['lottery_type']} - Draw {data['draw_number']}")
                
                updated_count += 1
                
            except Exception as e:
                logger.error(f"Failed to save {data.get('lottery_type', 'unknown')}: {str(e)}")
                continue
        
        session.commit()
        session.close()
        
        logger.info(f"Successfully updated {updated_count} lottery records")
        return updated_count > 0
        
    except Exception as e:
        logger.error(f"Database update failed: {str(e)}")
        return False

if __name__ == "__main__":
    logger.info("Starting complete lottery data extraction and update workflow...")
    
    # Extract lottery data using Gemini
    results = extract_from_screenshots()
    
    if results:
        logger.info(f"Extracted {len(results)} lottery results")
        
        # Save extracted data
        with open('test_complete_workflow.json', 'w') as f:
            json.dump(results, f, indent=2)
        
        # Update database
        if update_database(results):
            logger.info("✓ Complete workflow successful - lottery data updated with current draw numbers")
        else:
            logger.error("✗ Failed to update database")
    else:
        logger.error("✗ No lottery results extracted")