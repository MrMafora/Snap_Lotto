"""
Simplified Excel Import Module for Snap Lotto
Designed to work with single-sheet Excel files containing all lottery data
"""

import pandas as pd
import numpy as np
import json
import logging
from datetime import datetime
import os
import re
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

def parse_excel_date(date_value):
    """
    Parse Excel date value into Python datetime.
    
    Args:
        date_value: Date value from Excel (can be string, datetime, or integer)
        
    Returns:
        datetime: Parsed datetime object or None if parsing fails
    """
    if pd.isna(date_value):
        return None
        
    # If already a datetime, return as is
    if isinstance(date_value, datetime):
        return date_value
        
    # Handle string date formats
    if isinstance(date_value, str):
        date_str = date_value.strip()
        
        # Skip placeholder dates
        if date_str in ['YYYY-MM-DD', 'Example: 2023-01-01']:
            return None
            
        # Try different date formats
        date_formats = [
            '%Y-%m-%d',           # 2023-01-31
            '%d/%m/%Y',           # 31/01/2023
            '%m/%d/%Y',           # 01/31/2023
            '%d-%m-%Y',           # 31-01-2023
            '%d %b %Y',           # 31 Jan 2023
            '%d %B %Y',           # 31 January 2023
            '%B %d, %Y',          # January 31, 2023
            '%Y/%m/%d',           # 2023/01/31
        ]
        
        for date_format in date_formats:
            try:
                return datetime.strptime(date_str, date_format)
            except ValueError:
                continue
                
    # Handle numeric date (Excel serial date)
    if isinstance(date_value, (int, float)):
        try:
            # Excel dates start from 1900-01-01, which is day 1
            # Convert to Python datetime (library handles this conversion)
            return pd.to_datetime(date_value, unit='D', origin='1899-12-30')
        except Exception:
            pass
            
    logger.warning(f"Could not parse date: {date_value}")
    return None

def parse_numbers(numbers_str):
    """
    Parse lottery numbers from string format to list of integers.
    
    Args:
        numbers_str (str): String representation of numbers
        
    Returns:
        list: List of numbers as integers
    """
    if pd.isna(numbers_str) or not numbers_str:
        return []
        
    # If already a list of integers, return as is
    if isinstance(numbers_str, list):
        return numbers_str
        
    # Handle different formats of number strings
    if isinstance(numbers_str, str):
        # Remove any prefix like "Example:"
        numbers_str = numbers_str.replace('Example:', '').strip()
        
        # Handle comma-separated format: "1, 2, 3, 4, 5, 6"
        if ',' in numbers_str:
            return [int(n.strip()) for n in numbers_str.split(',') if n.strip().isdigit()]
            
        # Handle space-separated format: "1 2 3 4 5 6"
        return [int(n.strip()) for n in numbers_str.split() if n.strip().isdigit()]
        
    # Default empty list if we can't parse
    return []

def parse_divisions(row):
    """
    Parse division data from Excel row.
    
    Args:
        row (pandas.Series): Row data from Excel
        
    Returns:
        dict: Division data with winners and prizes
    """
    divisions = {}
    
    # Look for division information in various column naming formats
    for i in range(1, 9):  # Support up to 8 divisions
        # Define common prefixes and column patterns
        prefixes = [
            f'Division {i}',
            f'Div {i}',
            f'Div{i}',
            f'Division{i}'
        ]
        
        # Search for matching columns with these prefixes
        for prefix in prefixes:
            found_data = False
            
            # Try various suffix combinations
            for winners_suffix in [' Winners', ' Winner', ' Wnrs', 'Winners', 'Winner', 'Wnrs']:
                for payout_suffix in [' Payout', ' Prize', ' Winnings', 'Payout', 'Prize', 'Winnings']:
                    winners_key = f"{prefix}{winners_suffix}"
                    payout_key = f"{prefix}{payout_suffix}"
                    
                    # Case-insensitive column lookup
                    winners_col = next((col for col in row.index if col.lower() == winners_key.lower()), None)
                    payout_col = next((col for col in row.index if col.lower() == payout_key.lower()), None)
                    
                    if winners_col is not None or payout_col is not None:
                        division_key = f"div{i}"
                        divisions[division_key] = {
                            'winners': '0',
                            'prize': 'R0.00'
                        }
                        
                        # Process winners
                        if winners_col is not None:
                            winners = row.get(winners_col)
                            if winners is not None and not pd.isna(winners):
                                if isinstance(winners, str):
                                    # Clean up the string
                                    winners = winners.replace('Example:', '').strip()
                                    winners_value = re.sub(r'[^\d]', '', winners)
                                    if winners_value.isdigit():
                                        divisions[division_key]['winners'] = str(int(winners_value))
                                elif isinstance(winners, (int, float)):
                                    divisions[division_key]['winners'] = str(int(winners))
                        
                        # Process payouts
                        if payout_col is not None:
                            payout = row.get(payout_col)
                            if payout is not None and not pd.isna(payout):
                                if isinstance(payout, str):
                                    # Clean up the string
                                    payout = payout.replace('Example:', '').strip()
                                    # Add R prefix if missing
                                    if not payout.startswith('R'):
                                        payout = f'R{payout}'
                                    divisions[division_key]['prize'] = payout
                                elif isinstance(payout, (int, float)):
                                    divisions[division_key]['prize'] = f'R{payout:,.2f}'
                        
                        found_data = True
                        break
                
                if found_data:
                    break
    
    return divisions

