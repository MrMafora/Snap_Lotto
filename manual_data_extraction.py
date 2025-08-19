#!/usr/bin/env python3
"""
Manually extract Daily Lotto data from images and add to database
"""
import os
import json
import logging
from datetime import datetime
from google import genai
from google.genai import types

# Setup logging
logging.basicConfig(level=logging.INFO)

def extract_daily_lotto_from_images():
    """Extract lottery data from images using Gemini"""
    
    # Initialize Gemini client
    client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))
    
    image_files = [
        'attached_assets/image_1755620551715.png',  # Should be draw 2346
        'attached_assets/image_1755620573904.png'   # Should be draw 2347
    ]
    
    extracted_results = []
    
    for image_path in image_files:
        if not os.path.exists(image_path):
            logging.error(f"Image not found: {image_path}")
            continue
        
        logging.info(f"Processing {image_path}")
        
        try:
            # Read image
            with open(image_path, "rb") as f:
                image_bytes = f.read()
            
            # Create extraction prompt
            prompt = """
            Extract the Daily Lotto results from this lottery results image. 
            
            Look for:
            1. Draw ID/number (usually after "DRAW ID" like "2346" or "2347")
            2. Draw date (in format YYYY-MM-DD, like "2025-08-16")
            3. The 5 winning numbers in the yellow circles
            
            Return ONLY a JSON object in this exact format:
            {
                "draw_number": 2346,
                "draw_date": "2025-08-16", 
                "numbers": [5, 9, 18, 23, 26]
            }
            
            Make sure the numbers are sorted from lowest to highest.
            Return ONLY the JSON, no other text or explanation.
            """
            
            response = client.models.generate_content(
                model="gemini-2.5-pro",
                contents=[
                    types.Part.from_bytes(
                        data=image_bytes,
                        mime_type="image/png",
                    ),
                    prompt
                ],
            )
            
            if response.text:
                # Clean the response
                result_text = response.text.strip()
                if result_text.startswith('```json'):
                    result_text = result_text.replace('```json', '').replace('```', '').strip()
                elif result_text.startswith('```'):
                    result_text = result_text.replace('```', '').strip()
                
                # Parse JSON
                result_data = json.loads(result_text)
                extracted_results.append({
                    'image': image_path,
                    'data': result_data
                })
                
                logging.info(f"Extracted: Draw {result_data['draw_number']} on {result_data['draw_date']} - Numbers: {result_data['numbers']}")
            
        except Exception as e:
            logging.error(f"Error processing {image_path}: {str(e)}")
            continue
    
    return extracted_results

def add_to_database(results):
    """Add extracted results to database"""
    
    # Import here to avoid loading issues
    import sys
    sys.path.append(os.path.dirname(os.path.abspath(__file__)))
    
    # Import Flask app and models
    from main import app
    from models import LotteryResult, db
    
    added_count = 0
    
    with app.app_context():
        for result in results:
            data = result['data']
            
            # Check if draw already exists
            existing = db.session.query(LotteryResult).filter_by(
                game_type='DAILY LOTTO',
                draw_number=data['draw_number']
            ).first()
            
            if existing:
                logging.info(f"Draw {data['draw_number']} already exists, skipping")
                continue
            
            # Parse date
            draw_date = datetime.strptime(data['draw_date'], '%Y-%m-%d').date()
            
            # Create new result
            new_result = LotteryResult(
                game_type='DAILY LOTTO',
                draw_number=data['draw_number'],
                draw_date=draw_date,
                numbers=json.dumps(sorted(data['numbers'])),
                bonus_numbers=json.dumps([]),  # Daily Lotto has no bonus
                created_at=datetime.utcnow()
            )
            
            db.session.add(new_result)
            added_count += 1
            logging.info(f"Added Daily Lotto draw {data['draw_number']} to database")
        
        if added_count > 0:
            db.session.commit()
            logging.info(f"Successfully committed {added_count} new draws to database")
        else:
            logging.info("No new draws to add")
    
    return added_count

if __name__ == '__main__':
    print("🎯 Extracting Daily Lotto data from images...")
    
    # Extract data from images
    results = extract_daily_lotto_from_images()
    
    if results:
        print(f"✓ Extracted {len(results)} results from images")
        
        # Add to database
        added = add_to_database(results)
        print(f"✓ Added {added} new draws to database")
        
        # Print summary
        print("\n=== EXTRACTION SUMMARY ===")
        for result in results:
            data = result['data']
            print(f"Draw {data['draw_number']} ({data['draw_date']}): {data['numbers']}")
    else:
        print("✗ No data could be extracted from images")