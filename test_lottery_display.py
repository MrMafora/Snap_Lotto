#!/usr/bin/env python3
"""
Test script to display lottery results in the exact format requested
"""
import json
from main import app, db
from models import LotteryResult

def display_lottery_result(lottery_type, draw_number):
    """Display lottery result in the exact format requested"""
    with app.app_context():
        result = LotteryResult.query.filter_by(
            lottery_type=lottery_type, 
            draw_number=draw_number
        ).first()
        
        if not result:
            print(f"No result found for {lottery_type} Draw {draw_number}")
            return
        
        # Parse numbers
        numbers = result.get_numbers_list()
        bonus_numbers = result.get_bonus_numbers_list()
        bonus_number = bonus_numbers[0] if bonus_numbers else None
        
        # Parse divisions - debug the exact content
        divisions = {}
        print(f"DEBUG: divisions field type: {type(result.divisions)}")
        print(f"DEBUG: divisions field content: {repr(result.divisions)}")
        
        if result.divisions:
            try:
                if isinstance(result.divisions, str):
                    divisions = json.loads(result.divisions)
                else:
                    divisions = result.divisions
                print(f"DEBUG: parsed divisions: {divisions}")
            except Exception as e:
                print(f"Error parsing divisions: {e}")
                divisions = {}
        
        # Display header
        print(f"{lottery_type} Results")
        print(f"Draw ID: {result.draw_number}")
        print(f"Draw Date: {result.draw_date.strftime('%Y-%m-%d')}")
        
        # Display numbers in numerical order
        sorted_numbers = sorted(numbers)
        formatted_numbers = [f"{num:02d}" for num in sorted_numbers]
        print(f"Winning Numbers (Numerical Order): {', '.join(formatted_numbers)}")
        
        # Display bonus/powerball
        if bonus_number:
            if 'POWERBALL' in lottery_type.upper():
                print(f"PowerBall: {int(bonus_number):02d}")
            else:
                print(f"Bonus Ball: {int(bonus_number):02d}")
        
        # Display prize divisions
        print("Prize Divisions:")
        if divisions:
            for div_key in sorted(divisions.keys()):
                div = divisions[div_key]
                div_num = div_key[3:]  # Extract number from 'div1', 'div2', etc.
                winners = div.get('winners', '0')
                prize = div.get('prize', 'R0.00')
                description = div.get('description', '')
                
                winner_text = f"{winners} winner{'s' if int(winners) != 1 else ''}" if winners != '0' else '0 winners'
                print(f"Div {div_num} ({description}): {winner_text}, {prize}")
        else:
            print("No prize division data available")
        
        # Display more info
        print("More Info:")
        if result.rollover_amount:
            print(f"Rollover Amount: {result.rollover_amount}")
        if result.rollover_number:
            print(f"Rollover No: {result.rollover_number}")
        if result.total_pool_size:
            print(f"Total Pool Size: {result.total_pool_size}")
        if result.total_sales:
            print(f"Total Sales: {result.total_sales}")
        if result.next_jackpot:
            print(f"Next Jackpot: {result.next_jackpot}")
        if result.draw_machine:
            print(f"Draw Machine: {result.draw_machine}")
        if result.next_draw_date:
            if hasattr(result.next_draw_date, 'strftime'):
                print(f"Next Draw Date: {result.next_draw_date.strftime('%Y-%m-%d')}")
            else:
                print(f"Next Draw Date: {result.next_draw_date}")

if __name__ == "__main__":
    # Test LOTTO PLUS 1 format
    print("=== Testing LOTTO PLUS 1 Format ===")
    display_lottery_result('LOTTO PLUS 1', 2551)
    
    print("\n=== Testing LOTTO Format ===")
    display_lottery_result('LOTTO', 2551)
    
    print("\n=== Testing PowerBall Format ===")
    display_lottery_result('PowerBall', 1625)