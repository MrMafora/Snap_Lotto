#!/usr/bin/env python3
"""
Fix the missing prize division data for recent lottery entries
by reprocessing the screenshots with comprehensive extraction
"""

import os
import json
import psycopg2
import google.generativeai as genai
from datetime import datetime
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def fix_missing_prize_data():
    """Reprocess screenshots to get complete prize division data for records 111, 112, 113"""
    
    # Get API key
    api_key = os.environ.get("GOOGLE_API_KEY_SNAP_LOTTERY")
    if not api_key:
        logger.error("Missing GOOGLE_API_KEY_SNAP_LOTTERY")
        return {'success': False, 'error': 'Missing API key'}
    
    # Initialize Gemini
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel('gemini-2.0-flash-exp')
    
    # Target records to fix
    records_to_fix = [
        {'id': 111, 'lottery_type': 'POWERBALL', 'draw_number': 1635, 'screenshot': 'screenshots/20250722_231402_powerball.png'},
        {'id': 112, 'lottery_type': 'POWERBALL PLUS', 'draw_number': 1635, 'screenshot': 'screenshots/20250722_231412_powerball_plus.png'},
        {'id': 113, 'lottery_type': 'DAILY LOTTO', 'draw_number': 2321, 'screenshot': 'screenshots/20250722_231423_daily_lotto.png'}
    ]
    
    db_url = os.environ.get("DATABASE_URL")
    conn = psycopg2.connect(db_url)
    cur = conn.cursor()
    
    fixed_count = 0
    
    for record in records_to_fix:
        try:
            screenshot_path = record['screenshot']
            if not os.path.exists(screenshot_path):
                logger.warning(f"Screenshot not found: {screenshot_path}")
                continue
                
            logger.info(f"Reprocessing {record['lottery_type']} Draw {record['draw_number']}")
            
            # Read image
            with open(screenshot_path, "rb") as f:
                image_data = f.read()
            
            # Comprehensive extraction prompt
            prompt = f"""
            Extract complete lottery information from this South African {record['lottery_type']} lottery screenshot.
            Focus on extracting ALL prize divisions with winners and prize amounts.
            Return JSON with this exact format:
            {{
                "lottery_type": "{record['lottery_type']}",
                "draw_number": {record['draw_number']},
                "draw_date": "2025-07-22",
                "main_numbers": [1,2,3,4,5],
                "bonus_numbers": [1],
                "prize_divisions": [
                    {{"match": "5+PB", "winners": 0, "prize_per_winner": "R50,000,000.00"}},
                    {{"match": "4+PB", "winners": 2, "prize_per_winner": "R100,000.00"}},
                    {{"match": "5", "winners": 12, "prize_per_winner": "R5,000.00"}},
                    {{"match": "4", "winners": 345, "prize_per_winner": "R500.00"}},
                    {{"match": "3+PB", "winners": 678, "prize_per_winner": "R300.00"}},
                    {{"match": "3", "winners": 9012, "prize_per_winner": "R100.00"}},
                    {{"match": "2+PB", "winners": 12345, "prize_per_winner": "R60.00"}},
                    {{"match": "1+PB", "winners": 67890, "prize_per_winner": "R20.00"}},
                    {{"match": "PB", "winners": 123456, "prize_per_winner": "R10.00"}}
                ],
                "rollover_amount": "R5,000,000.00",
                "next_jackpot": "R85,000,000.00",
                "total_sales": "R25,000,000.00",
                "confidence": 95
            }}
            
            IMPORTANT: 
            - For POWERBALL/POWERBALL PLUS: Use "PB" for PowerBall matches (5+PB, 4+PB, 3+PB, 2+PB, 1+PB, PB)
            - For DAILY LOTTO: Use matches like "5", "4", "3", "2" (no bonus numbers)
            - Extract ALL visible prize divisions and financial data
            - Return clean JSON without markdown formatting
            """
            
            # Call Gemini
            response = model.generate_content([prompt, {"mime_type": "image/png", "data": image_data}])
            
            # Parse JSON response
            response_text = response.text.strip()
            if response_text.startswith('```json'):
                response_text = response_text[7:-3].strip()
            elif response_text.startswith('```'):
                response_text = response_text[3:-3].strip()
            
            data = json.loads(response_text)
            confidence = data.get('confidence', 0)
            
            logger.info(f"Extracted complete data - {confidence}% confidence, {len(data.get('prize_divisions', []))} prize divisions")
            
            # Update the record with complete data
            cur.execute("""
                UPDATE lottery_results SET
                    prize_divisions = %s,
                    rollover_amount = %s,
                    next_jackpot = %s,
                    total_sales = %s,
                    updated_at = %s
                WHERE id = %s
            """, (
                json.dumps(data.get('prize_divisions', [])),
                data.get('rollover_amount'),
                data.get('next_jackpot'),
                data.get('total_sales'),
                datetime.now(),
                record['id']
            ))
            
            conn.commit()
            fixed_count += 1
            logger.info(f"✅ Updated record ID {record['id']} with complete prize data")
            
        except Exception as e:
            logger.error(f"Failed to fix record {record['id']}: {e}")
            continue
    
    conn.close()
    
    logger.info(f"Fixed {fixed_count} records with complete prize division data")
    return {'success': True, 'fixed_count': fixed_count}

if __name__ == "__main__":
    result = fix_missing_prize_data()
    print(f"Fix result: {result}")