def get_column_mapping(df):
    """
    Map standard column names to actual columns in the spreadsheet
    
    Args:
        df (pandas.DataFrame): Excel dataframe
        
    Returns:
        dict: Column mapping
    """
    column_mapping = {}
    
    # Check for common column name patterns
    game_name_variants = ['game name', 'game type', 'lottery type', 'lottery game', 'lottery', 'lotto type', 'lotto game', 'lotto']
    draw_number_variants = ['draw number', 'draw no', 'draw id', 'number']
    draw_date_variants = ['draw date', 'game date', 'date']
    numbers_variants = ['winning numbers', 'main numbers', 'numbers']
    bonus_variants = ['bonus ball', 'bonus number', 'powerball']
    
    for col in df.columns:
        col_str = str(col)
        col_lower = col_str.lower()
        
        # Map standard fields to actual column names
        if any(variant in col_lower for variant in game_name_variants):
            column_mapping['lottery_type'] = col
        
        # Special case for "Game Name" which is the most common in our templates
        if col_str == "Game Name":
            column_mapping['lottery_type'] = col
        
        if any(variant in col_lower for variant in draw_number_variants):
            column_mapping['draw_number'] = col
        
        if any(variant in col_lower for variant in draw_date_variants):
            column_mapping['draw_date'] = col
        
        if any(variant in col_lower for variant in numbers_variants) or 'numerical' in col_lower:
            column_mapping['numbers'] = col
        
        if any(variant in col_lower for variant in bonus_variants):
            column_mapping['bonus_ball'] = col
    
    return column_mapping

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
    logger.info(f"Importing lottery data from: {excel_file}")
    
    # Initialize counters
    stats = {
        'total_processed': 0,
        'imported': 0,
        'updated': 0,
        'errors': 0,
        'by_lottery_type': {}
    }
    
    imported_records = []
    last_import_history_id = None
    
    try:
        # Use current_app or provided app
        ctx = flask_app.app_context() if flask_app else current_app.app_context()
        
        with ctx:
            # Log file information for debugging
            file_size = os.path.getsize(excel_file)
            logger.info(f"Excel file size: {file_size} bytes")
            
            # Create import history record
            import_history = ImportHistory(
                filename=os.path.basename(excel_file),
                timestamp=datetime.utcnow(),
                status="processing"
            )
            db.session.add(import_history)
            db.session.commit()
            last_import_history_id = import_history.id
            
            # Try different engines for maximum compatibility
            excel_data = None
            error_messages = []
            
            # Try with openpyxl engine first
            try:
                logger.info("Reading Excel with openpyxl engine")
                xls = pd.ExcelFile(excel_file, engine="openpyxl")
                
                # Check if 'Lottery' sheet exists (single-sheet approach)
                if 'Lottery' in xls.sheet_names:
                    excel_data = pd.read_excel(excel_file, sheet_name='Lottery', engine="openpyxl")
                    logger.info(f"Successfully read 'Lottery' sheet with openpyxl engine")
                else:
                    # Try first sheet in the file
                    sheet_name = xls.sheet_names[0]
                    excel_data = pd.read_excel(excel_file, sheet_name=sheet_name, engine="openpyxl")
                    logger.info(f"Successfully read '{sheet_name}' sheet with openpyxl engine")
            except Exception as e:
                error_msg = f"Error with openpyxl engine: {str(e)}"
                logger.warning(error_msg)
                error_messages.append(error_msg)
            
            # If openpyxl failed, try xlrd engine
            if excel_data is None:
                try:
                    logger.info("Reading Excel with xlrd engine")
                    xls = pd.ExcelFile(excel_file, engine="xlrd")
                    
                    # Check for 'Lottery' sheet
                    if 'Lottery' in xls.sheet_names:
                        excel_data = pd.read_excel(excel_file, sheet_name='Lottery', engine="xlrd")
                        logger.info(f"Successfully read 'Lottery' sheet with xlrd engine")
                    else:
                        # Try first sheet
                        sheet_name = xls.sheet_names[0]
                        excel_data = pd.read_excel(excel_file, sheet_name=sheet_name, engine="xlrd")
                        logger.info(f"Successfully read '{sheet_name}' sheet with xlrd engine")
                except Exception as e:
                    error_msg = f"Error with xlrd engine: {str(e)}"
                    logger.warning(error_msg)
                    error_messages.append(error_msg)
            
            # Last resort: try default engine
            if excel_data is None:
                try:
                    logger.info("Reading Excel with default engine")
                    excel_data = pd.read_excel(excel_file)
                    logger.info("Successfully read with default engine")
                except Exception as e:
                    error_msg = f"Error with default engine: {str(e)}"
                    logger.error(error_msg)
                    error_messages.append(error_msg)
                    
                    # All engines failed, update ImportHistory entry with error
                    import_history.status = "error"
                    import_history.notes = f"Failed to read Excel file: {'; '.join(error_messages)}"
                    db.session.commit()
                    return {'success': False, 'error': f"Failed to read Excel file: {'; '.join(error_messages)}"}
            
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
                import_history.status = "error"
                import_history.notes = error_msg
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
                        stats['errors'] += 1
                        continue
                    
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
                    
                    # Track imported record
                    imported_record = ImportedRecord(
                        import_history_id=import_history.id,
                        lottery_type=lottery_type,
                        draw_number=draw_number,
                        draw_date=draw_date,
                        status="success"
                    )
                    imported_records.append(imported_record)
                    
                    # Update lottery type statistics
                    if lottery_type not in stats['by_lottery_type']:
                        stats['by_lottery_type'][lottery_type] = 0
                    stats['by_lottery_type'][lottery_type] += 1
                
                except Exception as e:
                    error_detail = traceback.format_exc()
                    logger.error(f"Error processing row {index}: {str(e)}\n{error_detail}")
                    stats['errors'] += 1
                    
                    # Track failed record if we have enough information
                    lottery_type = lottery_type if 'lottery_type' in locals() else 'Unknown'
                    draw_number = draw_number if 'draw_number' in locals() else 'Unknown'
                    draw_date = draw_date if 'draw_date' in locals() else None
                    
                    failed_record = ImportedRecord(
                        import_history_id=import_history.id,
                        lottery_type=lottery_type,
                        draw_number=draw_number,
                        draw_date=draw_date,
                        status="error",
                        error_details=str(e)
                    )
                    imported_records.append(failed_record)
            
            # Bulk add all imported records
            db.session.add_all(imported_records)
            
            # Update import history with results
            import_history.status = "completed"
            import_history.import_count = stats['imported']
            import_history.update_count = stats['updated']
            import_history.error_count = stats['errors']
            import_history.notes = f"Processed {stats['total_processed']} records"
            
            db.session.commit()
            
            logger.info(f"Import completed. Stats: {stats}")
            return {'success': True, 'stats': stats}
    
    except Exception as e:
        error_detail = traceback.format_exc()
        logger.error(f"General error during import: {str(e)}\n{error_detail}")
        
        # Update import history with error if possible
        if last_import_history_id:
            try:
                with ctx:
                    import_history = ImportHistory.query.get(last_import_history_id)
                    if import_history:
                        import_history.status = "error"
                        import_history.notes = f"General error: {str(e)}"
                        db.session.commit()
            except Exception:
                pass
        
        return {'success': False, 'error': f'General error during import: {str(e)}'}

# For direct script execution
if __name__ == "__main__":
    import sys
    import traceback
    
    if len(sys.argv) > 1:
        excel_path = sys.argv[1]
    else:
        excel_path = "attached_assets/lottery_data_template_20250429_020457.xlsx"
    
    try:
        # Use a local app context for testing
        from app import app
        result = import_excel_data(excel_path, app)
        print(json.dumps(result, indent=2))
    except Exception as e:
        print(f"Error: {str(e)}")
        traceback.print_exc()