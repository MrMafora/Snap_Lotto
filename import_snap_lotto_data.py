#!/usr/bin/env python
"""
Script to import South African lottery data from the specific Snap_lotto
True Numbers and results Excel file.
"""

import os
import sys
import logging
import json
import pandas as pd
from datetime import datetime, timedelta
from models import db, LotteryResult, Screenshot

# Set up logging
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def parse_date(date_str):
    """Parse date from string format to datetime object"""
    try:
        # Use our dedicated date parsing module
        from excel_date_utils import parse_excel_date
        
        # Handle NaN values
        if date_str is None or pd.isna(date_str):
            return None
            
        # Use the utility function for consistent date parsing
        result = parse_excel_date(date_str)
        
        # Log the result for debugging
        logger.info(f"Using excel_date_utils to parse '{date_str}' → {result}")
        
        return result
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
            # If numbers are comma-separated
            if ',' in numbers_str:
                numbers = [int(num.strip()) for num in numbers_str.split(',') if num.strip().isdigit()]
                if numbers:
                    return numbers
                    
            # If numbers are space-separated or have other delimiters
            clean_str = ''.join(c if c.isdigit() or c.isspace() else ' ' for c in numbers_str)
            numbers = [int(num) for num in clean_str.split() if num.strip().isdigit()]
            return numbers
        elif isinstance(numbers_str, (int, float)):
            # Single number
            return [int(numbers_str)]
        else:
            return []
    except Exception as e:
        logger.error(f"Error parsing numbers {numbers_str}: {str(e)}")
        return []

def get_lottery_type(game_name):
    """Map game name to standardized lottery type"""
    if pd.isna(game_name):
        return ""
        
    game_str = str(game_name).strip().upper()
    
    if game_str == "LOTTO":
        return "Lotto"
    elif game_str == "LOTTO PLUS 1":
        return "Lotto Plus 1"
    elif game_str == "LOTTO PLUS 2":
        return "Lotto Plus 2"
    elif game_str == "POWERBALL":
        return "Powerball"
    elif game_str == "POWERBALL PLUS":
        return "Powerball Plus"
    elif game_str == "DAILY LOTTO":
        return "Daily Lotto"
    
    # Default case: return the original but with proper capitalization
    return game_name.strip().title()

def format_prize(prize_value):
    """Format prize value to standard format (R with commas)"""
    if pd.isna(prize_value):
        return "R0.00"
    
    # If it's already a string with R and proper formatting, return as is
    if isinstance(prize_value, str) and prize_value.startswith('R'):
        return prize_value
    
    # Format as currency
    try:
        # For floats/ints, format with R prefix
        if isinstance(prize_value, (int, float)):
            # Format with commas for thousands and two decimal places
            return f"R{prize_value:,.2f}"
        # For strings without R prefix, add it
        else:
            val = str(prize_value).strip()
            if not val.startswith('R'):
                return f"R{val}"
            return val
    except Exception as e:
        logger.warning(f"Error formatting prize {prize_value}: {str(e)}")
        # Default to returning as string
        return str(prize_value)

