"""
Fixed Excel Import Module for Snap Lotto
Designed to work with single-sheet Excel files containing all lottery data
"""

import pandas as pd
import numpy as np
import json
import logging
from datetime import datetime
import os
import re
import traceback
from sqlalchemy import text
from models import db, LotteryResult, ImportHistory, ImportedRecord
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
    if lottery_type is None:
        return None
        
    # Convert to string in case it's a numeric value
    lottery_type_str = str(lottery_type).strip()
    
    # Common lottery type mappings
    mapping = {
        'lotto': 'Lottery',
        'daily lotto': 'Daily Lottery',
        'powerball': 'Powerball',
        'powerball plus': 'Powerball Plus',
        'lotto plus 1': 'Lottery Plus 1',
        'lotto plus 2': 'Lottery Plus 2',
        'daily': 'Daily Lottery'
    }
    
    # Try to match against known lottery types (case-insensitive)
    lottery_type_lower = lottery_type_str.lower()
    for key, value in mapping.items():
        if key in lottery_type_lower:
            return value
            
    # Return original if no match found
    return lottery_type_str

def parse_excel_date(date_value):
    """
    Parse Excel date value into Python datetime.
    
    Args:
        date_value: Date value from Excel (can be string, datetime, or integer)
        
    Returns:
        datetime: Parsed datetime object or None if parsing fails
    """
    if date_value is None:
        return None
        
    # If it's already a datetime object, return it
    if isinstance(date_value, datetime):
        return date_value
        
    # Try parsing Excel date number
    try:
        # Excel dates are days since 1900-01-01
        if isinstance(date_value, (int, float)):
            # Check if it seems like an Excel date number (reasonable range)
            if 35000 < date_value < 50000:  # Valid dates roughly between 1995 and 2050
                return datetime.fromordinal(datetime(1900, 1, 1).toordinal() - 2 + int(date_value))
    except Exception as e:
        logger.debug(f"Failed to parse as Excel date number: {str(e)}")
    
    # Try parsing string formats    
    if isinstance(date_value, str):
        date_str = date_value.strip()
        
        # Try common date formats in South Africa
        date_formats = [
            '%Y-%m-%d',            # 2023-01-31
            '%d/%m/%Y',            # 31/01/2023
            '%d-%m-%Y',            # 31-01-2023
            '%d %B %Y',            # 31 January 2023
            '%d %b %Y',            # 31 Jan 2023
            '%B %d, %Y',           # January 31, 2023
            '%d.%m.%Y',            # 31.01.2023
            '%Y/%m/%d',            # 2023/01/31
            '%m/%d/%Y',            # 01/31/2023 (US format)
            '%d %m %Y',            # 31 01 2023
            '%Y%m%d',              # 20230131
        ]
        
        for date_format in date_formats:
            try:
                return datetime.strptime(date_str, date_format)
            except ValueError:
                continue
                
    logger.warning(f"Could not parse date value: {date_value}")
    return None

def parse_numbers(numbers_str):
    """
    Parse lottery numbers from string format to list of integers.
    
    Args:
        numbers_str (str): String representation of numbers
        
    Returns:
        list: List of numbers as integers
    """
    if numbers_str is None:
        return []
        
    # Convert to string if it's not already
    if not isinstance(numbers_str, str):
        numbers_str = str(numbers_str)
    
    # Remove any non-numeric and non-delimiter characters
    # Allow numbers, commas, spaces, and basic delimiters
    clean_str = re.sub(r'[^0-9,\s\-+|]', '', numbers_str)
    
    # Split by common delimiters
    numbers = re.split(r'[,\s\-+|]+', clean_str)
    
    # Convert to integers and filter out empty values
    result = []
    for num in numbers:
        if num:
            try:
                result.append(int(num))
            except ValueError:
                continue
                
    return result

