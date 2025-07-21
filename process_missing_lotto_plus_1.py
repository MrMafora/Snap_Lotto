#!/usr/bin/env python3
"""
Process missing LOTTO PLUS 1 latest result
"""

import os
import json
import logging
from datetime import datetime
import psycopg2
from google import genai

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))

# Try the most recent LOTTO PLUS 1 images
lotto_plus_1_images = [
    "attached_assets/20250720_202706_lotto_plus_1_1753043679967.png",
    "attached_assets/image_1753119107694.png",  # Recent image that might contain LOTTO PLUS 1
]

for image_path in lotto_plus_1_images:
    if os.path.exists(image_path):
        logger.info(f"Processing {image_path} for LOTTO PLUS 1")
        
        try:
            with open(image_path, "rb") as f:
                image_bytes = f.read()
                
            prompt = """Extract LOTTO PLUS 1 lottery information from this image. Return JSON:

{
  "lottery_type": "LOTTO PLUS 1",
  "draw_number": "exact draw number", 
  "draw_date": "YYYY-MM-DD format",
  "main_numbers": [array of 6 main numbers],
  "bonus_numbers": [bonus number],
  "confidence": 99
}

Focus only on LOTTO PLUS 1 results if multiple types are shown."""

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
                if data.get('draw_number') and data.get('main_numbers') and len(data.get('main_numbers', [])) == 6:
                    logger.info(f"Found LOTTO PLUS 1 Draw {data.get('draw_number')}: {data.get('main_numbers')}")
                    
                    # Save to database
                    connection_string = os.environ.get('DATABASE_URL')
                    with psycopg2.connect(connection_string) as conn:
                        with conn.cursor() as cur:
                            insert_query = """
                            INSERT INTO lottery_results (
                                lottery_type, draw_number, draw_date, main_numbers, bonus_numbers, created_at
                            ) VALUES (%s, %s, %s, %s, %s, %s)
                            RETURNING id
                            """
                            
                            values = (
                                'LOTTO PLUS 1',
                                data.get('draw_number'),
                                data.get('draw_date'),
                                json.dumps(data.get('main_numbers', [])),
                                data.get('bonus_numbers', []),
                                datetime.now()
                            )
                            
                            cur.execute(insert_query, values)
                            record_id = cur.fetchone()[0]
                            conn.commit()
                            
                            logger.info(f"✅ Saved LOTTO PLUS 1 Draw {data.get('draw_number')} to database with ID {record_id}")
                            break
                else:
                    logger.info(f"No valid LOTTO PLUS 1 data found in {image_path}")
            
        except Exception as e:
            logger.error(f"Error processing {image_path}: {e}")
    else:
        logger.warning(f"Image not found: {image_path}")

logger.info("LOTTO PLUS 1 processing complete")