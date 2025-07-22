#!/usr/bin/env python3
"""
Simple AI Workflow Integration
Processes existing screenshots with working Google Gemini AI
"""

import os
import json
import glob
import logging
import psycopg2
from datetime import datetime
import google.generativeai as genai

def process_available_screenshots():
    """Process available screenshots with AI"""
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)
    
    logger.info("Starting AI processing of available screenshots...")
    
    # Check API key
    api_key = os.environ.get("GOOGLE_API_KEY_SNAP_LOTTERY")
    if not api_key:
        logger.error("Missing GOOGLE_API_KEY_SNAP_LOTTERY")
        return {'success': False, 'error': 'Missing API key'}
    
    # Initialize Gemini
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel('gemini-2.0-flash-exp')
    
    # Find screenshots 
    screenshots = glob.glob('screenshots/*.png') + glob.glob('uploads/*.png')
    if not screenshots:
        logger.error("No screenshots found")
        return {'success': False, 'error': 'No screenshots found'}
    
    processed = 0
    new_results = []
    
    # Process up to 3 screenshots for testing
    for screenshot_path in screenshots[:3]:
        try:
            logger.info(f"Processing: {screenshot_path}")
            
            # Read image
            with open(screenshot_path, "rb") as f:
                image_data = f.read()
            
            # Comprehensive extraction prompt including prize divisions
            prompt = """
            Extract complete lottery information from this South African lottery screenshot including all prize divisions.
            Return JSON with this exact format:
            {
                "lottery_type": "LOTTO",
                "draw_number": 2560,
                "draw_date": "2025-07-22",
                "main_numbers": [1,2,3,4,5,6],
                "bonus_numbers": [7],
                "prize_divisions": [
                    {"match": "6", "winners": 0, "prize_per_winner": "R8,000,000.00"},
                    {"match": "5+B", "winners": 2, "prize_per_winner": "R100,000.00"},
                    {"match": "5", "winners": 45, "prize_per_winner": "R5,000.00"},
                    {"match": "4+B", "winners": 123, "prize_per_winner": "R1,200.00"},
                    {"match": "4", "winners": 2156, "prize_per_winner": "R200.00"},
                    {"match": "3+B", "winners": 4567, "prize_per_winner": "R100.00"},
                    {"match": "3", "winners": 89012, "prize_per_winner": "R50.00"},
                    {"match": "2+B", "winners": 78901, "prize_per_winner": "R20.00"}
                ],
                "rollover_amount": "R5,753,261.36",
                "next_jackpot": "R12,000,000.00",
                "total_sales": "R15,670,660.00",
                "confidence": 95
            }
            
            IMPORTANT: Extract ALL prize divisions visible in the screenshot. For Powerball, use PowerBall (PB) instead of bonus (B). For Daily Lotto, there are typically 4 divisions without bonus numbers. Include financial information if visible.
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
            
            logger.info(f"Extracted {data['lottery_type']} Draw {data['draw_number']} - {confidence}% confidence")
            
            # Save to database
            db_url = os.environ.get("DATABASE_URL")
            conn = psycopg2.connect(db_url)
            cur = conn.cursor()
            
            # Check if already exists
            cur.execute("""
                SELECT id FROM lottery_results 
                WHERE lottery_type = %s AND draw_number = %s
            """, (data['lottery_type'], data['draw_number']))
            
            if cur.fetchone():
                logger.info(f"Result already exists: {data['lottery_type']} Draw {data['draw_number']}")
            else:
                # Insert new record with complete data
                cur.execute("""
                    INSERT INTO lottery_results (
                        lottery_type, draw_number, draw_date, main_numbers, 
                        bonus_numbers, prize_divisions, rollover_amount, 
                        next_jackpot, total_sales, created_at
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    RETURNING id
                """, (
                    data['lottery_type'],
                    data['draw_number'], 
                    data['draw_date'],
                    json.dumps(data['main_numbers']),
                    json.dumps(data.get('bonus_numbers', [])),
                    json.dumps(data.get('prize_divisions', [])),
                    data.get('rollover_amount'),
                    data.get('next_jackpot'),
                    data.get('total_sales'),
                    datetime.now()
                ))
                
                record_id = cur.fetchone()[0]
                conn.commit()
                
                new_results.append({
                    'lottery_type': data['lottery_type'],
                    'draw_number': data['draw_number'],
                    'draw_date': data['draw_date'],
                    'confidence': confidence,
                    'record_id': record_id
                })
                logger.info(f"✅ NEW result saved: ID {record_id}")
            
            conn.close()
            processed += 1
            
        except Exception as e:
            logger.error(f"Failed to process {screenshot_path}: {e}")
    
    logger.info(f"AI processing complete: {processed} processed, {len(new_results)} new results")
    
    return {
        'success': True,
        'processed': processed,
        'new_results': len(new_results),
        'results': new_results,
        'message': f"Processed {processed} screenshots, found {len(new_results)} new lottery results"
    }

if __name__ == "__main__":
    result = process_available_screenshots()
    print(f"Result: {result}")