def parse_divisions(row):
    """
    Parse division data from Excel row.
    
    Args:
        row (pandas.Series): Row data from Excel
        
    Returns:
        dict: Division data with winners and prizes
    """
    divisions = {}
    
    for i in range(1, 9):  # Support up to 8 divisions
        # Check if these columns exist
        desc_col = f'Div {i} Description'
        winners_col = f'Div {i} Winners'
        winnings_col = f'Div {i} Winnings'
        
        # Skip if essential columns missing
        if desc_col not in row.index or winners_col not in row.index:
            continue
            
        # Skip if both description and winners are empty
        if pd.isna(row[desc_col]) and pd.isna(row[winners_col]):
            continue
            
        # Get division description
        desc = str(row[desc_col]) if not pd.isna(row[desc_col]) else f'Division {i}'
        
        # Get winner count and prize amount
        winners = 0
        if not pd.isna(row[winners_col]):
            try:
                winners = int(row[winners_col])
            except (ValueError, TypeError):
                # Try to extract numbers from strings like "1,234 winners"
                match = re.search(r'([\d,]+)', str(row[winners_col]))
                if match:
                    winners_str = match.group(1).replace(',', '')
                    try:
                        winners = int(winners_str)
                    except ValueError:
                        pass
        
        # Format prize amount
        prize = ''
        if winnings_col in row.index and not pd.isna(row[winnings_col]):
            prize = str(row[winnings_col])
            # If it doesn't have currency symbol, add R
            if not any(symbol in prize for symbol in ['R', '$', '€']):
                # Try to parse as number first
                try:
                    amount = float(prize.replace(',', ''))
                    prize = f'R {amount:,.2f}'
                except ValueError:
                    prize = f'R {prize}'
        
        # Add to divisions dictionary
        divisions[f'Division {i}'] = {
            'description': desc,
            'winners': winners,
            'prize': prize
        }
    
    return divisions

def get_column_mapping(df):
    """
    Map standard column names to actual columns in the spreadsheet
    
    Args:
        df (pandas.DataFrame): Excel dataframe
        
    Returns:
        dict: Column mapping
    """
    mapping = {}
    
    # List of possible column names for each data type
    column_types = {
        'lottery_type': ['game name', 'game type', 'lottery type', 'lotto type', 'game', 'lottery'],
        'draw_number': ['draw number', 'draw no', 'draw', 'id', 'draw id'],
        'draw_date': ['draw date', 'date', 'game date'],
        'numbers': ['winning numbers', 'main numbers', 'numbers', 'winning balls', 'winning numbers (numerical)'],
        'bonus_ball': ['bonus ball', 'bonus number', 'powerball', 'power ball', 'additional number', 'extra ball', 'bonus']
    }
    
    # Actual column names in the dataframe
    df_columns = [str(col).lower() for col in df.columns]
    
    # Map each data type to an actual column
    for data_type, possible_names in column_types.items():
        for col_index, col_name in enumerate(df_columns):
            if any(possible in col_name for possible in possible_names):
                # Found a match
                mapping[data_type] = df.columns[col_index]
                break
    
    return mapping

