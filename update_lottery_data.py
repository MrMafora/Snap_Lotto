#!/usr/bin/env python
"""
Script to update South African lottery data from Excel spreadsheet.
This script adds new records without purging existing data.
"""

import os
import sys
import logging
import json
import pandas as pd
import numpy as np
from datetime import datetime
from models import db, LotteryResult
import main  # Import main to get Flask application context

# Set up logging
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def parse_date(date_str):
    """Parse date from string format to datetime object"""
    try:
        if pd.isna(date_str):
            return None
        
        # If it's already a datetime object, return it
        if isinstance(date_str, datetime):
            return date_str
            
        # Convert to string if it's not
        date_str = str(date_str).strip()
        
        # Try various date formats
        for fmt in ['%Y-%m-%d', '%d/%m/%Y', '%d-%m-%Y', '%Y/%m/%d', '%m/%d/%Y']:
            try:
                return datetime.strptime(date_str, fmt)
            except ValueError:
                continue
                
        # If all formats fail, raise error
        raise ValueError(f"Couldn't parse date: {date_str}")
    except Exception as e:
        logger.error(f"Error parsing date {date_str}: {str(e)}")
        return None

def parse_numbers(numbers_str):
    """Parse numbers from string format to list of integers"""
    try:
        if pd.isna(numbers_str):
            return []
            
        # Handle different formats
        if isinstance(numbers_str, str):
            # Remove any non-numeric characters except commas, spaces, and brackets
            cleaned = ''.join(c for c in numbers_str if c.isdigit() or c in ', []')
            # Remove brackets if present
            cleaned = cleaned.replace('[', '').replace(']', '')
            # Split by comma or space
            if ',' in cleaned:
                return [int(n.strip()) for n in cleaned.split(',') if n.strip().isdigit()]
            else:
                return [int(n.strip()) for n in cleaned.split() if n.strip().isdigit()]
        elif isinstance(numbers_str, (int, float)):
            return [int(numbers_str)]
        else:
            return []
    except Exception as e:
        logger.error(f"Error parsing numbers {numbers_str}: {str(e)}")
        return []

def parse_divisions(divisions_data):
    """Parse divisions data from various formats to structured dictionary"""
    try:
        if pd.isna(divisions_data):
            return {}
            
        # If already a dict or json string, use it
        if isinstance(divisions_data, dict):
            return divisions_data
        elif isinstance(divisions_data, str):
            try:
                return json.loads(divisions_data)
            except json.JSONDecodeError:
                pass
                
        # Otherwise, parse from basic string format
        divisions = {}
        
        # Simple format: Division 1:0 winners@R0, Division 2:1 winner@R250000, etc.
        if isinstance(divisions_data, str):
            parts = divisions_data.split(',')
            for part in parts:
                part = part.strip()
                if ':' in part and '@' in part:
                    div_name, rest = part.split(':', 1)
                    winners_str, prize_str = rest.split('@', 1)
                    
                    # Clean up
                    div_name = div_name.strip()
                    winners = winners_str.strip().split(' ')[0].strip()
                    prize = prize_str.strip()
                    
                    # Add R if missing
                    if prize and not prize.startswith('R'):
                        prize = 'R' + prize
                        
                    divisions[div_name] = {
                        "winners": winners,
                        "prize": prize
                    }
        
        return divisions
    except Exception as e:
        logger.error(f"Error parsing divisions data {divisions_data}: {str(e)}")
        return {}

def standardize_lottery_type(lottery_type):
    """Standardize lottery type names for consistency"""
    lottery_type = str(lottery_type).strip()
    
    # Map common variations to standard names
    mapping = {
        'lotto': 'Lotto',
        'lotto plus 1': 'Lotto Plus 1',
        'lotto plus1': 'Lotto Plus 1',
        'lotto plus 2': 'Lotto Plus 2',
        'lotto plus2': 'Lotto Plus 2',
        'powerball': 'Powerball',
        'power ball': 'Powerball',
        'powerball plus': 'Powerball Plus',
        'power ball plus': 'Powerball Plus',
        'daily lotto': 'Daily Lotto',
        'dailylotto': 'Daily Lotto'
    }
    
    # Standardize case for lookup
    key = lottery_type.lower()
    if key in mapping:
        return mapping[key]
    
    return lottery_type

