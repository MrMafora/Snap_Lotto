import pandas as pd
import numpy as np
import json
import logging
import traceback
from datetime import datetime
import os
import re
from sqlalchemy import desc
from sqlalchemy.exc import SQLAlchemyError
from excel_date_utils import parse_excel_date
from models import LotteryResult, ImportHistory, ImportedRecord
from flask import current_app

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def standardize_lottery_type(lottery_type):
    """
    Standardize lottery type names to ensure consistency, prioritizing "Lottery" naming.
    
    Args:
        lottery_type (str): Original lottery type name
        
    Returns:
        str: Standardized lottery type name
    """
    if not lottery_type:
        return lottery_type
    
    # Convert to string if not already
    if not isinstance(lottery_type, str):
        lottery_type = str(lottery_type)
    
    # Normalize to lowercase for matching
    lottery_lower = lottery_type.lower().strip()
    
    # Define standardized mappings - prioritize "Lottery" terminology
    standard_mapping = {
        # Primary forms with "Lottery"
        'lottery': 'Lottery',
        'lottery plus 1': 'Lottery Plus 1',
        'lottery+1': 'Lottery Plus 1',
        'lottery plus one': 'Lottery Plus 1',
        'lottery plus1': 'Lottery Plus 1',
        'lottery + 1': 'Lottery Plus 1',
        'lottery plus 2': 'Lottery Plus 2',
        'lottery+2': 'Lottery Plus 2',
        'lottery plus two': 'Lottery Plus 2',
        'lottery plus2': 'Lottery Plus 2',
        'lottery + 2': 'Lottery Plus 2',
        'daily lottery': 'Daily Lottery',
        'dailylottery': 'Daily Lottery',
        
        # Legacy forms with "Lotto"
        'lotto': 'Lottery',
        'lotto plus 1': 'Lottery Plus 1',
        'lotto+1': 'Lottery Plus 1',
        'lotto plus one': 'Lottery Plus 1',
        'lotto plus1': 'Lottery Plus 1',
        'lotto + 1': 'Lottery Plus 1',
        'lotto plus 2': 'Lottery Plus 2',
        'lotto+2': 'Lottery Plus 2',
        'lotto plus two': 'Lottery Plus 2',
        'lotto plus2': 'Lottery Plus 2',
        'lotto + 2': 'Lottery Plus 2',
        'daily lotto': 'Daily Lottery',
        'dailylotto': 'Daily Lottery',
        
        # Powerball forms (unchanged)
        'powerball': 'Powerball',
        'powerball+': 'Powerball Plus',
        'powerball plus': 'Powerball Plus',
    }
    
    # Check for direct match in mappings
    if lottery_lower in standard_mapping:
        return standard_mapping[lottery_lower]
    
    # Check for partial matches based on known prefixes/patterns
    if lottery_lower.startswith('lottery plus 1') or lottery_lower.startswith('lotto plus 1'):
        return 'Lottery Plus 1'
    elif lottery_lower.startswith('lottery plus 2') or lottery_lower.startswith('lotto plus 2'):
        return 'Lottery Plus 2'
    elif lottery_lower.startswith('powerball plus'):
        return 'Powerball Plus'
    elif lottery_lower.startswith('powerball'):
        return 'Powerball'
    elif lottery_lower.startswith('daily lottery') or lottery_lower.startswith('daily lotto'):
        return 'Daily Lottery'
    elif lottery_lower == 'lottery' or lottery_lower == 'lotto':
        return 'Lottery'
    
    # If no match, log a warning and return original with proper capitalization
    logger.warning(f"No standard match found for lottery type: '{lottery_type}'")
    return str(lottery_type).strip()

def parse_numbers(numbers_str):
    """
    Parse lottery numbers from various string formats to a list of integers.
    
    Args:
        numbers_str (str): String containing numbers
        
    Returns:
        list: List of integers
    """
    if not numbers_str or pd.isna(numbers_str):
        return []
        
    # Skip example data
    if isinstance(numbers_str, str) and numbers_str.lower().startswith('example:'):
        return []
        
    # Convert to string if it's not already
    if not isinstance(numbers_str, str):
        numbers_str = str(numbers_str)
        
    # Try different delimiters: comma, space, semicolon
    for delimiter in [',', ' ', ';']:
        # Try splitting by this delimiter
        parts = numbers_str.split(delimiter)
        # If we get multiple parts and they look like numbers, use this delimiter
        if len(parts) > 1 and all(part.strip().isdigit() for part in parts if part.strip()):
            return [int(part.strip()) for part in parts if part.strip().isdigit()]
    
    # If no delimiter worked, check if the string is just a single number
    if numbers_str.strip().isdigit():
        return [int(numbers_str.strip())]
    
    # If we got here, we couldn't parse the numbers
    return []

