#!/usr/bin/env python
"""
Script to specifically import PowerBall data from Excel spreadsheet.
"""

import os
import sys
import logging
import json
import pandas as pd
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

def import_powerball_data(excel_file, flask_app=None):
    """
    Import PowerBall data from Excel spreadsheet.
    
    Args:
        excel_file (str): Path to Excel file
        flask_app: Flask app object for context (optional)
    """
    logger.info(f"Starting import of PowerBall data from {excel_file}")
    
    # Use app context if provided, otherwise use main app
    if flask_app:
        app = flask_app
    else:
        app = main.app
    
    with app.app_context():
        try:
            # Load PowerBall sheet
            try:
                df_power = pd.read_excel(excel_file, sheet_name='Powerball')
                logger.info(f"Loaded {len(df_power)} PowerBall rows")
            except Exception as e:
                logger.error(f"Error loading PowerBall sheet: {str(e)}")
                print(f"Error: Could not load PowerBall sheet: {str(e)}")
                return
            
            # Load PowerBall Plus sheet
            try:
                df_plus = pd.read_excel(excel_file, sheet_name='Powerball Plus')
                logger.info(f"Loaded {len(df_plus)} PowerBall Plus rows")
            except Exception as e:
                logger.error(f"Error loading PowerBall Plus sheet: {str(e)}")
                df_plus = None
            
            # Counters for summary
            counters = {
                'added': 0,
                'updated': 0,
                'skipped': 0,
                'errors': 0
            }
            
            # Process PowerBall rows
            for _, row in df_power.iterrows():
                try:
                    # Extract required data
                    game_type = 'Powerball'
                    draw_number = str(row['Draw Number']).strip()
                    draw_date = parse_date(row['Draw Date'])
                    numbers = parse_numbers(row['Winning Numbers'])
                    bonus_number = parse_numbers(row['Bonus Number'])
                    
                    # Skip if missing required data
                    if not draw_number or not draw_date or not numbers:
                        logger.warning(f"Skipping PowerBall row due to missing data")
                        counters['skipped'] += 1
                        continue
                    
                    # Convert empty list to None
                    bonus_numbers = bonus_number if bonus_number else None
                    
                    # Build division data
                    divisions = {}
                    for div in range(1, 9):
                        winners_col = f'Division {div} Winners'
                        prize_col = f'Division {div} Prize'
                        
                        if winners_col in df_power.columns and prize_col in df_power.columns:
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
                    
                    # Check if this draw already exists
                    existing = LotteryResult.query.filter_by(
                        lottery_type=game_type,
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
                        logger.info(f"Updated {game_type} draw {draw_number}")
                        counters['updated'] += 1
                    else:
                        # Create new record
                        new_result = LotteryResult(
                            lottery_type=game_type,
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
                        logger.info(f"Added new {game_type} draw {draw_number}")
                        counters['added'] += 1
                
                except Exception as e:
                    logger.error(f"Error processing PowerBall row: {str(e)}")
                    counters['errors'] += 1
                    continue
            
            # Process PowerBall Plus rows if available
            if df_plus is not None:
                for _, row in df_plus.iterrows():
                    try:
                        # Extract required data
                        game_type = 'Powerball Plus'
                        draw_number = str(row['Draw Number']).strip()
                        draw_date = parse_date(row['Draw Date'])
                        numbers = parse_numbers(row['Winning Numbers'])
                        bonus_number = parse_numbers(row['Bonus Number'])
                        
                        # Skip if missing required data
                        if not draw_number or not draw_date or not numbers:
                            logger.warning(f"Skipping PowerBall Plus row due to missing data")
                            counters['skipped'] += 1
                            continue
                        
                        # Convert empty list to None
                        bonus_numbers = bonus_number if bonus_number else None
                        
                        # Build division data
                        divisions = {}
                        for div in range(1, 9):
                            winners_col = f'Division {div} Winners'
                            prize_col = f'Division {div} Prize'
                            
                            if winners_col in df_plus.columns and prize_col in df_plus.columns:
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
                        
                        # Check if this draw already exists
                        existing = LotteryResult.query.filter_by(
                            lottery_type=game_type,
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
                            logger.info(f"Updated {game_type} draw {draw_number}")
                            counters['updated'] += 1
                        else:
                            # Create new record
                            new_result = LotteryResult(
                                lottery_type=game_type,
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
                            logger.info(f"Added new {game_type} draw {draw_number}")
                            counters['added'] += 1
                    
                    except Exception as e:
                        logger.error(f"Error processing PowerBall Plus row: {str(e)}")
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
        print("Usage: python import_powerball.py <excel_file>")
        sys.exit(1)
        
    excel_file = sys.argv[1]
    if not os.path.exists(excel_file):
        print(f"Error: File not found: {excel_file}")
        sys.exit(1)
        
    import_powerball_data(excel_file)