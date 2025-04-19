#!/usr/bin/env python
"""
Script to import just Lotto draw 2534 from the spreadsheet.
"""

import json
import pandas as pd
import numpy as np
from datetime import datetime
from models import db, LotteryResult
import main

def import_lotto_2534(excel_file):
    """Import just the Lotto draw 2534 from the spreadsheet"""
    try:
        # Read the spreadsheet
        df = pd.read_excel(excel_file)
        
        # Find the Lotto 2534 row (case-insensitive)
        lotto_2534 = df[(df['Game Name'].str.upper() == 'LOTTO') & (df['Draw Number'] == 2534)]
        
        if lotto_2534.empty:
            print("Error: Could not find Lotto draw 2534 in the spreadsheet")
            return False
            
        # Get the first matching row
        row = lotto_2534.iloc[0]
        
        # Extract data
        draw_number = str(row['Draw Number'])
        draw_date = row['Draw Date']
        
        # Parse the winning numbers
        numbers_str = str(row['Winning Numbers (Numerical)'])
        numbers_list = [int(n.strip()) for n in numbers_str.split() if n.strip().isdigit()]
        
        # If parsing fails, try alternative parsing
        if not numbers_list:
            clean_str = ''.join(c if c.isdigit() or c.isspace() else ' ' for c in numbers_str)
            numbers_list = [int(num) for num in clean_str.split() if num.strip().isdigit()]
        
        # Parse bonus number
        bonus_number = [int(row['Bonus Ball'])] if not pd.isna(row['Bonus Ball']) else []
        
        # Format divisions if present
        divisions_dict = {}
        div_columns = [col for col in row.index if 'Div' in col and 'Winners' in col or 'Winnings' in col]
        
        if div_columns:
            for i in range(1, 9):  # Up to 8 divisions
                winners_col = f'Div {i} Winners'
                winnings_col = f'Div {i} Winnings'
                
                if winners_col in row and winnings_col in row:
                    if not pd.isna(row[winners_col]) and not pd.isna(row[winnings_col]):
                        winners = int(row[winners_col])
                        winnings = str(row[winnings_col])
                        
                        # Format winnings as currency if not already
                        if not winnings.startswith('R'):
                            winnings = f"R{winnings}"
                            
                        divisions_dict[f"Division {i}"] = {
                            "winners": winners,
                            "prize": winnings
                        }
        
        print(f"Found Lotto 2534 with date {draw_date}")
        print(f"Numbers: {numbers_list}")
        print(f"Bonus: {bonus_number}")
        
        with main.app.app_context():
            # Check if this record already exists
            existing = LotteryResult.query.filter_by(
                lottery_type='Lotto',
                draw_number=draw_number
            ).first()
            
            if existing:
                print(f"Lotto draw {draw_number} already exists in the database")
                return True
                
            # Create the new lottery result record
            new_result = LotteryResult(
                lottery_type='Lotto',
                draw_number=draw_number,
                draw_date=draw_date,
                numbers=json.dumps(numbers_list),
                bonus_numbers=json.dumps(bonus_number),
                divisions=json.dumps(divisions_dict) if divisions_dict else None,
                source_url='spreadsheet-import',
                ocr_provider='manual-import',
                ocr_model='excel-spreadsheet',
                ocr_timestamp=datetime.utcnow().isoformat()
            )
            
            db.session.add(new_result)
            db.session.commit()
            print(f"Successfully added Lotto draw {draw_number} (ID: {new_result.id})")
            return True
            
    except Exception as e:
        print(f"Error: {str(e)}")
        return False

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python import_lotto_2534.py <excel_file>")
        sys.exit(1)
        
    excel_file = sys.argv[1]
    import_lotto_2534(excel_file)