#!/usr/bin/env python3
"""
Script to create a test data file with realistic lottery data.
"""
import pandas as pd
import os
from datetime import datetime, timedelta
import random

def create_test_data_file(output_path):
    """Create a test data Excel file with realistic lottery data"""
    # Define lottery types
    lottery_types = [
        'Lottery', 'Lottery Plus 1', 'Lottery Plus 2', 
        'Powerball', 'Powerball Plus', 'Daily Lottery'
    ]
    
    # Create a writer to save the DataFrame
    writer = pd.ExcelWriter(output_path, engine='openpyxl')
    
    # Start date (recent)
    base_date = datetime.now() - timedelta(days=60)
    
    # For each lottery type
    for lottery_type in lottery_types:
        # Create sample data rows
        rows = []
        draw_number_base = random.randint(1000, 2000)
        
        # Create 5 draws per lottery type (one per week, except Daily Lottery is daily)
        for i in range(5):
            # Calculate draw date
            if lottery_type == 'Daily Lottery':
                draw_date = base_date + timedelta(days=i)
            else:
                draw_date = base_date + timedelta(days=i*7)
            
            # Generate winning numbers
            if lottery_type in ['Lottery', 'Lottery Plus 1', 'Lottery Plus 2']:
                winning_numbers = ", ".join([str(random.randint(1, 52)) for _ in range(6)])
                bonus_ball = random.randint(1, 52)
            elif lottery_type in ['Powerball', 'Powerball Plus']:
                winning_numbers = ", ".join([str(random.randint(1, 50)) for _ in range(5)])
                bonus_ball = random.randint(1, 20)
            else:  # Daily Lottery
                winning_numbers = ", ".join([str(random.randint(1, 36)) for _ in range(5)])
                bonus_ball = None
            
            # Generate division data
            division1_winners = random.randint(0, 3)
            division1_payout = f"R{random.randint(1000000, 50000000):,}.00" if division1_winners > 0 else "R0.00"
            
            division2_winners = random.randint(5, 50)
            division2_payout = f"R{random.randint(50000, 500000):,}.00"
            
            division3_winners = random.randint(100, 500)
            division3_payout = f"R{random.randint(1000, 10000):,}.00"
            
            # Next draw date and jackpot
            next_draw_date = draw_date + timedelta(days=7 if lottery_type != 'Daily Lottery' else 1)
            next_jackpot = f"R{random.randint(2000000, 100000000):,}.00"
            
            # Create row
            row = {
                'Game Name': lottery_type,
                'Draw Number': str(draw_number_base + i),
                'Draw Date': draw_date.strftime('%Y-%m-%d'),
                'Winning Numbers': winning_numbers,
                'Bonus Ball': bonus_ball if bonus_ball is not None else '',
                'Division 1 Winners': division1_winners,
                'Division 1 Payout': division1_payout,
                'Division 2 Winners': division2_winners,
                'Division 2 Payout': division2_payout,
                'Division 3 Winners': division3_winners,
                'Division 3 Payout': division3_payout,
                'Next Draw Date': next_draw_date.strftime('%Y-%m-%d'),
                'Next Draw Jackpot': next_jackpot
            }
            rows.append(row)
        
        # Create DataFrame
        df = pd.DataFrame(rows)
        
        # Save to Excel
        df.to_excel(writer, sheet_name=lottery_type, index=False)
    
    # Add instructions sheet
    instructions_df = pd.DataFrame([
        {'Instructions': 'LOTTERY DATA IMPORT TEMPLATE'},
        {'Instructions': ''},
        {'Instructions': 'HOW TO USE THIS TEMPLATE:'},
        {'Instructions': '1. Each sheet represents a different lottery game'},
        {'Instructions': '2. Fill in the actual draw information on each sheet'}
    ])
    instructions_df.to_excel(writer, sheet_name='Instructions', index=False)
    
    # Save the Excel file
    writer.close()
    
    return output_path

if __name__ == "__main__":
    output_path = "attached_assets/lottery_test_data.xlsx"
    created_file = create_test_data_file(output_path)
    print(f"Created test data file: {created_file}")
    print(f"File size: {os.path.getsize(output_path)} bytes")
    print(f"Last modified: {datetime.fromtimestamp(os.path.getmtime(output_path))}")