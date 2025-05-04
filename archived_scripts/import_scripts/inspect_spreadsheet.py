#!/usr/bin/env python
"""
Script to inspect the lottery data spreadsheet without importing.
"""

import os
import sys
import pandas as pd
import numpy as np
from datetime import datetime

def inspect_spreadsheet(filepath):
    """
    Inspect the contents of a lottery data spreadsheet.
    
    Args:
        filepath (str): Path to the Excel file
    """
    print(f"Inspecting spreadsheet: {filepath}")
    
    try:
        # Read the Excel file
        df = pd.read_excel(filepath)
        
        # Display basic info
        print(f"\nTotal rows: {len(df)}")
        print(f"Columns: {list(df.columns)}")
        
        # Check for Lotto draw 2534
        lotto_data = df[df['Game Name'] == 'Lotto']
        print(f"\nTotal Lotto rows: {len(lotto_data)}")
        
        # Look specifically for draw 2534
        draw_2534 = df[df['Draw Number'] == 2534]
        print(f"\nRows with Draw Number 2534: {len(draw_2534)}")
        
        # Display all Draw 2534 records
        if not draw_2534.empty:
            print("\nDetailed Draw 2534 data:")
            for index, row in draw_2534.iterrows():
                game_type = row.get('Game Name', 'Unknown')
                draw_date = row.get('Draw Date', 'Unknown')
                
                # Get winning numbers from the 'Winning Numbers (Numerical)' column
                numbers = []
                if 'Winning Numbers (Numerical)' in row and not pd.isna(row['Winning Numbers (Numerical)']):
                    numbers_str = str(row['Winning Numbers (Numerical)'])
                    # Try to parse comma-separated numbers
                    try:
                        numbers = [int(n.strip()) for n in numbers_str.split(',') if n.strip()]
                    except ValueError:
                        numbers = [numbers_str]  # If parsing fails, just use the raw string
                
                # Look for bonus number
                bonus = None
                if 'Bonus Ball' in row and not pd.isna(row['Bonus Ball']):
                    bonus = row['Bonus Ball']
                
                print(f"Row {index+1}: {game_type}, Date: {draw_date}, Numbers: {numbers}, Bonus: {bonus}")
        else:
            print("No records found for Draw Number 2534")
        
        # Check if there are any Lotto games with draw 2534
        lotto_2534 = df[(df['Game Name'] == 'Lotto') & (df['Draw Number'] == 2534)]
        print(f"\nLotto rows with Draw Number 2534: {len(lotto_2534)}")
        
        if not lotto_2534.empty:
            print("Found Lotto draw 2534!")
            for index, row in lotto_2534.iterrows():
                print(f"Row {index+1}:")
                for col in row.index:
                    if not pd.isna(row[col]):  # Only show non-empty cells
                        print(f"  {col}: {row[col]}")
        else:
            print("No Lotto draw 2534 found in the spreadsheet")
        
        # Show first 3 rows for sample data format
        print("\nSample data (first 3 rows):")
        for index, row in df.head(3).iterrows():
            print(f"Row {index+1}:")
            game_name = row.get('Game Name', 'Unknown')
            draw_number = row.get('Draw Number', 'Unknown')
            print(f"  Game Name: {game_name}")
            print(f"  Draw Number: {draw_number}")
            print(f"  Draw Date: {row.get('Draw Date', 'Unknown')}")
            print(f"  Winning Numbers: {row.get('Winning Numbers (Numerical)', 'Unknown')}")
            print(f"  Bonus Ball: {row.get('Bonus Ball', 'Unknown')}")
            print("---")
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python inspect_spreadsheet.py <excel_file>")
        sys.exit(1)
    
    excel_file = sys.argv[1]
    if not os.path.exists(excel_file):
        print(f"Error: File {excel_file} not found")
        sys.exit(1)
    
    inspect_spreadsheet(excel_file)