def parse_divisions(division_data):
    """
    Parse division data from structured columns in the multi-sheet template.
    
    Args:
        division_data (dict): Division data from DataFrame row
        
    Returns:
        dict: Structured divisions dictionary
    """
    divisions = {}
    
    # Process division winners and payouts from the template
    for i in range(1, 6):  # Divisions 1-5
        winners_key = f'Division {i} Winners'
        payout_key = f'Division {i} Payout'
        
        # Skip if both values are empty or if this is example data
        if (winners_key not in division_data or pd.isna(division_data[winners_key])) and \
           (payout_key not in division_data or pd.isna(division_data[payout_key])):
            continue
            
        # Skip example data
        if isinstance(division_data.get(winners_key), str) and \
            division_data.get(winners_key, '').lower().startswith('example:'):
            continue
            
        division_key = f'Division {i}'
        divisions[division_key] = {}
        
        # Process winners
        if winners_key in division_data and not pd.isna(division_data[winners_key]):
            winners_value = division_data[winners_key]
            if isinstance(winners_value, str):
                # Clean up the string - remove "Example:" prefix and any non-numeric chars
                winners_value = re.sub(r'[^\d]', '', winners_value)
                if winners_value.isdigit():
                    divisions[division_key]['winners'] = int(winners_value)
            elif isinstance(winners_value, (int, float)):
                divisions[division_key]['winners'] = int(winners_value)
        
        # Process payouts
        if payout_key in division_data and not pd.isna(division_data[payout_key]):
            payout_value = division_data[payout_key]
            if isinstance(payout_value, str):
                # Clean up the string - remove "Example:" prefix
                payout_value = payout_value.replace('Example:', '').strip()
                # Add R prefix if missing
                if not payout_value.startswith('R'):
                    payout_value = f'R{payout_value}'
                divisions[division_key]['prize'] = payout_value
            elif isinstance(payout_value, (int, float)):
                divisions[division_key]['prize'] = f'R{payout_value:,.2f}'
    
    return divisions