def import_excel_data(excel_file, flask_app=None):
    """
    Simplified function to import lottery data from a single-sheet Excel file.
    This version works specifically with files that have all data in one sheet.
    
    Args:
        excel_file (str): Path to Excel file
        flask_app: Flask app object for context (optional)
        
    Returns:
        dict: Import statistics
    """
    # Initialize stats
    stats = {
        'imported': 0,
        'updated': 0,
        'errors': 0,
        'total_processed': 0,
        'by_lottery_type': {}
    }
    
    # List to collect imported records
    imported_records = []
    
    # Track history record ID
    last_import_history_id = None
    
    try:
        # Get app context
        ctx = None
        if flask_app:
            ctx = flask_app.app_context()
        else:
            try:
                ctx = current_app.app_context()
            except RuntimeError:
                logger.error("No Flask app context available")
                return {'success': False, 'error': 'No Flask app context available'}
        
        # Use app context
        with ctx:
            # Create import history record
            import_history = ImportHistory(
                import_type="excel",
                file_name=os.path.basename(excel_file),
                import_date=datetime.utcnow()
            )
            db.session.add(import_history)
            db.session.commit()
            
            last_import_history_id = import_history.id
            
            logger.info(f"Importing lottery data from: {excel_file}")
            
            # Get file size for logging
            try:
                filesize = os.path.getsize(excel_file)
                logger.info(f"Excel file size: {filesize} bytes")
            except (OSError, IOError) as e:
                logger.warning(f"Could not get file size: {str(e)}")
            
            # Try to read the Excel file
            excel_data = None
            
            # First try with openpyxl engine
            try:
                logger.info("Reading Excel with openpyxl engine")
                excel_data = pd.read_excel(excel_file, engine='openpyxl')
                
                # Check if we have multiple worksheets
                xl = pd.ExcelFile(excel_file, engine='openpyxl')
                sheets = xl.sheet_names
                
                # Look for a sheet with lottery data
                for sheet in sheets:
                    # Prefer sheets with "lottery", "lotto", "data", or "results" in name
                    if any(keyword in sheet.lower() for keyword in ['lottery', 'lotto', 'data', 'results']):
                        logger.info(f"Found sheet with lottery data: {sheet}")
                        excel_data = pd.read_excel(excel_file, sheet_name=sheet, engine='openpyxl')
                        logger.info(f"Successfully read '{sheet}' sheet with openpyxl engine")
                        break
                else:
                    # If no matching sheet found, use the first sheet
                    if sheets:
                        excel_data = pd.read_excel(excel_file, sheet_name=sheets[0], engine='openpyxl')
                        logger.info(f"Used first sheet: {sheets[0]}")
                
            except Exception as e:
                logger.error(f"Error with openpyxl engine: {str(e)}")
                
                # Fallback to xlrd engine for older Excel files
                try:
                    logger.info("Falling back to xlrd engine")
                    excel_data = pd.read_excel(excel_file, engine='xlrd')
                    logger.info("Successfully read Excel with xlrd engine")
                except Exception as e:
                    logger.error(f"Error with xlrd engine: {str(e)}")
                    
                    # If all engines failed, return error
                    import_history.errors = 1
                    db.session.commit()
                    return {'success': False, 'error': f"Failed to read Excel file: {str(e)}"}
            
            # Replace NaN values with None for cleaner processing
            excel_data = excel_data.replace({np.nan: None})
            
            # Log column headers for debugging
            logger.info(f"Excel columns: {', '.join(str(col) for col in excel_data.columns)}")
            
            # Get column mapping
            column_mapping = get_column_mapping(excel_data)
            logger.info(f"Column mapping: {column_mapping}")
            
            # Check if we found essential columns
            if 'lottery_type' not in column_mapping or 'draw_number' not in column_mapping:
                error_msg = "Could not find essential columns (Game Name and Draw Number)"
                logger.error(error_msg)
                import_history.errors = 1
                db.session.commit()
                return {'success': False, 'error': error_msg}
            
            # Process each row in the dataframe
            for index, row in excel_data.iterrows():
                # Skip header-like rows (containing column names)
                column_value_matches = 0
                for col in excel_data.columns:
                    if row[col] == col:
                        column_value_matches += 1
                
                # If more than half the values match column names, it's likely a header row
                if column_value_matches > len(excel_data.columns) / 2:
                    logger.info(f"Skipping header-like row at index {index}")
                    continue
                
                # Skip rows with placeholder or example data
                lottery_type_col = column_mapping['lottery_type']
                if row[lottery_type_col] is None or (isinstance(row[lottery_type_col], str) and 
                                                    ('example' in row[lottery_type_col].lower() or 
                                                    row[lottery_type_col].strip() == '')):
                    logger.info(f"Skipping example/empty row at index {index}")
                    continue
                
                try:
                    stats['total_processed'] += 1
                    
                    # Extract and process lottery type
                    raw_lottery_type = row[column_mapping['lottery_type']]
                    lottery_type = standardize_lottery_type(raw_lottery_type)
                    
                    if not lottery_type:
                        logger.warning(f"Could not determine lottery type for row {index}")
                        stats['errors'] += 1
                        continue
                    
                    # Extract and process draw number
                    raw_draw_number = row[column_mapping['draw_number']]
                    if raw_draw_number is None:
                        logger.warning(f"Missing draw number for row {index}")
                        stats['errors'] += 1
                        continue
                    
                    draw_number = str(raw_draw_number).strip()
                    
                    # Extract and process draw date
                    raw_draw_date = None
                    if 'draw_date' in column_mapping:
                        raw_draw_date = row[column_mapping['draw_date']]
                    
                    draw_date = parse_excel_date(raw_draw_date)
                    if not draw_date:
                        logger.warning(f"Could not parse draw date for {lottery_type} draw {draw_number}")
                        # Default to current date if missing
                        draw_date = datetime.utcnow()
                    
                    # Extract and process winning numbers
                    winning_numbers = []
                    if 'numbers' in column_mapping:
                        raw_numbers = row[column_mapping['numbers']]
                        winning_numbers = parse_numbers(raw_numbers)
                    
                    if not winning_numbers:
                        logger.warning(f"Could not parse winning numbers for {lottery_type} draw {draw_number}")
                        stats['errors'] += 1
                        continue
                    
                    # Extract and process bonus numbers
                    bonus_numbers = []
                    if 'bonus_ball' in column_mapping:
                        raw_bonus = row[column_mapping['bonus_ball']]
                        if raw_bonus is not None:
                            bonus_numbers = parse_numbers(raw_bonus)
                    
                    # Parse division data
                    divisions = parse_divisions(row)
                    
                    # Check if this draw already exists in the database
                    existing_result = LotteryResult.query.filter_by(
                        lottery_type=lottery_type,
                        draw_number=draw_number
                    ).first()
                    
                    lottery_result = None
                    
                    if existing_result:
                        # Update existing record
                        existing_result.draw_date = draw_date
                        existing_result.numbers = json.dumps(winning_numbers)
                        existing_result.bonus_numbers = json.dumps(bonus_numbers)
                        existing_result.divisions = json.dumps(divisions)
                        existing_result.source_url = excel_file
                        
                        db.session.commit()
                        stats['updated'] += 1
                        logger.info(f"Updated {lottery_type} draw {draw_number}")
                        lottery_result = existing_result
                    else:
                        # Create new record
                        new_result = LotteryResult(
                            lottery_type=lottery_type,
                            draw_number=draw_number,
                            draw_date=draw_date,
                            numbers=json.dumps(winning_numbers),
                            bonus_numbers=json.dumps(bonus_numbers),
                            divisions=json.dumps(divisions),
                            source_url=excel_file,
                            created_at=datetime.utcnow()
                        )
                        
                        db.session.add(new_result)
                        db.session.commit()
                        stats['imported'] += 1
                        logger.info(f"Imported new {lottery_type} draw {draw_number}")
                        lottery_result = new_result
                    
                    # Update lottery type statistics
                    if lottery_type not in stats['by_lottery_type']:
                        stats['by_lottery_type'][lottery_type] = 0
                    stats['by_lottery_type'][lottery_type] += 1
                
                except Exception as e:
                    error_detail = traceback.format_exc()
                    logger.error(f"Error processing row {index}: {str(e)}\n{error_detail}")
                    stats['errors'] += 1
            
            # Update import history with results
            import_history.records_added = stats['imported']
            import_history.records_updated = stats['updated']
            import_history.errors = stats['errors']
            import_history.total_processed = stats['total_processed']
            
            db.session.commit()
            
            logger.info(f"Import completed. Stats: {stats}")
            return {'success': True, 'stats': stats}
    
    except Exception as e:
        error_detail = traceback.format_exc()
        logger.error(f"General error during import: {str(e)}\n{error_detail}")
        
        # Update import history with error if possible
        if last_import_history_id:
            try:
                # Get the app context
                if flask_app:
                    ctx = flask_app.app_context()
                else:
                    ctx = current_app.app_context()
                    
                with ctx:
                    import_history = ImportHistory.query.get(last_import_history_id)
                    if import_history:
                        import_history.errors = 1
                        db.session.commit()
            except Exception:
                pass
        
        return {'success': False, 'error': f'General error during import: {str(e)}'}

# For direct script execution
if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        excel_path = sys.argv[1]
    else:
        excel_path = "attached_assets/lottery_data_template_20250430_011720.xlsx"
    
    try:
        # Use a local app context for testing
        from app import app
        result = import_excel_data(excel_path, app)
        print(json.dumps(result, indent=2))
    except Exception as e:
        print(f"Error: {str(e)}")
        traceback.print_exc()