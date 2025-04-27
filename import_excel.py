import pandas as pd
import numpy as np
import json
import logging
from datetime import datetime
from flask import current_app
from models import LotteryResult, ImportHistory, ImportedRecord
from sqlalchemy import desc
from sqlalchemy.exc import SQLAlchemyError
from datetime import datetime, timedelta
import os
import re
import traceback
from excel_date_utils import parse_excel_date

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

def parse_divisions(divisions_data):
    """
    Parse divisions data from various formats to a structured dictionary.
    
    Args:
        divisions_data (dict): Dictionary of raw division data
        
    Returns:
        dict: Structured divisions dictionary
    """
    if not divisions_data:
        return {}
        
    divisions = {}
    
    # First check if we have division-like keys
    division_pattern = re.compile(r'(division|div)\s*(\d+)', re.IGNORECASE)
    
    # Process each key in the divisions data
    for key, value in divisions_data.items():
        if not key or pd.isna(key):
            continue
            
        # Check if this key relates to a division
        match = division_pattern.search(str(key))
        if match:
            # This is a division key, extract the division number
            division_num = match.group(2)
            division_key = f"Division {division_num}"
            
            # Check if this is a winners or prize key
            if 'winner' in str(key).lower():
                if division_key not in divisions:
                    divisions[division_key] = {}
                divisions[division_key]['winners'] = value
            elif any(prize_term in str(key).lower() for prize_term in ['prize', 'payout', 'winnings']):
                if division_key not in divisions:
                    divisions[division_key] = {}
                
                # Format prize value
                if isinstance(value, str):
                    if not value.startswith("R"):
                        prize_value = f"R{value}"
                    else:
                        prize_value = value
                else:
                    prize_value = f"R{value}"
                    
                divisions[division_key]['prize'] = prize_value
    
    return divisions