def update_excel_data(excel_file, flask_app=None):
    """
    Import lottery data from Excel spreadsheet without purging existing data.
    
    Args:
        excel_file (str): Path to Excel file
        flask_app: Flask app object for context (optional)
    """
    logger.info(f"Starting update of lottery data from {excel_file}")
    
    # Use app context if provided, otherwise use main app
    if flask_app:
        app = flask_app
    else:
        app = main.app
    
    with app.app_context():
        try:
            # Load the single sheet from the Excel file (expecting only one sheet)
            df = pd.read_excel(excel_file)
            logger.info(f"Loaded {len(df)} rows from Excel file")
            
            # Define possible column name mappings for different sheets
            possible_name_mappings = {
                'lottery_type': ['Game Name', 'Game Type'],
                'draw_number': ['Draw Number'],
                'draw_date': ['Draw Date'],
                'numbers': ['Winning Numbers (Numerical)', 'Winning Numbers'],
                'bonus_number': ['Bonus Ball', 'Bonus Number']
            }
            
            # Find actual column names based on possible mappings
            column_mapping = {}
            for target_col, possible_cols in possible_name_mappings.items():
                found = False
                for col in possible_cols:
                    if col in df.columns:
                        column_mapping[target_col] = col
                        found = True
                        break
                
                if not found and target_col in ['lottery_type', 'draw_number', 'draw_date', 'numbers']:
                    logger.error(f"Required column mapping not found for '{target_col}'")
                    print(f"Error: Could not find a column for '{target_col}'. Available columns: {list(df.columns)}")
                    return
            
            # Log the column mapping being used
            logger.info(f"Using column mapping: {column_mapping}")
            
            # Rename columns to match our expected names
            df.rename(columns={v: k for k, v in column_mapping.items()}, inplace=True)
            
            # Counters for summary
            counters = {
                'added': 0,
                'updated': 0,
                'skipped': 0,
                'errors': 0
            }
            
            # Process each row
            for _, row in df.iterrows():
                try:
                    # Extract and validate data
                    lottery_type = standardize_lottery_type(row['lottery_type'])
                    draw_number = str(row['draw_number']).strip()
                    draw_date = parse_date(row['draw_date'])
                    numbers = parse_numbers(row['numbers'])
                    
                    # Validate required fields
                    if not lottery_type or not draw_number or not draw_date or not numbers:
                        logger.warning(f"Skipping row due to missing required data: {row.to_dict()}")
                        counters['skipped'] += 1
                        continue
                    
                    # Special validation for Daily Lotto - must have exactly 5 numbers
                    if lottery_type == 'Daily Lotto' and len(numbers) != 5:
                        logger.warning(f"Skipping Daily Lotto draw {draw_number} - must have exactly 5 numbers, found {len(numbers)}")
                        counters['skipped'] += 1
                        continue
                    
                    # Extract optional fields
                    bonus_numbers = []
                    if 'bonus_number' in row and not pd.isna(row['bonus_number']):
                        bonus_numbers = parse_numbers(row['bonus_number'])
                    
                    # Build divisions data from the spreadsheet's division columns
                    divisions = {}
                    
                    # Define patterns for division columns across different sheet formats
                    division_column_patterns = [
                        # Lotto format: "Div X Winners" / "Div X Winnings"
                        {'winners_pattern': 'Div {0} Winners', 'prize_pattern': 'Div {0} Winnings'},
                        # PowerBall format: "Division X Winners" / "Division X Prize"
                        {'winners_pattern': 'Division {0} Winners', 'prize_pattern': 'Division {0} Prize'}
                    ]
                    
                    # Try all patterns to find division data
                    for div in range(1, 9):  # Support up to 8 divisions
                        for pattern in division_column_patterns:
                            winners_col = pattern['winners_pattern'].format(div)
                            prize_col = pattern['prize_pattern'].format(div)
                            
                            # Check if columns exist in the dataframe or the row (row.get is safer)
                            if winners_col in df.columns and prize_col in df.columns:
                                winners = row.get(winners_col)
                                prize = row.get(prize_col)
                                
                                if not pd.isna(winners) and not pd.isna(prize):
                                    # Format prize with R if needed
                                    if isinstance(prize, str) and not prize.startswith('R'):
                                        prize = 'R' + prize
                                    elif isinstance(prize, (int, float)):
                                        prize = f'R{prize:,.2f}'
                                    
                                    divisions[f'Division {div}'] = {
                                        'winners': str(int(winners) if isinstance(winners, (int, float)) else winners),
                                        'prize': prize
                                    }
                                    break  # Found this division, move to next
                    
                    # Check if this draw already exists
                    existing = LotteryResult.query.filter_by(
                        lottery_type=lottery_type,
                        draw_number=draw_number
                    ).first()
                    
                    if existing:
                        # Update existing record
                        existing.draw_date = draw_date
                        existing.numbers = json.dumps(numbers)
                        if bonus_numbers:
                            existing.bonus_numbers = json.dumps(bonus_numbers)
                        if divisions:
                            existing.divisions = json.dumps(divisions)
                        existing.ocr_provider = 'manual-import'
                        existing.ocr_model = 'excel-spreadsheet'
                        existing.ocr_timestamp = datetime.utcnow()
                        db.session.commit()
                        logger.info(f"Updated {lottery_type} draw {draw_number}")
                        counters['updated'] += 1
                    else:
                        # Create new record
                        new_result = LotteryResult(
                            lottery_type=lottery_type,
                            draw_number=draw_number,
                            draw_date=draw_date,
                            numbers=json.dumps(numbers),
                            bonus_numbers=json.dumps(bonus_numbers) if bonus_numbers else None,
                            divisions=json.dumps(divisions) if divisions else None,
                            source_url='imported-from-excel',
                            ocr_provider='manual-import',
                            ocr_model='excel-spreadsheet',
                            ocr_timestamp=datetime.utcnow()
                        )
                        db.session.add(new_result)
                        db.session.commit()
                        logger.info(f"Added new {lottery_type} draw {draw_number}")
                        counters['added'] += 1
                
                except Exception as e:
                    logger.error(f"Error processing row: {str(e)}")
                    counters['errors'] += 1
                    continue
            
            # Print summary
            print(f"Import summary:")
            print(f"  - Added: {counters['added']} new draws")
            print(f"  - Updated: {counters['updated']} existing draws")
            print(f"  - Skipped: {counters['skipped']} rows")
            print(f"  - Errors: {counters['errors']} rows")
            
        except Exception as e:
            logger.error(f"Error during import operation: {str(e)}")
            print(f"Error: {str(e)}")
            return

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python update_lottery_data.py <excel_file>")
        sys.exit(1)
        
    excel_file = sys.argv[1]
    if not os.path.exists(excel_file):
        print(f"Error: File not found: {excel_file}")
        sys.exit(1)
        
    update_excel_data(excel_file)