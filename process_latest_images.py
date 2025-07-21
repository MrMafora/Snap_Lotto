#!/usr/bin/env python3
"""
Process latest lottery images with Google Gemini 2.5 Pro to get current results
"""

import os
import sys
import json
import logging
from datetime import datetime
import psycopg2
from google import genai

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Initialize Gemini client
client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))

def process_lottery_image(image_path, lottery_type):
    """Process a single lottery image with Gemini 2.5 Pro"""
    try:
        logger.info(f"Processing {image_path} for {lottery_type}")
        
        with open(image_path, "rb") as f:
            image_bytes = f.read()
            
        prompt = """Extract ALL lottery information from this South African National Lottery image with 99% confidence. Return JSON format:

{
  "lottery_type": "EXACT type (LOTTO, LOTTO PLUS 1, LOTTO PLUS 2, POWERBALL, POWERBALL PLUS, DAILY LOTTO)",
  "draw_number": "exact draw number",
  "draw_date": "YYYY-MM-DD format", 
  "main_numbers": [array of main numbers],
  "bonus_numbers": [array of bonus numbers],
  "confidence": 99,
  "divisions": [
    {
      "match": "exact match type (e.g., '6', '5+B', '5+PB')",
      "winners": "number of winners",
      "prize_per_winner": "prize amount"
    }
  ],
  "rollover_amount": "rollover amount if any",
  "next_jackpot": "next jackpot amount", 
  "total_sales": "total sales amount",
  "draw_machine": "draw machine info",
  "next_draw_date": "YYYY-MM-DD format"
}

CRITICAL: Extract ALL numbers exactly as shown. Verify twice before responding."""

        response = client.models.generate_content(
            model="gemini-2.5-pro",
            contents=[
                genai.types.Part.from_bytes(data=image_bytes, mime_type="image/png"),
                prompt
            ],
            config=genai.types.GenerateContentConfig(
                response_mime_type="application/json"
            ),
        )
        
        if response.text:
            data = json.loads(response.text)
            logger.info(f"Successfully extracted: {lottery_type} Draw {data.get('draw_number')} - {data.get('main_numbers')}")
            return data
        else:
            logger.error(f"No response from Gemini for {image_path}")
            return None
            
    except Exception as e:
        logger.error(f"Error processing {image_path}: {e}")
        return None

def save_to_database(data):
    """Save extracted data to PostgreSQL database"""
    try:
        connection_string = os.environ.get('DATABASE_URL')
        with psycopg2.connect(connection_string) as conn:
            with conn.cursor() as cur:
                # Insert into lottery_results table
                insert_query = """
                INSERT INTO lottery_results (
                    lottery_type, draw_number, draw_date, main_numbers, bonus_numbers,
                    divisions, rollover_amount, next_jackpot, total_pool_size, total_sales,
                    draw_machine, next_draw_date, created_at
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                RETURNING id
                """
                
                values = (
                    data['lottery_type'],
                    data.get('draw_number'),
                    data.get('draw_date'),
                    json.dumps(data.get('main_numbers', [])),
                    data.get('bonus_numbers', []),
                    json.dumps(data.get('divisions', [])),
                    data.get('rollover_amount'),
                    data.get('next_jackpot'),
                    None,  # total_pool_size
                    data.get('total_sales'),
                    data.get('draw_machine'),
                    data.get('next_draw_date'),
                    datetime.now()
                )
                
                cur.execute(insert_query, values)
                record_id = cur.fetchone()[0]
                conn.commit()
                
                logger.info(f"Saved {data['lottery_type']} to database with ID {record_id}")
                return record_id
                
    except Exception as e:
        logger.error(f"Database error: {e}")
        return None

def main():
    """Process the latest lottery images"""
    
    # Latest images from July 20-21, 2025
    latest_images = [
        ("attached_assets/20250721_164508_lotto_1753117038994.png", "LOTTO"),
        ("attached_assets/20250720_205523_lotto_1753045245755.png", "LOTTO"),
        ("attached_assets/20250720_205617_lotto_plus_1_1753045245755.png", "LOTTO PLUS 1"),
        ("attached_assets/20250720_205913_lotto_plus_2_1753045245756.png", "LOTTO PLUS 2"),
        ("attached_assets/20250720_205657_powerball_1753045245755.png", "POWERBALL"),
        ("attached_assets/20250720_205749_powerball_plus_1753045245756.png", "POWERBALL PLUS"),
        ("attached_assets/20250720_205826_daily_lotto_1753045245756.png", "DAILY LOTTO"),
    ]
    
    logger.info("=== PROCESSING LATEST LOTTERY IMAGES ===")
    
    processed_count = 0
    for image_path, lottery_type in latest_images:
        if os.path.exists(image_path):
            logger.info(f"\n--- Processing {lottery_type} ---")
            
            # Extract data with Gemini 2.5 Pro
            data = process_lottery_image(image_path, lottery_type)
            
            if data and data.get('confidence', 0) >= 95:
                # Save to database
                record_id = save_to_database(data)
                if record_id:
                    processed_count += 1
                    logger.info(f"✅ Successfully processed {lottery_type}: Draw {data.get('draw_number')} on {data.get('draw_date')}")
                else:
                    logger.error(f"❌ Failed to save {lottery_type} to database")
            else:
                logger.error(f"❌ Low confidence or failed extraction for {lottery_type}")
        else:
            logger.warning(f"⚠️ Image not found: {image_path}")
    
    logger.info(f"\n=== PROCESSING COMPLETE ===")
    logger.info(f"Successfully processed {processed_count} lottery images")
    
    return processed_count

if __name__ == "__main__":
    main()