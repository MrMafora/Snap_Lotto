#!/usr/bin/env python3
"""
Add comprehensive LOTTO PLUS 2 data from the provided screenshot
Draw ID 2547 - 2025-06-04
"""
import os
import sys
import json
from datetime import datetime

# Add the current directory to the path so we can import from main
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def add_lotto_plus_2_comprehensive_data():
    """Add comprehensive LOTTO PLUS 2 data from the screenshot"""
    try:
        from main import app, db, LotteryResult
        
        with app.app_context():
            # Check if this entry already exists
            existing = LotteryResult.query.filter_by(
                lottery_type="LOTTO PLUS 2",
                draw_number=2547
            ).first()
            
            if existing:
                print("Updating existing LOTTO PLUS 2 Draw 2547...")
                db.session.delete(existing)
                db.session.commit()
            
            # Create comprehensive LOTTO PLUS 2 entry
            lotto_plus_2_result = LotteryResult()
            lotto_plus_2_result.lottery_type = "LOTTO PLUS 2"
            lotto_plus_2_result.draw_number = 2547
            lotto_plus_2_result.draw_date = datetime(2025, 6, 4)
            
            # Winning numbers from screenshot: 06, 28, 01, 23, 26, 22 + 31
            lotto_plus_2_result.numbers = json.dumps([6, 28, 1, 23, 26, 22])
            lotto_plus_2_result.bonus_numbers = json.dumps([31])
            
            # Complete prize divisions from screenshot
            divisions_data = [
                {
                    "division": "DIV 1",
                    "requirement": "SIX CORRECT NUMBERS",
                    "winners": 0,
                    "prize_amount": "R0.00"
                },
                {
                    "division": "DIV 2", 
                    "requirement": "FIVE CORRECT NUMBERS + BONUS BALL",
                    "winners": 27,
                    "prize_amount": "R67,603.10"
                },
                {
                    "division": "DIV 3",
                    "requirement": "FIVE CORRECT NUMBERS",
                    "winners": 58,
                    "prize_amount": "R3,338.40"
                },
                {
                    "division": "DIV 4",
                    "requirement": "FOUR CORRECT NUMBERS + BONUS BALL",
                    "winners": 1758,
                    "prize_amount": "R1,928.20"
                },
                {
                    "division": "DIV 5",
                    "requirement": "FOUR CORRECT NUMBERS",
                    "winners": 7508,
                    "prize_amount": "R127.20"
                },
                {
                    "division": "DIV 6",
                    "requirement": "THREE CORRECT NUMBERS + BONUS BALL",
                    "winners": 13610,
                    "prize_amount": "R104.10"
                },
                {
                    "division": "DIV 7",
                    "requirement": "THREE CORRECT NUMBERS",
                    "winners": 53140,
                    "prize_amount": "R25.00"
                },
                {
                    "division": "DIV 8",
                    "requirement": "TWO CORRECT NUMBERS + BONUS BALL",
                    "winners": None,  # Shown as "-" in screenshot
                    "prize_amount": "R15.00"
                }
            ]
            
            lotto_plus_2_result.divisions = json.dumps(divisions_data)
            
            # Financial information from screenshot
            lotto_plus_2_result.rollover_amount = "R8,996,961.23"
            lotto_plus_2_result.rollover_number = 8
            lotto_plus_2_result.total_pool_size = "R10,968,714.23"
            lotto_plus_2_result.total_sales = "R5,713,125.00"
            lotto_plus_2_result.next_jackpot = "R10,000,000.00"
            lotto_plus_2_result.draw_machine = "RNG 1"
            lotto_plus_2_result.next_draw_date_str = "2025-06-07"
            
            # Required database fields
            lotto_plus_2_result.source_url = "https://www.nationallottery.co.za/results/lotto-plus-2-results"
            lotto_plus_2_result.ocr_provider = "manual-comprehensive-extraction"
            lotto_plus_2_result.ocr_model = "human-verified-accurate"
            lotto_plus_2_result.ocr_timestamp = datetime.now()
            
            # Add to database
            db.session.add(lotto_plus_2_result)
            db.session.commit()
            
            print("✓ Successfully added comprehensive LOTTO PLUS 2 data!")
            print("✓ Draw 2547 - 2025-06-04")
            print("✓ Numbers: [6, 28, 1, 23, 26, 22] + Bonus [31]")
            print("✓ All 8 prize divisions with winners and amounts")
            print(f"✓ Rollover: R8,996,961.23 (Rollover #8)")
            print(f"✓ Total Pool: R10,968,714.23")
            print(f"✓ Next Jackpot: R10,000,000.00")
            print("✓ Draw Machine: RNG 1")
            print("✓ Next Draw: 2025-06-07")
            
            return True
            
    except Exception as e:
        print(f"Error adding LOTTO PLUS 2 data: {e}")
        return False

if __name__ == "__main__":
    print("Adding comprehensive LOTTO PLUS 2 data...")
    success = add_lotto_plus_2_comprehensive_data()
    if success:
        print("LOTTO PLUS 2 data addition completed successfully!")
    else:
        print("LOTTO PLUS 2 data addition failed!")