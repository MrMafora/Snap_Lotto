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
            
            # Simple extraction prompt
            prompt = """
            Extract lottery information from this South African lottery screenshot. 
            Return JSON with this format:
            {
                "lottery_type": "LOTTO",
                "draw_number": 2560,
                "draw_date": "2025-07-22",
                "main_numbers": [1,2,3,4,5,6],
                "bonus_numbers": [7],
                "confidence": 95
            }
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
                # Insert new record
                cur.execute("""
                    INSERT INTO lottery_results (
                        lottery_type, draw_number, draw_date, main_numbers, 
                        bonus_numbers, created_at
                    ) VALUES (%s, %s, %s, %s, %s, %s)
                    RETURNING id
                """, (
                    data['lottery_type'],
                    data['draw_number'], 
                    data['draw_date'],
                    json.dumps(data['main_numbers']),
                    json.dumps(data.get('bonus_numbers', [])),
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