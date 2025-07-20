#!/usr/bin/env python3
"""
Complete AI workflow test: Extract from screenshot → Preview → Save to database
"""

import os
import json
import logging
from pathlib import Path
from google import genai
from google.genai import types
from datetime import datetime
import psycopg2
from urllib.parse import urlparse

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def connect_database():
    """Connect to PostgreSQL database"""
    try:
        database_url = os.environ.get('DATABASE_URL')
        if not database_url:
            logger.error("❌ DATABASE_URL not found")
            return None
        
        conn = psycopg2.connect(database_url)
        return conn
    except Exception as e:
        logger.error(f"❌ Database connection failed: {e}")
        return None

def extract_with_gemini(screenshot_path):
    """Extract lottery data using Gemini 2.5 Pro"""
    
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        logger.error("❌ GEMINI_API_KEY not found")
        return None
    
    client = genai.Client(api_key=api_key)
    
    prompt = """
    You are analyzing a South African National Lottery website screenshot.
    Extract lottery information and return in this EXACT JSON format:

    {
        "lottery_type": "POWERBALL",
        "draw_number": 1630,
        "draw_date": "2025-07-19",
        "main_numbers": [3, 5, 23, 35, 43],
        "bonus_numbers": [7],
        "jackpot_amount": 84000000,
        "next_jackpot": 90000000,
        "prize_divisions": [
            {
                "division": "Division 1 (5+PB)",
                "winners": 0,
                "prize_amount": "84000000"
            },
            {
                "division": "Division 2 (5)",  
                "winners": 2,
                "prize_amount": "15000"
            }
        ],
        "confidence": 95
    }

    Important rules:
    - lottery_type must be one of: LOTTO, LOTTO PLUS 1, LOTTO PLUS 2, POWERBALL, POWERBALL PLUS, DAILY LOTTO
    - main_numbers: array of integers (lottery numbers)
    - bonus_numbers: array of integers (powerball/bonus numbers)
    - jackpot_amount: integer (current jackpot in Rands)
    - next_jackpot: integer (next draw jackpot in Rands)
    - draw_number: integer
    - draw_date: string in YYYY-MM-DD format
    - Only return valid JSON, no extra text
    """
    
    try:
        with open(screenshot_path, "rb") as f:
            image_bytes = f.read()
        
        response = client.models.generate_content(
            model="gemini-2.5-pro",
            contents=[
                types.Part.from_bytes(data=image_bytes, mime_type="image/png"),
                prompt
            ],
        )
        
        if response.text:
            # Clean response text to get only JSON
            response_text = response.text.strip()
            if response_text.startswith('```json'):
                response_text = response_text[7:]
            if response_text.endswith('```'):
                response_text = response_text[:-3]
            response_text = response_text.strip()
            
            extracted_data = json.loads(response_text)
            logger.info(f"✅ Gemini extraction successful: {extracted_data['lottery_type']}")
            logger.info(f"Full response: {json.dumps(extracted_data, indent=2)}")
            return extracted_data
        else:
            logger.error("❌ Empty response from Gemini")
            return None
            
    except Exception as e:
        logger.error(f"❌ Gemini extraction failed: {e}")
        return None

def save_to_database(extracted_data):
    """Save extracted lottery data to main database"""
    
    conn = connect_database()
    if not conn:
        return False
    
    try:
        cursor = conn.cursor()
        
        # Insert into lottery_results table (using correct column names)
        insert_query = """
        INSERT INTO lottery_results (
            lottery_type, draw_number, draw_date, main_numbers, bonus_numbers,
            next_jackpot, prize_divisions, created_at
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        RETURNING id
        """
        
        now = datetime.now()
        
        values = (
            extracted_data['lottery_type'],
            extracted_data.get('draw_number'),
            extracted_data['draw_date'],
            json.dumps(extracted_data.get('main_numbers', [])),
            json.dumps(extracted_data.get('bonus_numbers', [])),
            str(extracted_data.get('next_jackpot', '')),
            json.dumps(extracted_data.get('prize_divisions', [])),
            now
        )
        
        cursor.execute(insert_query, values)
        new_id = cursor.fetchone()[0]
        
        conn.commit()
        logger.info(f"✅ Saved to database with ID: {new_id}")
        return True
        
    except Exception as e:
        logger.error(f"❌ Database save failed: {e}")
        conn.rollback()
        return False
    finally:
        conn.close()

def run_complete_workflow():
    """Run the complete AI workflow test"""
    
    print("🚀 Complete AI Workflow Test")
    print("=" * 50)
    
    # 1. Extract from screenshot
    screenshot_path = "screenshots/test_capture.png"
    
    if not os.path.exists(screenshot_path):
        print("❌ Test screenshot not found")
        return False
    
    print("🧠 Step 1: Extracting with Gemini AI...")
    extracted_data = extract_with_gemini(screenshot_path)
    
    if not extracted_data:
        print("❌ AI extraction failed")
        return False
    
    # 2. Display preview
    print("\n📋 Step 2: Data Preview")
    print("-" * 30)
    print(f"Lottery Type: {extracted_data.get('lottery_type')}")
    print(f"Draw Number: {extracted_data.get('draw_number')}")  
    print(f"Draw Date: {extracted_data.get('draw_date')}")
    print(f"Main Numbers: {extracted_data.get('main_numbers')}")
    print(f"Bonus Numbers: {extracted_data.get('bonus_numbers')}")
    jackpot = extracted_data.get('jackpot_amount')
    print(f"Jackpot: R{jackpot:,}" if jackpot else "Jackpot: N/A")
    confidence = extracted_data.get('confidence')
    print(f"Confidence: {confidence}%" if confidence else "Confidence: N/A")
    print(f"Prize Divisions: {len(extracted_data.get('prize_divisions', []))}")
    
    # 3. Save to database
    print("\n💾 Step 3: Saving to database...")
    success = save_to_database(extracted_data)
    
    if success:
        print("✅ Complete workflow successful!")
        print(f"🎯 Lottery data extracted and saved: {extracted_data['lottery_type']}")
        return True
    else:
        print("❌ Database save failed")
        return False

if __name__ == "__main__":
    success = run_complete_workflow()
    if success:
        print("\n🎉 AI-powered lottery scanner working perfectly!")
    else:
        print("\n⚠️ Workflow needs attention")