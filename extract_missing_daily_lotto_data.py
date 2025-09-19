#!/usr/bin/env python3
"""
Extract missing Daily Lotto data from user-provided images
"""
import os
import sys
import json
import logging
from datetime import datetime

# Add current directory to path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from main import app
from models import LotteryResult, db
import google.generativeai as genai

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def extract_and_save_lottery_data():
    """Extract lottery data from user-provided images and save to database"""
    
    # Initialize Gemini directly
    genai.configure(api_key=os.environ.get('GEMINI_API_KEY'))
    model = genai.GenerativeModel('gemini-2.0-flash-exp')
    
    # Image files to process
    image_files = [
        'attached_assets/image_1755620551715.png',  # Draw 2346 - 2025-08-16
        'attached_assets/image_1755620573904.png'   # Draw 2347 - 2025-08-17
    ]
    
    results_to_add = []
    
    with app.app_context():
        for image_path in image_files:
            if not os.path.exists(image_path):
                logging.error(f"Image not found: {image_path}")
                continue
                
            logging.info(f"Processing image: {image_path}")
            
            try:
                # Read and process image
                import PIL.Image
                img = PIL.Image.open(image_path)
                
                prompt = """
                Extract the Daily Lotto results from this image. Return only a JSON object with this exact structure:
                {
                    "daily_lotto": {
                        "draw_number": <number>,
                        "draw_date": "YYYY-MM-DD",
                        "numbers": [<sorted list of 5 numbers>]
                    }
                }
                
                Look for:
                - Draw ID/number (like "2346" or "2347")
                - Draw date in format YYYY-MM-DD
                - The 5 winning numbers (extract from the yellow circles)
                
                Return ONLY the JSON, no other text.
                """
                
                response = model.generate_content([prompt, img])
                extracted_text = response.text.strip()
                
                # Clean and parse JSON
                if extracted_text.startswith('```json'):
                    extracted_text = extracted_text.replace('```json', '').replace('```', '').strip()
                elif extracted_text.startswith('```'):
                    extracted_text = extracted_text.replace('```', '').strip()
                
                extracted_data = json.loads(extracted_text)
                
                if extracted_data and 'daily_lotto' in extracted_data:
                    daily_data = extracted_data['daily_lotto']
                    
                    # Parse the extracted data
                    draw_number = daily_data.get('draw_number')
                    draw_date_str = daily_data.get('draw_date')
                    numbers = daily_data.get('numbers', [])
                    
                    if not all([draw_number, draw_date_str, numbers]):
                        logging.error(f"Incomplete data extracted from {image_path}")
                        continue
                    
                    # Parse date
                    try:
                        draw_date = datetime.strptime(draw_date_str, '%Y-%m-%d').date()
                    except ValueError:
                        logging.error(f"Invalid date format: {draw_date_str}")
                        continue
                    
                    # Check if this draw already exists
                    existing = db.session.query(LotteryResult).filter_by(
                        game_type='DAILY LOTTO',
                        draw_number=draw_number
                    ).first()
                    
                    if existing:
                        logging.info(f"Draw {draw_number} already exists, skipping")
                        continue
                    
                    # Create new lottery result
                    new_result = LotteryResult(
                        game_type='DAILY LOTTO',
                        draw_number=draw_number,
                        draw_date=draw_date,
                        numbers=json.dumps(sorted(numbers)),
                        bonus_numbers=json.dumps([]),  # Daily Lotto has no bonus numbers
                        created_at=datetime.utcnow()
                    )
                    
                    results_to_add.append({
                        'result': new_result,
                        'image': image_path,
                        'numbers': numbers
                    })
                    
                    logging.info(f"Prepared Daily Lotto draw {draw_number} for {draw_date}: {numbers}")
                
            except Exception as e:
                logging.error(f"Error processing {image_path}: {str(e)}")
                continue
        
        # Save all results to database
        if results_to_add:
            try:
                for item in results_to_add:
                    db.session.add(item['result'])
                
                db.session.commit()
                
                logging.info(f"Successfully added {len(results_to_add)} Daily Lotto draws to database")
                
                # Print summary
                print("\n=== EXTRACTION SUMMARY ===")
                for item in results_to_add:
                    result = item['result']
                    print(f"Draw {result.draw_number} ({result.draw_date}): {json.loads(result.numbers)}")
                
            except Exception as e:
                db.session.rollback()
                logging.error(f"Error saving to database: {str(e)}")
                return False
        else:
            logging.info("No new data to add to database")
            return False
    
    return len(results_to_add) > 0

if __name__ == '__main__':
    success = extract_and_save_lottery_data()
    if success:
        print("✓ Data extraction and database update completed successfully")
    else:
        print("✗ No new data was extracted or saved")