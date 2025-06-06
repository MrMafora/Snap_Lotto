#!/usr/bin/env python3
import os
import sys
import json
from datetime import datetime

# Import from main.py which has the complete app setup
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from main import app, db, LotteryResult

def add_lotto_plus_1_comprehensive_data():
    """Add comprehensive LOTTO PLUS 1 data from the screenshot"""
    
    with app.app_context():
        print("Adding comprehensive June 4, 2025 LOTTO PLUS 1 data...")
        
        # Check if this draw already exists
        existing = LotteryResult.query.filter_by(
            lottery_type='LOTTO PLUS 1',
            draw_number=2547
        ).first()
        
        if existing:
            print(f"LOTTO PLUS 1 draw 2547 already exists, updating with comprehensive data...")
            db.session.delete(existing)
            db.session.commit()
        
        # Prize divisions data from the screenshot
        divisions_data = [
            {
                "division": "DIV 1",
                "requirement": "SIX CORRECT NUMBERS",
                "winners": 1,
                "prize_amount": "R0.00"
            },
            {
                "division": "DIV 2", 
                "requirement": "FIVE CORRECT NUMBERS + BONUS BALL",
                "winners": 30,
                "prize_amount": "R0.00"
            },
            {
                "division": "DIV 3",
                "requirement": "FIVE CORRECT NUMBERS", 
                "winners": 75,
                "prize_amount": "R8,377.20"
            },
            {
                "division": "DIV 4",
                "requirement": "FOUR CORRECT NUMBERS + BONUS BALL",
                "winners": 1657,
                "prize_amount": "R1,663.00"
            },
            {
                "division": "DIV 5",
                "requirement": "FOUR CORRECT NUMBERS",
                "winners": 7460,
                "prize_amount": "R150.60"
            },
            {
                "division": "DIV 6",
                "requirement": "THREE CORRECT NUMBERS + BONUS BALL",
                "winners": 13286,
                "prize_amount": "R102.20"
            },
            {
                "division": "DIV 7",
                "requirement": "THREE CORRECT NUMBERS",
                "winners": 56976,
                "prize_amount": "R25.00"
            },
            {
                "division": "DIV 8",
                "requirement": "TWO CORRECT NUMBERS + BONUS BALL",
                "winners": None,
                "prize_amount": "R15.00"
            }
        ]
        
        # Create new comprehensive lottery result
        new_result = LotteryResult()
        new_result.lottery_type = 'LOTTO PLUS 1'
        new_result.draw_number = 2547
        new_result.draw_date = datetime(2025, 6, 4)
        new_result.numbers = json.dumps([17, 40, 39, 31, 7, 43])  # Main numbers from screenshot
        new_result.bonus_numbers = json.dumps([13])  # Bonus number
        new_result.divisions = json.dumps(divisions_data)
        new_result.rollover_amount = "R13,788,244.88"
        new_result.rollover_number = 12
        new_result.total_pool_size = "R15,874,988.08"
        new_result.total_sales = "R6,146,795.00"
        new_result.next_jackpot = "R15,000,000.00"
        new_result.draw_machine = "RNG 1"
        new_result.next_draw_date_str = "2025-06-07"
        new_result.source_url = "https://www.nationallottery.co.za/lotto-plus-1"  # Add required source URL
        
        db.session.add(new_result)
        db.session.commit()
        
        print(f"Successfully saved LOTTO PLUS 1 draw 2547 with {len(divisions_data)} divisions")
        print(f"Main numbers: {[17, 40, 39, 31, 7, 43]}")
        print(f"Bonus number: 13")
        print(f"Rollover amount: R13,788,244.88")
        print("Successfully added comprehensive LOTTO PLUS 1 data with all prize divisions")

if __name__ == "__main__":
    add_lotto_plus_1_comprehensive_data()