def process_row(row, sheet_name):
    """
    Process a single row from a sheet in the multi-sheet template.
    
    Args:
        row (pandas.Series): Row data from DataFrame
        sheet_name (str): Name of the sheet (used as fallback for lottery_type)
        
    Returns:
        dict: Processed lottery data
    """
    # Skip rows with example data
    draw_number = row.get('Draw Number')
    if isinstance(draw_number, str) and draw_number.lower().startswith('example:'):
        return None
        
    # Skip placeholder rows
    draw_date = row.get('Draw Date')
    if isinstance(draw_date, str) and draw_date == 'YYYY-MM-DD':
        return None
        
    # Get lottery type from 'Game Name' column or sheet name
    lottery_type = row.get('Game Name')
    if pd.isna(lottery_type) or not lottery_type:
        lottery_type = sheet_name
        
    # Standardize the lottery type
    standard_lottery_type = standardize_lottery_type(lottery_type)
    
    # Extract draw number
    draw_number = row.get('Draw Number')
    if pd.isna(draw_number) or not draw_number:
        # We need a draw number, skip this row if it's missing
        logger.warning(f"Skipping row because draw number is missing for {standard_lottery_type}")
        return None
        
    # Clean up draw number if it's a string
    if isinstance(draw_number, str):
        # Remove "Example:" prefix if present
        draw_number = draw_number.replace('Example:', '').strip()
        # Extract just the numeric part
        draw_number = re.sub(r'[^\d]', '', draw_number)
    
    # Extract draw date
    draw_date = row.get('Draw Date')
    if pd.isna(draw_date) or not draw_date:
        # We need a draw date, skip this row if it's missing
        logger.warning(f"Skipping row because draw date is missing for {standard_lottery_type} - {draw_number}")
        return None
        
    # Parse the draw date
    parsed_date = parse_excel_date(draw_date)
    if not parsed_date:
        logger.warning(f"Skipping row because draw date could not be parsed: {draw_date}")
        return None
        
    # Extract winning numbers
    numbers_str = row.get('Winning Numbers')
    winning_numbers = parse_numbers(numbers_str)
    if not winning_numbers:
        logger.warning(f"Skipping row because winning numbers could not be parsed: {numbers_str}")
        return None
    
    # Extract bonus ball/powerball
    bonus_str = row.get('Bonus Ball')
    bonus_ball = None
    if not pd.isna(bonus_str):
        if isinstance(bonus_str, str) and bonus_str.lower().startswith('example:'):
            # Skip example data
            pass
        else:
            # Try to extract just the numeric part
            if isinstance(bonus_str, str):
                bonus_str = re.sub(r'[^\d]', '', bonus_str.replace('Example:', '').strip())
            
            try:
                bonus_ball = int(bonus_str)
            except (ValueError, TypeError):
                logger.warning(f"Could not parse bonus ball: {bonus_str}")
    
    # Process division data
    divisions = parse_divisions(row)
    
    # Create the lottery data dictionary
    lottery_data = {
        'lottery_type': standard_lottery_type,
        'draw_number': draw_number,
        'draw_date': parsed_date,
        'numbers': winning_numbers,
        'bonus_ball': bonus_ball,
        'divisions': divisions
    }
    
    # Extract additional optional fields
    next_draw_date = row.get('Next Draw Date')
    if not pd.isna(next_draw_date):
        parsed_next_date = parse_excel_date(next_draw_date)
        if parsed_next_date:
            lottery_data['next_draw_date'] = parsed_next_date
    
    next_jackpot = row.get('Next Draw Jackpot')
    if not pd.isna(next_jackpot):
        if isinstance(next_jackpot, str):
            # Clean up and ensure R prefix
            if not next_jackpot.startswith('R'):
                next_jackpot = f'R{next_jackpot}'
            lottery_data['next_jackpot'] = next_jackpot
        elif isinstance(next_jackpot, (int, float)):
            lottery_data['next_jackpot'] = f'R{next_jackpot:,.2f}'
    
    return lottery_data

def import_multisheet_excel(excel_file, flask_app=None):
    """
    Import lottery data from a multi-sheet Excel spreadsheet.
    Each sheet represents a different lottery game.
    
    Args:
        excel_file (str): Path to Excel file
        flask_app: Flask app object for context (optional)
        
    Returns:
        dict: Import statistics
    """
    # Initialize counters
    imported_count = 0
    updated_count = 0
    error_count = 0
    total_count = 0
    imported_records = []
    
    # Verify the file exists
    if not os.path.exists(excel_file):
        logger.error(f"Excel file not found: {excel_file}")
        return {
            'success': False,
            'error': f"Excel file not found: {excel_file}"
        }
    
    try:
        # Load the Excel file
        logger.info(f"Loading Excel file: {excel_file}")
        xls = pd.ExcelFile(excel_file)
        
        # Get all sheet names except 'Instructions'
        sheet_names = [sheet for sheet in xls.sheet_names if sheet.lower() != 'instructions']
        logger.info(f"Found {len(sheet_names)} data sheets: {sheet_names}")
        
        # Process each sheet
        for sheet_name in sheet_names:
            try:
                logger.info(f"Processing sheet: {sheet_name}")
                
                # Read the sheet
                df = pd.read_excel(excel_file, sheet_name=sheet_name)
                
                # Skip empty sheets
                if df.empty:
                    logger.warning(f"Sheet '{sheet_name}' is empty, skipping")
                    continue
                
                # Process each row in the sheet
                for _, row in df.iterrows():
                    try:
                        total_count += 1
                        
                        # Process the row
                        lottery_data = process_row(row, sheet_name)
                        
                        # Skip if the row couldn't be processed
                        if not lottery_data:
                            logger.warning(f"Skipping row in sheet '{sheet_name}' - invalid or example data")
                            continue
                        
                        # Process row data
                        result, is_new = save_lottery_result(lottery_data, flask_app)
                        if result:
                            if is_new:
                                imported_count += 1
                            else:
                                updated_count += 1
                            
                            # Add to imported records list
                            imported_records.append({
                                'lottery_type': result.lottery_type,
                                'draw_number': result.draw_number,
                                'draw_date': result.draw_date,
                                'is_new': is_new,
                                'lottery_result_id': result.id
                            })
                    
                    except Exception as e:
                        error_count += 1
                        logger.error(f"Error processing row in sheet '{sheet_name}': {str(e)}")
                        logger.error(traceback.format_exc())
            
            except Exception as e:
                error_count += 1
                logger.error(f"Error processing sheet '{sheet_name}': {str(e)}")
                logger.error(traceback.format_exc())
        
        logger.info(f"Import completed. Added: {imported_count}, Updated: {updated_count}, Errors: {error_count}")
        
        # Return statistics
        return {
            'success': True,
            'added': imported_count,
            'updated': updated_count,
            'total': total_count,
            'errors': error_count,
            'imported_records': imported_records
        }
    
    except Exception as e:
        logger.error(f"Error importing Excel file: {str(e)}")
        logger.error(traceback.format_exc())
        return {
            'success': False,
            'error': str(e)
        }

