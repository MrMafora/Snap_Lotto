#!/usr/bin/env python3
"""
Comprehensive lottery data extraction from screenshots with full prize division details
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

def extract_comprehensive_lottery_data(image_path):
    """Extract complete lottery data including divisions, winners, and financial details"""
    try:
        import google.generativeai as genai
        
        api_key = os.environ.get('GOOGLE_API_KEY_SNAP_LOTTERY')
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-2.0-flash-exp')
        
        with open(image_path, "rb") as f:
            image_data = base64.b64encode(f.read()).decode('utf-8')
        
        # Advanced developer-focused prompt for comprehensive extraction
        advanced_prompt = """You are an automated data extraction API. Your task is to analyze the provided image of a lottery result and return the data in a structured JSON format.

Instructions:
- Strictly adhere to the JSON schema defined below.
- Extract all data points accurately from the image.
- If a field is not present in the image (e.g., a bonus ball in Daily Lotto), use null as its value.
- Parse numbers from strings where specified (e.g., Draw ID, Winners). Currency values should remain as strings to preserve formatting.

JSON Output Schema:
{
  "gameName": "String",
  "drawId": "Number",
  "drawDate": "String (YYYY-MM-DD)",
  "winningNumbers": {
    "asDrawn": ["Array of Numbers"],
    "numericalOrder": ["Array of Numbers"],
    "bonusBall": "Number | null"
  },
  "prizeDivisions": [
    {
      "division": "Number",
      "description": "String",
      "winners": "Number",
      "prizeAmount": "String"
    }
  ],
  "jackpotInfo": {
     "nextJackpot": "String",
     "nextDrawDate": "String (YYYY-MM-DD)"
  },
  "additionalInfo": {
    "rolloverAmount": "String | null",
    "totalPoolSize": "String | null",
    "totalSales": "String | null"
  }
}

Example Extraction Guidelines:
- gameName: Extract from the main title (e.g., "LOTTO PLUS 1").
- drawId: Extract the "DRAW ID" number.
- winningNumbers.bonusBall: This is the number after the + sign.
- prizeDivisions.description: Extract the text description for each prize tier (e.g., "SIX CORRECT NUMBERS", "FIVE CORRECT NUMBERS + BONUS BALL").
- jackpotInfo.nextJackpot: Find the estimated jackpot amount for the next draw, often at the bottom of the page.

Process the attached image and return the JSON output."""

        response = model.generate_content([
            advanced_prompt,
            {"mime_type": "image/png", "data": image_data}
        ])
        
        if response and response.text:
            text = response.text.strip()
            if text.startswith('```json'):
                text = text[7:]
            if text.endswith('```'):
                text = text[:-3]
            
            extracted_data = json.loads(text)
            logger.info(f"✅ Comprehensive extraction successful for {extracted_data.get('gameName')}")
            return extracted_data
    
    except Exception as e:
        logger.error(f"Error in comprehensive extraction for {image_path}: {e}")
        return None

def save_comprehensive_lottery_data(data):
    """Save comprehensive lottery data to database"""
    try:
        with app.app_context():
            # Parse draw date
            draw_date = datetime.strptime(data['drawDate'], '%Y-%m-%d').date()
            
            # Extract winning numbers
            winning_numbers = data['winningNumbers']['asDrawn']
            bonus_numbers = [data['winningNumbers']['bonusBall']] if data['winningNumbers']['bonusBall'] else []
            
            # Create comprehensive lottery result
            new_result = LotteryResult(
                lottery_type=data['gameName'],
                draw_number=str(data['drawId']),
                draw_date=draw_date,
                numbers=json.dumps(winning_numbers),
                bonus_numbers=json.dumps(bonus_numbers),
                source_url='https://www.nationallottery.co.za/results',
                ocr_provider='gemini-2.5-pro-comprehensive'
            )
            
            # Add comprehensive data as JSON metadata if available
            if 'prizeDivisions' in data:
                new_result.metadata = json.dumps({
                    'prize_divisions': data['prizeDivisions'],
                    'jackpot_info': data.get('jackpotInfo', {}),
                    'additional_info': data.get('additionalInfo', {}),
                    'winning_numbers_ordered': data['winningNumbers'].get('numericalOrder', [])
                })
            
            db.session.add(new_result)
            db.session.commit()
            
            logger.info(f"✅ Saved comprehensive data for {data['gameName']} Draw {data['drawId']}")
            return True
            
    except Exception as e:
        logger.error(f"Error saving comprehensive data: {e}")
        db.session.rollback()
        return False

def process_screenshot_comprehensive(image_path):
    """Process a single screenshot with comprehensive extraction"""
    logger.info(f"Processing comprehensive extraction: {image_path}")
    
    extracted_data = extract_comprehensive_lottery_data(image_path)
    if extracted_data:
        success = save_comprehensive_lottery_data(extracted_data)
        
        if success:
            logger.info(f"✅ Complete processing successful for {extracted_data['gameName']}")
            return extracted_data
        else:
            logger.error(f"❌ Database save failed for {extracted_data['gameName']}")
    else:
        logger.error(f"❌ Extraction failed for {image_path}")
    
    return None

def batch_process_screenshots():
    """Process all lottery screenshots with comprehensive extraction"""
    screenshots = [
        "screenshots/20250606_171929_lotto.png",
        "screenshots/20250606_171942_lotto_plus_1_results.png",
        "screenshots/20250606_171954_lotto_plus_2_results.png", 
        "screenshots/20250606_172007_powerball.png",
        "screenshots/20250606_172018_powerball_plus.png",
        "screenshots/20250606_172030_daily_lotto.png"
    ]
    
    logger.info("=== STARTING COMPREHENSIVE LOTTERY EXTRACTION ===")
    
    results = []
    successful_extractions = 0
    
    for screenshot in screenshots:
        if os.path.exists(screenshot):
            result = process_screenshot_comprehensive(screenshot)
            if result:
                results.append(result)
                successful_extractions += 1
                
                # Display summary for this extraction
                game_name = result.get('gameName', 'Unknown')
                draw_id = result.get('drawId', 'Unknown')
                winning_nums = result.get('winningNumbers', {}).get('asDrawn', [])
                bonus_ball = result.get('winningNumbers', {}).get('bonusBall')
                
                logger.info(f"📊 {game_name} Draw {draw_id}: {winning_nums} + [{bonus_ball}]")
                
                # Show prize divisions if available
                divisions = result.get('prizeDivisions', [])
                if divisions:
                    logger.info(f"   Prize Divisions: {len(divisions)} tiers")
                    for div in divisions[:3]:  # Show first 3 divisions
                        logger.info(f"   Div {div.get('division')}: {div.get('winners')} winners @ {div.get('prizeAmount')}")
        else:
            logger.warning(f"Screenshot not found: {screenshot}")
    
    logger.info(f"=== COMPREHENSIVE EXTRACTION COMPLETE: {successful_extractions}/{len(screenshots)} successful ===")
    return results

if __name__ == "__main__":
    batch_process_screenshots()