def import_snap_lotto_data(excel_file, flask_app=None):
    """
    Import lottery data from the Snap Lotto Excel spreadsheet.
    
    Args:
        excel_file (str): Path to Excel file
        flask_app: Flask app object for context
    """
    try:
        # Use the provided Flask app context or try to import the app if in script mode
        if flask_app:
            ctx = flask_app.app_context()
        else:
            # For standalone script usage, we need to import the app
            from app import app as flask_app
            ctx = flask_app.app_context()
            
        with ctx:
            logger.info(f"Starting import from {excel_file}...")
            
            # Check if this is an empty template file by getting all sheet names
            try:
                xl = pd.ExcelFile(excel_file, engine='openpyxl')  # Explicitly specify the engine
                sheet_names = xl.sheet_names
                logger.info(f"Found sheets: {sheet_names}")
            except Exception as e:
                logger.error(f"Error reading Excel file: {str(e)}. Trying with alternative engine.")
                try:
                    # Try with alternative engine
                    xl = pd.ExcelFile(excel_file, engine='xlrd')
                    sheet_names = xl.sheet_names
                    logger.info(f"Found sheets using alternative engine: {sheet_names}")
                except Exception as e2:
                    logger.error(f"Error reading Excel file with alternative engine: {str(e2)}")
                    from flask import flash
                    flash(f"Unable to read the Excel file. The file might be corrupted or not a valid Excel file.", "danger")
                    return False
            
            # Check if this is our template format (has lotto type sheets)
            expected_sheets = ["Lotto", "Lotto Plus 1", "Lotto Plus 2", "Powerball", "Powerball Plus", "Daily Lotto"]
            
            # If this is our template format, check if there's data in at least one sheet
            if any(sheet in sheet_names for sheet in expected_sheets):
                # Check each sheet for data
                has_data = False
                for sheet in expected_sheets:
                    if sheet in sheet_names:
                        try:
                            df = pd.read_excel(excel_file, sheet_name=sheet, engine='openpyxl')
                            # Check if there are rows with actual data
                            if not df.empty and len(df) > 0:
                                # Check if some common lottery columns exist
                                for column in ["Draw Number", "Draw Date", "Game Name", "Winning Numbers"]:
                                    if any(col for col in df.columns if column.lower() in str(col).lower()):
                                        has_data = True
                                        logger.info(f"Found lottery data in sheet: {sheet}")
                                        break
                        except Exception as e:
                            logger.error(f"Error reading sheet {sheet}: {str(e)}")
                
                # If no data found in any sheet
                if not has_data:
                    logger.info("This appears to be an empty template file. No data to import.")
                    if flask_app:
                        with flask_app.app_context():
                            from flask import flash
                            flash("❗ EMPTY TEMPLATE DETECTED", "danger")  # Use danger for maximum visibility
                            flash("The uploaded file appears to be an empty template. Please add lottery data to the template sheets and try again.", "info")
                            flash("No data was imported. Please fill in the template with lottery data before uploading.", "warning")
                            flash("How to add data: 1) Open the template, 2) Add lottery information to each sheet, 3) Save the file, 4) Upload again", "info")
                    return True  # Special case for empty template
                
            # Try to read the expected sheet for the standard Snap Lotto format
            try:
                df = pd.read_excel(excel_file, sheet_name="Sheet1", engine='openpyxl')
            except ValueError as e:
                logger.error(f"Worksheet named 'Sheet1' not found. Available sheets: {sheet_names}")
                # Try to read the first available sheet instead
                if sheet_names:
                    logger.info(f"Attempting to read first available sheet: {sheet_names[0]}")
                    df = pd.read_excel(excel_file, sheet_name=sheet_names[0])
                else:
                    logger.error("No sheets found in the Excel file.")
                    return False
            
            # CRITICAL: Only skip the first row (header row)
            # This ensures we capture ALL lottery data starting from row 1
            # We previously skipped rows 0-3 which caused data loss - NEVER skip more than 1 row
            logger.warning(f"⚠️ CRITICAL: Only skipping the first row (header) to prevent data loss")
            logger.warning(f"⚠️ Previous bug was skipping first 4 rows causing lottery results to be missed")
            df = df.iloc[1:].reset_index(drop=True)
            
            # Add extra debug logging for the first row (Excel row 2)
            if not df.empty:
                logger.warning(f"⚠️ Processing CRITICAL Row 2 data: {df.iloc[0].to_dict()}")
            
            # Assign proper column names based on row 3
            column_names = {
                df.columns[0]: 'game_name',
                df.columns[1]: 'draw_number',
                df.columns[2]: 'draw_date',
                df.columns[3]: 'winning_numbers',
                df.columns[4]: 'bonus_ball'
            }
            
            # Add division columns
            for i in range(1, 9):
                column_names[df.columns[4 + (i*2) - 1]] = f'div_{i}_winners'
                column_names[df.columns[4 + (i*2)]] = f'div_{i}_prize'
            
            # Add rollover column
            if len(df.columns) > 20:
                column_names[df.columns[20]] = 'rollover_amount'
            
            # Rename columns
            df = df.rename(columns=column_names)
            
            # Drop rows where game_name is missing or NaN
            df = df.dropna(subset=['game_name'])
            
            # Count records before import
            initial_count = LotteryResult.query.count()
            logger.info(f"Database has {initial_count} records before import")
            
            # Track results
            imported_count = 0
            errors_count = 0
            imported_records = []  # Track individual records for import history
            
            # Process each row
            for idx, row in df.iterrows():
                try:
                    # Extract basic data
                    game_name = row['game_name']
                    lottery_type = get_lottery_type(game_name)
                    # Extract and normalize draw number by removing any "Draw" prefix
                    draw_number = str(row['draw_number']).strip()
                    
                    # Enhanced extraction - use data_aggregator's normalize function if available
                    try:
                        from data_aggregator import normalize_draw_number
                        draw_number = normalize_draw_number(draw_number)
                        logger.info(f"Normalized draw number to: {draw_number}")
                    except ImportError:
                        # Fallback to simple normalization if function not available
                        draw_number = draw_number.replace('Draw', '').replace('DRAW', '').strip()
                        logger.info(f"Basic normalization of draw number to: {draw_number}")
                    draw_date = parse_date(row['draw_date'])
                    
                    # Skip rows with missing essential data
                    if not lottery_type or not draw_number or not draw_date:
                        logger.warning(f"Skipping row {idx+1} due to missing key data: {lottery_type}, {draw_number}, {draw_date}")
                        continue
                    
                    # Parse numbers
                    winning_numbers = parse_numbers(row['winning_numbers'])
                    
                    # Daily Lotto has no bonus balls - handle it differently
                    bonus_ball = []
                    # Ensure Daily Lotto has exactly 5 numbers
                    if lottery_type == "Daily Lotto":
                        # Limit Daily Lotto to exactly 5 numbers
                        if len(winning_numbers) > 5:
                            logger.warning(f"Daily Lotto draw {draw_number} has {len(winning_numbers)} numbers, limiting to first 5")
                            winning_numbers = winning_numbers[:5]
                        elif len(winning_numbers) < 5:
                            logger.warning(f"Daily Lotto draw {draw_number} has only {len(winning_numbers)} numbers, expected 5")
                    else:
                        bonus_ball = parse_numbers(row['bonus_ball']) if 'bonus_ball' in row and not pd.isna(row['bonus_ball']) else []
                    
                    # Skip rows with missing winning numbers
                    if not winning_numbers:
                        logger.warning(f"Skipping row {idx+1} due to missing winning numbers")
                        continue
                    
                    # Process divisions data
                    divisions = {}
                    for i in range(1, 9):
                        winners_col = f'div_{i}_winners'
                        prize_col = f'div_{i}_prize'
                        
                        if winners_col in row and prize_col in row and not pd.isna(row[winners_col]) and not pd.isna(row[prize_col]):
                            # Check for "Data N/A" or similar placeholders
                            if isinstance(row[winners_col], str) and "N/A" in row[winners_col]:
                                # Skip adding this division entirely when data is not available
                                continue
                            
                            # Handle Daily Lotto differently due to different data format in the spreadsheet
                            if lottery_type == "Daily Lotto":
                                # Check if the winners column actually contains a prize value (R prefix)
                                if isinstance(row[winners_col], str) and row[winners_col].strip().startswith('R'):
                                    divisions[f"Division {i}"] = {
                                        "winners": str(i), # For Daily Lotto, division number = number of matches
                                        "prize": format_prize(row[winners_col])
                                    }
                                else:
                                    divisions[f"Division {i}"] = {
                                        "winners": str(int(row[winners_col]) if isinstance(row[winners_col], (int, float)) else row[winners_col]),
                                        "prize": format_prize(row[prize_col])
                                    }
                            else:
                                divisions[f"Division {i}"] = {
                                    "winners": str(int(row[winners_col]) if isinstance(row[winners_col], (int, float)) else row[winners_col]),
                                    "prize": format_prize(row[prize_col])
                                }
                    
                    # Check if this result already exists
                    existing = LotteryResult.query.filter_by(
                        lottery_type=lottery_type,
                        draw_number=draw_number
                    ).first()
                    
                    if existing:
                        logger.info(f"Updating existing result for {lottery_type} draw {draw_number}")
                        existing.draw_date = draw_date
                        existing.numbers = json.dumps(winning_numbers)
                        existing.bonus_numbers = json.dumps(bonus_ball) if bonus_ball else None
                        existing.divisions = json.dumps(divisions) if divisions else None
                        existing.source_url = "imported-from-excel"
                        existing.ocr_provider = "manual-import"
                        existing.ocr_model = "excel-spreadsheet"
                        existing.ocr_timestamp = datetime.utcnow().isoformat()
                    else:
                        # Create new result
                        new_result = LotteryResult(
                            lottery_type=lottery_type,
                            draw_number=draw_number,
                            draw_date=draw_date,
                            numbers=json.dumps(winning_numbers),
                            bonus_numbers=json.dumps(bonus_ball) if bonus_ball else None,
                            divisions=json.dumps(divisions) if divisions else None,
                            source_url="imported-from-excel",
                            ocr_provider="manual-import",
                            ocr_model="excel-spreadsheet",
                            ocr_timestamp=datetime.utcnow().isoformat()
                        )
                        db.session.add(new_result)
                    
                    # Commit each result individually to avoid losing all data if one fails
                    db.session.commit()
                    
                    # Store this record in import_tracking for later reference
                    # Record if this was a new record or an update
                    is_new_record = existing is None
                    lottery_result = existing if existing else db.session.query(LotteryResult).filter_by(
                        lottery_type=lottery_type,
                        draw_number=draw_number
                    ).first()
                    
                    imported_records.append({
                        'lottery_type': lottery_type,
                        'draw_number': draw_number,
                        'draw_date': draw_date,
                        'is_new': is_new_record,
                        'lottery_result_id': lottery_result.id
                    })
                    
                    imported_count += 1
                    
                    if imported_count % 10 == 0:
                        logger.info(f"Imported {imported_count} records so far...")
                    
                except Exception as e:
                    errors_count += 1
                    logger.error(f"Error processing row {idx+1}: {str(e)}")
                    # Rollback this row only
                    db.session.rollback()
            
            # Count records after import
            final_count = LotteryResult.query.count()
            
            logger.info("Import completed!")
            logger.info(f"Records: {initial_count} -> {final_count} (added {final_count - initial_count})")
            logger.info(f"Successfully imported/updated {imported_count} records")
            logger.info(f"Encountered {errors_count} errors")
            
            # Return stats dictionary for detailed success message
            return {
                "success": True,
                "initial_count": initial_count,
                "final_count": final_count,
                "total": imported_count,
                "errors": errors_count,
                "added": final_count - initial_count,
                "updated": imported_count - (final_count - initial_count),
                "imported_records": imported_records  # Include records for import history
            }
    except Exception as e:
        logger.error(f"Error during import operation: {str(e)}")
        return False

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python import_snap_lotto_data.py <excel_file> [--purge]")
        print("  --purge: Optional flag to purge existing data before import")
        sys.exit(1)
    
    excel_file = sys.argv[1]
    if not os.path.exists(excel_file):
        print(f"Error: Excel file {excel_file} not found")
        sys.exit(1)
    
    # Check if purge flag is provided
    should_purge = len(sys.argv) > 2 and sys.argv[2] == "--purge"
    
    if should_purge:
        # First purge existing data
        from purge_data import purge_data
        if purge_data():
            print("Existing data purged successfully.")
        else:
            print("Error: Failed to purge existing data. Import aborted.")
            sys.exit(1)
    
    # Import from Excel
    import_snap_lotto_data(excel_file)