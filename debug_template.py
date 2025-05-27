#!/usr/bin/env python3
"""
Debug script to test exactly what data is being passed to the template
"""

import sys
sys.path.append('.')
from main import app, db
from models import LotteryResult
import json

def debug_template_data():
    with app.app_context():
        lottery_types = ['Lottery', 'Lottery Plus 1', 'Lottery Plus 2', 'Powerball', 'Powerball Plus', 'Daily Lottery']
        
        # Use the same mapping logic as main.py
        lottery_mapping = {
            'Lottery': ['Lottery', 'Lotto'],
            'Lottery Plus 1': ['Lottery Plus 1', 'Lotto Plus 1'], 
            'Lottery Plus 2': ['Lottery Plus 2', 'Lotto Plus 2'],
            'Powerball': ['Powerball', 'PowerBall'],
            'Powerball Plus': ['Powerball Plus'],
            'Daily Lottery': ['Daily Lottery']
        }
        
        latest_results = {}
        for display_type, db_names in lottery_mapping.items():
            for db_name in db_names:
                latest_result = LotteryResult.query.filter_by(lottery_type=db_name).order_by(LotteryResult.draw_date.desc()).first()
                if latest_result:
                    latest_results[display_type] = latest_result
                    break
        
        print("=== TEMPLATE DATA DEBUG ===")
        print(f"lottery_types = {lottery_types}")
        print(f"latest_results keys = {list(latest_results.keys())}")
        print()
        
        # Test the exact template logic for each lottery type
        for lottery_type in lottery_types:
            print(f"\n--- Testing {lottery_type} ---")
            
            # Template condition 1: latest_results and lottery_type in latest_results and latest_results[lottery_type]
            condition1 = latest_results and lottery_type in latest_results and latest_results[lottery_type]
            print(f"Condition 1 (latest_results and lottery_type in latest_results and latest_results[lottery_type]): {condition1}")
            
            if condition1:
                result = latest_results[lottery_type]
                print(f"result object: {result}")
                print(f"result.numbers: {repr(result.numbers)}")
                print(f"type(result.numbers): {type(result.numbers)}")
                print(f"bool(result.numbers): {bool(result.numbers)}")
                
                # Template condition 2: result.numbers
                condition2 = bool(result.numbers) if result.numbers is not None else False
                print(f"Condition 2 (result.numbers): {condition2}")
                
                if condition2:
                    try:
                        numbers_list = result.get_numbers_list()
                        print(f"get_numbers_list(): {numbers_list}")
                        print(f"len(numbers_list): {len(numbers_list) if numbers_list else 0}")
                        print("✓ TEMPLATE SHOULD SHOW NUMBERS")
                    except Exception as e:
                        print(f"ERROR in get_numbers_list(): {e}")
                        print("✗ TEMPLATE WILL SHOW 'No winning numbers available'")
                else:
                    print("✗ TEMPLATE WILL SHOW 'No winning numbers available'")
            else:
                print("✗ TEMPLATE WILL SHOW 'No results available'")

if __name__ == "__main__":
    debug_template_data()