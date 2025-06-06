#!/usr/bin/env python3
"""
Save all extracted Google Gemini results to database
"""

import json
from datetime import datetime
from models import LotteryResult, db
from main import app

def save_all_extracted_data():
    """Save all Google Gemini extracted lottery results to database"""
    
    # Complete extraction results from all 6 lottery screenshots
    lottery_results = [
        {
            "lottery_type": "LOTTO",
            "draw_number": "2547",
            "draw_date": "2025-06-04",
            "main_numbers": [32, 34, 8, 52, 36, 24],
            "bonus_numbers": [26]
        },
        {
            "lottery_type": "LOTTO PLUS 1",
            "draw_number": "2547", 
            "draw_date": "2025-06-04",
            "main_numbers": [17, 40, 39, 31, 7, 43],
            "bonus_numbers": [13]
        },
        {
            "lottery_type": "LOTTO PLUS 2",
            "draw_number": "2547",
            "draw_date": "2025-06-04",
            "main_numbers": [6, 28, 1, 23, 26, 22],
            "bonus_numbers": [31]
        },
        {
            "lottery_type": "PowerBall",
            "draw_number": "1622",
            "draw_date": "2025-06-03",
            "main_numbers": [50, 5, 47, 40, 26],
            "bonus_numbers": [14]
        },
        {
            "lottery_type": "PowerBall Plus",
            "draw_number": "1622",
            "draw_date": "2025-06-03", 
            "main_numbers": [16, 39, 37, 38, 30],
            "bonus_numbers": [4]
        },
        {
            "lottery_type": "Daily Lotto",
            "draw_number": "2274",
            "draw_date": "2025-06-05",
            "main_numbers": [7, 27, 35, 22, 15],
            "bonus_numbers": []
        }
    ]
    
    with app.app_context():
        saved_count = 0
        
        for result_data in lottery_results:
            try:
                # Convert date string to datetime object
                draw_date = datetime.strptime(result_data['draw_date'], '%Y-%m-%d').date()
                
                # Create new lottery result
                new_result = LotteryResult(
                    lottery_type=result_data['lottery_type'],
                    draw_number=result_data['draw_number'],
                    draw_date=draw_date,
                    numbers=json.dumps(result_data['main_numbers']),
                    bonus_numbers=json.dumps(result_data['bonus_numbers']),
                    source_url='https://www.nationallottery.co.za/results',
                    ocr_provider='gemini-2.5-pro',
                    created_at=datetime.now(),
                    updated_at=datetime.now()
                )
                
                db.session.add(new_result)
                db.session.commit()
                
                print(f"✓ Saved {result_data['lottery_type']} Draw {result_data['draw_number']}")
                saved_count += 1
                
            except Exception as e:
                print(f"✗ Error saving {result_data['lottery_type']}: {str(e)}")
                db.session.rollback()
        
        print(f"\nGoogle Gemini extraction complete: {saved_count}/{len(lottery_results)} results saved to database")
        
        # Display final summary
        print("\n=== FINAL LOTTERY EXTRACTION RESULTS ===")
        for result in lottery_results:
            print(f"{result['lottery_type']} Draw {result['draw_number']}: {result['main_numbers']} + {result['bonus_numbers']}")

if __name__ == "__main__":
    save_all_extracted_data()