def import_excel_data(excel_file, flask_app=None):
    """
    Import lottery data from Excel spreadsheet with enhanced error handling.
    Prioritizes "Lottery" terminology over "Lotto" in all processing.
    
    Args:
        excel_file (str): Path to Excel file
        flask_app: Flask app object for context (optional)
    """
    # Initialize counters
    imported_count = 0
    updated_count = 0
    error_count = 0
    imported_records = []
    last_import_history_id = None
    
    try:
        # Use current_app or provided app
        ctx = flask_app.app_context() if flask_app else current_app.app_context()
        
        with ctx:
            logger.info(f"Starting import from {excel_file}")
            
            # Log file information for debugging
            file_size = os.path.getsize(excel_file)
            logger.info(f"Excel file size: {file_size} bytes")
            
            # Try different engines for maximum compatibility
            read_success = False
            error_messages = []
            
            # Try with openpyxl engine first
            try:
                logger.info("Reading Excel with openpyxl engine")
                df = pd.read_excel(excel_file, engine="openpyxl")
                read_success = True
                logger.info("Successfully read with openpyxl engine")
            except Exception as e:
                error_msg = f"Error with openpyxl engine: {str(e)}"
                logger.warning(error_msg)
                error_messages.append(error_msg)
            
            # If openpyxl failed, try xlrd engine
            if not read_success:
                try:
                    logger.info("Reading Excel with xlrd engine")
                    df = pd.read_excel(excel_file, engine="xlrd")
                    read_success = True
                    logger.info("Successfully read with xlrd engine")
                except Exception as e:
                    error_msg = f"Error with xlrd engine: {str(e)}"
                    logger.warning(error_msg)
                    error_messages.append(error_msg)
            
            # Last resort: try default engine
            if not read_success:
                try:
                    logger.info("Reading Excel with default engine")
                    df = pd.read_excel(excel_file)
                    read_success = True
                    logger.info("Successfully read with default engine")
                except Exception as e:
                    error_msg = f"Error with default engine: {str(e)}"
                    logger.error(error_msg)
                    error_messages.append(error_msg)
                    # All engines failed, create ImportHistory entry with error
                    import_history = ImportHistory(
                        filename=os.path.basename(excel_file),
                        timestamp=datetime.utcnow(),
                        status="error",
                        notes=f"Failed to read Excel file: {'; '.join(error_messages)}"
                    )
                    db.session.add(import_history)
                    db.session.commit()
                    return False
            
            # Replace NaN values with None for cleaner processing
            df = df.replace({np.nan: None})
            
            # Log column headers for debugging
            logger.info(f"Excel columns: {', '.join(str(col) for col in df.columns)}")
            
            # Create import history record
            import_history = ImportHistory(
                filename=os.path.basename(excel_file),
                timestamp=datetime.utcnow(),
                status="processing"
            )
            db.session.add(import_history)
            db.session.commit()
            last_import_history_id = import_history.id
            
            # Map standard column names to actual columns in the spreadsheet
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
                
                # Check for division data columns
                for i in range(1, 9):  # Assuming up to 8 divisions
                    # Check for different division column formats
                    div_winners_patterns = [
                        f'div {i} winners', 
                        f'division {i} winners',
                        f'div{i} winners'
                    ]
                    
                    div_prize_patterns = [
                        f'div {i} prize',
                        f'div {i} payout',
                        f'div {i} winning',
                        f'division {i} prize',
                        f'division {i} payout'
                    ]
                    
                    if any(pattern in col_lower for pattern in div_winners_patterns):
                        column_mapping[f'div{i}_winners'] = col
                    
                    if any(pattern in col_lower for pattern in div_prize_patterns):
                        column_mapping[f'div{i}_prize'] = col
            
            # Log the column mapping for debugging
            logger.info(f"Column mapping: {column_mapping}")
            
            # Check if we found essential columns
            if 'lottery_type' not in column_mapping or 'draw_number' not in column_mapping:
                logger.error("Could not find essential columns for lottery data import")
                import_history.status = "error"
                import_history.notes = "Could not find essential columns (Game Name and Draw Number)"
                db.session.commit()
                return False
            
            # Process each row in the dataframe
            for index, row in df.iterrows():
                # Skip header-like rows (containing column names)
                column_value_matches = 0
                for col in df.columns:
                    if row[col] == col:
                        column_value_matches += 1
                
                # If more than half the values match column names, it's likely a header row
                if column_value_matches > len(df.columns) / 2:
                    logger.info(f"Skipping header-like row at index {index}")
                    continue
                
                try:
                    # Extract data from row using the column mapping
                    raw_lottery_type = row[column_mapping['lottery_type']] if 'lottery_type' in column_mapping and column_mapping['lottery_type'] in row else None
                    raw_draw_number = row[column_mapping['draw_number']] if 'draw_number' in column_mapping and column_mapping['draw_number'] in row else None
                    raw_draw_date = row[column_mapping['draw_date']] if 'draw_date' in column_mapping and column_mapping['draw_date'] in row else None
                    raw_numbers = row[column_mapping['numbers']] if 'numbers' in column_mapping and column_mapping['numbers'] in row else None
                    raw_bonus_ball = row[column_mapping['bonus_ball']] if 'bonus_ball' in column_mapping and column_mapping['bonus_ball'] in row else None
                    
                    # Skip rows with missing essential data
                    if not raw_lottery_type or pd.isna(raw_lottery_type) or not raw_draw_number or pd.isna(raw_draw_number):
                        continue
                    
                    # Standardize lottery type
                    lottery_type = standardize_lottery_type(raw_lottery_type)
                    
                    # Format draw number as string
                    if isinstance(raw_draw_number, (int, float)):
                        draw_number = str(int(raw_draw_number))
                    else:
                        draw_number = str(raw_draw_number).strip()
                    
                    # Parse draw date
                    draw_date = parse_excel_date(raw_draw_date)
                    if not draw_date:
                        logger.warning(f"Could not parse draw date: {raw_draw_date}")
                        draw_date = datetime.utcnow()
                    
                    # Parse numbers
                    numbers = parse_numbers(raw_numbers)
                    
                    # Parse bonus numbers
                    if raw_bonus_ball and not pd.isna(raw_bonus_ball):
                        # For numeric values
                        if isinstance(raw_bonus_ball, (int, float)):
                            bonus_numbers = [int(raw_bonus_ball)]
                        # For string values
                        elif isinstance(raw_bonus_ball, str):
                            bonus_numbers = parse_numbers(raw_bonus_ball)
                        else:
                            bonus_numbers = []
                    else:
                        bonus_numbers = []
                    
                    # Parse division data
                    divisions = {}
                    for i in range(1, 9):  # Assuming up to 8 divisions
                        winners_key = f'div{i}_winners'
                        prize_key = f'div{i}_prize'
                        
                        if winners_key in column_mapping and prize_key in column_mapping:
                            winners_col = column_mapping[winners_key]
                            prize_col = column_mapping[prize_key]
                            
                            raw_winners = row[winners_col] if winners_col in row else None
                            raw_prize = row[prize_col] if prize_col in row else None
                            
                            if raw_winners is not None and not pd.isna(raw_winners) and raw_prize is not None and not pd.isna(raw_prize):
                                # Format winners value
                                if isinstance(raw_winners, (int, float)):
                                    winners_value = str(int(raw_winners))
                                else:
                                    winners_value = str(raw_winners)
                                
                                # Format prize value
                                if isinstance(raw_prize, str):
                                    if not raw_prize.startswith("R"):
                                        prize_value = f"R{raw_prize}"
                                    else:
                                        prize_value = raw_prize
                                else:
                                    prize_value = f"R{raw_prize}"
                                
                                divisions[f"Division {i}"] = {
                                    "winners": winners_value,
                                    "prize": prize_value
                                }
                    
                    # Verify we have valid data
                    if lottery_type and draw_number and numbers:
                        # Check if result already exists in the database
                        existing_result = LotteryResult.query.filter_by(
                            lottery_type=lottery_type,
                            draw_number=draw_number
                        ).first()
                        
                        # Create JSON strings for database storage
                        numbers_json = json.dumps(numbers)
                        bonus_numbers_json = json.dumps(bonus_numbers) if bonus_numbers else None
                        divisions_json = json.dumps(divisions) if divisions else None
                        
                        # Log what we're doing for debugging
                        if existing_result:
                            logger.info(f"Updating existing result: {lottery_type} Draw {draw_number}")
                            
                            # Update existing record
                            existing_result.draw_date = draw_date
                            existing_result.numbers = numbers_json
                            existing_result.bonus_numbers = bonus_numbers_json
                            existing_result.divisions = divisions_json
                            existing_result.source_url = "imported-from-excel"
                            existing_result.ocr_provider = "manual-import"
                            existing_result.ocr_model = "excel-spreadsheet"
                            existing_result.ocr_timestamp = datetime.utcnow().isoformat()
                            
                            db.session.commit()
                            updated_count += 1
                            
                            # Track imported record
                            imported_records.append({
                                'lottery_type': lottery_type,
                                'draw_number': draw_number,
                                'draw_date': draw_date,
                                'is_new': False,
                                'lottery_result_id': existing_result.id
                            })
                        else:
                            logger.info(f"Creating new result: {lottery_type} Draw {draw_number}")
                            
                            # Create new result
                            new_result = LotteryResult(
                                lottery_type=lottery_type,
                                draw_number=draw_number,
                                draw_date=draw_date,
                                numbers=numbers_json,
                                bonus_numbers=bonus_numbers_json,
                                divisions=divisions_json,
                                source_url="imported-from-excel",
                                ocr_provider="manual-import",
                                ocr_model="excel-spreadsheet",
                                ocr_timestamp=datetime.utcnow().isoformat()
                            )
                            
                            db.session.add(new_result)
                            db.session.commit()
                            imported_count += 1
                            
                            # Track imported record
                            imported_records.append({
                                'lottery_type': lottery_type,
                                'draw_number': draw_number,
                                'draw_date': draw_date,
                                'is_new': True,
                                'lottery_result_id': new_result.id
                            })
                    else:
                        logger.warning(f"Skipping row {index} due to missing essential data")
                        error_count += 1
                except Exception as row_error:
                    logger.error(f"Error processing row {index}: {str(row_error)}")
                    error_count += 1
            
            # Update import history with results
            if last_import_history_id:
                import_history = ImportHistory.query.get(last_import_history_id)
                if import_history:
                    import_history.status = "completed"
                    import_history.imported_count = imported_count
                    import_history.updated_count = updated_count
                    import_history.error_count = error_count
                    import_history.notes = f"Imported {imported_count} new records, updated {updated_count} existing records, {error_count} errors"
                    db.session.commit()
                    
                    # Create ImportedRecord entries for each imported record
                    for record in imported_records:
                        imported_record = ImportedRecord(
                            import_history_id=import_history.id,
                            lottery_type=record['lottery_type'],
                            draw_number=record['draw_number'],
                            draw_date=record['draw_date'],
                            is_new=record['is_new'],
                            lottery_result_id=record['lottery_result_id']
                        )
                        db.session.add(imported_record)
                    
                    db.session.commit()
            
            logger.info(f"Import completed: {imported_count} imported, {updated_count} updated, {error_count} errors")
            return imported_count + updated_count > 0
            
    except Exception as e:
        logger.error(f"Error importing Excel data: {str(e)}")
        logger.error(traceback.format_exc())
        
        # Update import history with error if it exists
        if last_import_history_id:
            try:
                import_history = ImportHistory.query.get(last_import_history_id)
                if import_history:
                    import_history.status = "error"
                    import_history.notes = f"Error during import: {str(e)}"
                    db.session.commit()
            except Exception as db_error:
                logger.error(f"Could not update import history: {str(db_error)}")
        
        return False