def save_lottery_result(lottery_data, flask_app=None):
    """
    Save lottery result to database.
    
    Args:
        lottery_data (dict): Lottery data dictionary
        flask_app: Flask app object for context (optional)
        
    Returns:
        tuple: (LotteryResult object, is_new boolean flag)
    """
    # If no Flask app is provided, we're running outside a context
    # Just return the data as if it was processed (for testing)
    if flask_app is None:
        # Create a mock result object with the key fields
        from types import SimpleNamespace
        mock_result = SimpleNamespace(
            id=0,
            lottery_type=lottery_data['lottery_type'],
            draw_number=lottery_data['draw_number'],
            draw_date=lottery_data['draw_date']
        )
        return mock_result, True  # Assume it would be new
    
    try:
        # With a Flask app, we can properly save to database
        with flask_app.app_context():
            # Check if this lottery result already exists
            existing_result = LotteryResult.query.filter_by(
                lottery_type=lottery_data['lottery_type'],
                draw_number=lottery_data['draw_number']
            ).first()
            
            if existing_result:
                # Update existing record
                existing_result.draw_date = lottery_data['draw_date']
                existing_result.numbers = json.dumps(lottery_data['numbers'])
                
                if 'bonus_ball' in lottery_data and lottery_data['bonus_ball'] is not None:
                    existing_result.bonus_ball = lottery_data['bonus_ball']
                    
                if 'divisions' in lottery_data and lottery_data['divisions']:
                    existing_result.divisions = json.dumps(lottery_data['divisions'])
                    
                if 'next_draw_date' in lottery_data:
                    existing_result.next_draw_date = lottery_data['next_draw_date']
                    
                if 'next_jackpot' in lottery_data:
                    existing_result.next_jackpot = lottery_data['next_jackpot']
                
                # Save the changes
                flask_app.db.session.commit()
                
                return existing_result, False
            else:
                # Create new record
                new_result = LotteryResult(
                    lottery_type=lottery_data['lottery_type'],
                    draw_number=lottery_data['draw_number'],
                    draw_date=lottery_data['draw_date'],
                    numbers=json.dumps(lottery_data['numbers']),
                    bonus_ball=lottery_data.get('bonus_ball'),
                    divisions=json.dumps(lottery_data.get('divisions', {})),
                    next_draw_date=lottery_data.get('next_draw_date'),
                    next_jackpot=lottery_data.get('next_jackpot')
                )
                
                # Add and commit
                flask_app.db.session.add(new_result)
                flask_app.db.session.commit()
                
                return new_result, True
    
    except SQLAlchemyError as e:
        if flask_app:
            flask_app.db.session.rollback()
        logger.error(f"Database error saving lottery result: {str(e)}")
        return None, False
    except Exception as e:
        if flask_app:
            flask_app.db.session.rollback()
        logger.error(f"Error saving lottery result: {str(e)}")
        return None, False

if __name__ == "__main__":
    # For testing directly
    import sys
    
    if len(sys.argv) > 1:
        excel_file = sys.argv[1]
        print(f"Processing Excel file: {excel_file}")
        result = import_multisheet_excel(excel_file)
        print(json.dumps(result, default=str, indent=2))
    else:
        print("Usage: python multi_sheet_import.py <excel_file>")