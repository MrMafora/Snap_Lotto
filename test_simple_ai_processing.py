#!/usr/bin/env python3
"""
Simple AI processing test for lottery screenshots
Tests Google Gemini 2.5 Pro extraction and database insertion
"""

import os
import json
import logging
import psycopg2
from datetime import datetime
import google.generativeai as genai

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_ai_processing():
    """Test AI processing on one screenshot"""
    
    # Check API key
    api_key = os.environ.get("GOOGLE_API_KEY_SNAP_LOTTERY")
    if not api_key:
        logger.error("Missing GOOGLE_API_KEY_SNAP_LOTTERY")
        return False
    
    # Initialize Gemini
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel('gemini-2.0-flash-exp')
    
    # Find a screenshot
    import glob
    screenshots = glob.glob('screenshots/*.png')
    if not screenshots:
        # Also check uploads directory
        screenshots = glob.glob('uploads/*.png')
        if not screenshots:
            logger.error("No screenshots found in screenshots/ or uploads/")
            return False
    
    test_file = screenshots[0]
    logger.info(f"Testing with: {test_file}")
    
    try:
        # Read image
        with open(test_file, "rb") as f:
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
        
        logger.info(f"Gemini response: {response.text}")
        
        # Try to parse JSON (strip markdown code blocks)
        try:
            response_text = response.text.strip()
            if response_text.startswith('```json'):
                response_text = response_text[7:-3].strip()
            elif response_text.startswith('```'):
                response_text = response_text[3:-3].strip()
            
            data = json.loads(response_text)
            logger.info(f"Parsed data: {data}")
            
            # Test database connection
            db_url = os.environ.get("DATABASE_URL")
            conn = psycopg2.connect(db_url)
            cur = conn.cursor()
            
            # Insert test
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
            conn.close()
            
            logger.info(f"✅ SUCCESS: Inserted record ID {record_id}")
            return True
            
        except json.JSONDecodeError as e:
            logger.error(f"JSON parse error: {e}")
            return False
            
    except Exception as e:
        logger.error(f"Processing failed: {e}")
        return False

if __name__ == "__main__":
    success = test_ai_processing()
    print(f"Test result: {'SUCCESS' if success else 'FAILED'}")