def create_empty_template(output_path):
    """
    Create a properly formatted Excel template for lottery data import with an empty worksheet.
    
    Args:
        output_path (str): Path to save the Excel file
        
    Returns:
        bool: Success status
    """
    # Create Excel writer
    writer = pd.ExcelWriter(output_path, engine='openpyxl')
    
    # Create empty DataFrames for each lottery type - using "Lottery" terminology
    lottery_types = [
        'Lottery',
        'Lottery Plus 1',
        'Lottery Plus 2',
        'Powerball',
        'Powerball Plus',
        'Daily Lottery'
    ]
    
    # Create columns that match our expected format
    columns = [
        'Game Name',
        'Draw Number',
        'Draw Date',
        'Winning Numbers',
        'Bonus Ball',
        'Division 1 Winners',
        'Division 1 Payout',
        'Division 2 Winners',
        'Division 2 Payout',
        'Division 3 Winners',
        'Division 3 Payout',
        'Division 4 Winners',
        'Division 4 Payout',
        'Division 5 Winners',
        'Division 5 Payout',
        'Next Draw Date',
        'Next Draw Jackpot'
    ]
    
    # Create empty DataFrames for each lottery type with the columns
    for lottery_type in lottery_types:
        # Create an empty DataFrame with our columns
        df = pd.DataFrame(columns=columns)
        
        # Add a couple of example rows to show the format
        example_data = {
            'Game Name': lottery_type,
            'Draw Number': f'Example: 1234',
            'Draw Date': 'YYYY-MM-DD',
            'Winning Numbers': 'Example: 1, 2, 3, 4, 5, 6',
            'Bonus Ball': 'Example: 7',
            'Division 1 Winners': 'Example: 1',
            'Division 1 Payout': 'Example: R5,000,000.00',
            'Division 2 Winners': 'Example: 5',
            'Division 2 Payout': 'Example: R250,000.00',
        }
        df = pd.concat([df, pd.DataFrame([example_data])], ignore_index=True)
        
        # Write to Excel
        df.to_excel(writer, sheet_name=lottery_type, index=False)
    
    # Create a main sheet with instructions
    instructions = pd.DataFrame({
        'Instructions': [
            'LOTTERY DATA IMPORT TEMPLATE',
            '',
            'HOW TO USE THIS TEMPLATE:',
            '1. Each sheet represents a different lottery game',
            '2. Fill in the actual draw information on each sheet',
            '3. Save the file',
            '4. Upload through the Import Data page',
            '',
            'REQUIRED FIELDS:',
            '- Game Name: The name of the lottery game',
            '- Draw Number: The official draw number',
            '- Draw Date: The date of the draw (YYYY-MM-DD format)',
            '- Winning Numbers: Comma-separated list of winning numbers',
            '',
            'OPTIONAL FIELDS:',
            '- Bonus Ball: The bonus ball for games that have one',
            '- Division X Winners: Number of winners in each division',
            '- Division X Payout: Prize amount for each division',
            '- Next Draw Date: Date of the next scheduled draw',
            '- Next Draw Jackpot: Estimated jackpot for the next draw',
        ]
    })
    
    instructions.to_excel(writer, sheet_name='Instructions', index=False)
    
    # Save the Excel file
    writer.close()
    
    return os.path.exists(output_path)

from main import db  # Import at end to avoid circular import

# If run directly, perform a test import
if __name__ == "__main__":
    from main import app
    # Find the most recent Excel file
    excel_files = []
    for root, dirs, files in os.walk("uploads"):
        for filename in files:
            if filename.endswith(".xlsx"):
                excel_files.append(os.path.join(root, filename))
    
    if excel_files:
        newest_file = max(excel_files, key=os.path.getmtime)
        print(f"Importing from: {newest_file}")
        import_excel_data(newest_file, app)
    else:
        print("No Excel files found in uploads directory.")