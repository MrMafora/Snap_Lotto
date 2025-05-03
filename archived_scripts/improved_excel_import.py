#!/usr/bin/env python
"""
Improved Excel Import System

This module provides a more robust system for importing Excel data into the database.
It's designed to handle various Excel formats and column naming conventions.

Key improvements:
1. Better error handling and logging
2. More precise column name matching
3. Better handling of number parsing
4. Clearer feedback on import process
5. Detailed logging of what was imported
"""

import pandas as pd
import numpy as np
import json
import os
import logging
import traceback
from datetime import datetime
from flask import Flask
from models import db, LotteryResult, ImportHistory, ImportedRecord
import sys

# Configure logging
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def normalize_lottery_type(lottery_type):
    """
    Normalize lottery type names with exact matching for important types.
    
    Args:
        lottery_type (str): The lottery type name
        
    Returns:
        str: Normalized lottery type
    """
    if not lottery_type:
        return "Unknown"
    
    # First, handle exact matches with case sensitivity
    cleaned_type = str(lottery_type).strip()
    
    # Handle the exact matches from the Excel file
    EXACT_MATCHES = {
        'PowerBall': 'Powerball',
        'PowerBall PLUS': 'Powerball Plus',
        'Lottery Plus 1': 'Lottery Plus 1',
        'Lottery Plus 2': 'Lottery Plus 2',
        'Daily Lottery': 'Daily Lottery',
        'Lottery': 'Lottery',
        'Powerball': 'Powerball',
        'Powerball Plus': 'Powerball Plus',
    }
    
    if cleaned_type in EXACT_MATCHES:
        return EXACT_MATCHES[cleaned_type]
    
    # Convert to uppercase for case-insensitive matching
    upper_type = cleaned_type.upper()
    
    # Prioritize "Lottery" terminology with flexible pattern matching
    if upper_type == 'LOTTO' or upper_type == 'LOTTERY':
        return 'Lottery'
    elif any(pattern in upper_type for pattern in ['LOTTERY PLUS 1', 'LOTTO PLUS 1']):
        return 'Lottery Plus 1'
    elif any(pattern in upper_type for pattern in ['LOTTERY PLUS 2', 'LOTTO PLUS 2']):
        return 'Lottery Plus 2' 
    elif any(pattern in upper_type for pattern in ['POWERBALL PLUS', 'POWER BALL PLUS']):
        return 'Powerball Plus'
    elif any(pattern in upper_type for pattern in ['POWERBALL', 'POWER BALL']):
        return 'Powerball'
    elif any(pattern in upper_type for pattern in ['DAILY LOTTERY', 'DAILY LOTTO']):
        return 'Daily Lottery'
        
    # If no match, return original with proper capitalization
    return cleaned_type

def parse_numbers(number_str):
    """
    Parse winning numbers from string, handling various formats.
    
    Args:
        number_str: The string containing the numbers
        
    Returns:
        list: List of integers
    """
    if pd.isna(number_str):
        return []
    
    # Convert to string in case it's a numeric type
    nums_str = str(number_str).strip()
    
    # Handle empty strings
    if not nums_str:
        return []
    
    # Try different delimiters
    for delimiter in [',', ' ', ';']:
        if delimiter in nums_str:
            try:
                # Try to parse numbers separated by the delimiter
                numbers = [int(n.strip()) for n in nums_str.split(delimiter) if n.strip() and n.strip().isdigit()]
                if numbers:
                    return numbers
            except Exception as e:
                logger.debug(f"Failed to parse with delimiter '{delimiter}': {e}")
                continue
    
    # If no delimiters worked, check if it's a single number
    if nums_str.isdigit():
        return [int(nums_str)]
    
    # Failed to parse numbers
    return []

def improved_excel_import(excel_path, app):
    """
    Improved function to import Excel data into the database.
    
    Args:
        excel_path (str): Path to Excel file
        app (Flask): Flask application instance for context
        
    Returns:
        dict: Import statistics
    """
    stats = {
        "total_processed": 0,
        "sheets_processed": 0,
        "updated_records": 0,
        "new_records": 0,
        "errors": 0,
        "lottery_types": {}
    }
    
    with app.app_context():
        try:
            # Create import history record
            import_history = ImportHistory(
                import_date=datetime.utcnow(),
                import_type="excel-import",
                file_name=os.path.basename(excel_path),
                records_added=0,
                records_updated=0,
                total_processed=0,
                errors=0
            )
            db.session.add(import_history)
            db.session.commit()
            import_history_id = import_history.id
            
            # Print information about the Excel file
            file_size = os.path.getsize(excel_path)
            logger.info(f"Processing Excel file: {excel_path} (Size: {file_size} bytes)")
            
            # Get list of sheets in Excel file
            xlsx = pd.ExcelFile(excel_path, engine='openpyxl')
            sheets = xlsx.sheet_names
            logger.info(f"Found {len(sheets)} sheets: {', '.join(sheets)}")
            
            # Process each sheet
            for sheet in sheets:
                try:
                    logger.info(f"Processing sheet: {sheet}")
                    
                    # Read sheet
                    df = pd.read_excel(excel_path, sheet_name=sheet)
                    
                    # Skip empty sheets
                    if df.empty:
                        logger.info(f"Sheet {sheet} is empty, skipping")
                        continue
                    
                    # Check if this is a multi-lottery sheet or single lottery sheet
                    is_multi_lottery = False
                    if 'Game Name' in df.columns:
                        # Count unique lottery types
                        unique_games = df['Game Name'].dropna().unique()
                        logger.info(f"Found {len(unique_games)} unique lottery types in the sheet")
                        if len(unique_games) > 1:
                            is_multi_lottery = True
                    
                    # Print column names for this sheet
                    logger.info(f"Columns in sheet {sheet}: {list(df.columns)}")
                    
                    # Initialize sheet stats
                    sheet_stats = {
                        "processed": 0,
                        "updated": 0,
                        "new": 0,
                        "errors": 0
                    }
                    
                    # Filter out non-data rows (metadata, headers, notes)
                    valid_rows = df
                    
                    # For multi-lottery sheets, only keep rows with valid Game Name and Draw Number
                    if is_multi_lottery:
                        # Keep only rows that have both Game Name and Draw Number
                        valid_mask = (~pd.isna(df['Game Name'])) & (~pd.isna(df['Draw Number']))
                        
                        # Make sure Game Name is a lottery type (skip note rows)
                        def is_lottery_type(game_name):
                            if pd.isna(game_name):
                                return False
                            game_name = str(game_name).strip().lower()
                            return any(lottery_keyword in game_name for lottery_keyword in 
                                    ['lottery', 'lotto', 'powerball', 'power ball', 'daily'])
                        
                        valid_mask = valid_mask & df['Game Name'].apply(is_lottery_type)
                        valid_rows = df[valid_mask]
                        logger.info(f"Filtered {len(df)} rows down to {len(valid_rows)} valid lottery data rows")
                    
                    # Process each row
                    for index, row in valid_rows.iterrows():
                        try:
                            # Skip rows with insufficient data - require Game Name and Draw Number
                            if pd.isna(row.get('Game Name')) or pd.isna(row.get('Draw Number')):
                                continue
                            
                            # Skip rows with example data
                            draw_number_str = str(row.get('Draw Number')).strip()
                            if 'example' in draw_number_str.lower():
                                logger.info(f"Skipping example row: {row.get('Game Name')} - {draw_number_str}")
                                continue
                            
                            # Get lottery type from data
                            lottery_type = normalize_lottery_type(row['Game Name'])
                            
                            # Get draw number as string - handle both numeric and string formats
                            try:
                                draw_number = str(int(row['Draw Number']))
                            except:
                                draw_number = draw_number_str
                            
                            # Skip if missing lottery type or draw number
                            if not lottery_type or not draw_number:
                                logger.warning(f"Skipping row {index} - missing lottery type or draw number")
                                continue
                            
                            # Parse draw date
                            draw_date = None
                            if not pd.isna(row.get('Draw Date')):
                                if isinstance(row['Draw Date'], datetime):
                                    draw_date = row['Draw Date']
                                else:
                                    try:
                                        date_str = str(row['Draw Date'])
                                        if ' ' in date_str:
                                            date_str = date_str.split()[0]
                                        
                                        # Try different date formats
                                        for fmt in ["%Y-%m-%d", "%d-%m-%Y", "%m/%d/%Y", "%d/%m/%Y"]:
                                            try:
                                                draw_date = datetime.strptime(date_str, fmt)
                                                break
                                            except:
                                                continue
                                    except Exception as e:
                                        logger.warning(f"Failed to parse date '{row['Draw Date']}': {e}")
                                        draw_date = datetime.utcnow()
                            else:
                                draw_date = datetime.utcnow()
                            
                            # Parse winning numbers
                            numbers = []
                            for col_name in ['Winning Numbers', 'Winning Numbers (Numerical)']:
                                if col_name in row and not pd.isna(row.get(col_name)):
                                    numbers = parse_numbers(row[col_name])
                                    if numbers:
                                        break
                            
                            # Parse bonus numbers
                            bonus_numbers = []
                            if 'Bonus Ball' in row and not pd.isna(row.get('Bonus Ball')):
                                bonus_str = str(row['Bonus Ball'])
                                
                                # For Daily Lottery, the Bonus Ball is sometimes "Five Correct Numbers"
                                if 'daily' in lottery_type.lower() and ('five correct' in bonus_str.lower() or 
                                                                      'division' in bonus_str.lower()):
                                    bonus_numbers = []
                                else:
                                    bonus_numbers = parse_numbers(bonus_str)
                            
                            # Skip if missing essential data
                            if not lottery_type or not draw_number:
                                logger.warning(f"Skipping row {index} - missing lottery_type or draw_number")
                                continue
                            
                            # For some types, allow importing without numbers
                            if not numbers and not (('powerball' in lottery_type.lower()) or 
                                                 ('daily' in lottery_type.lower())):
                                logger.warning(f"Skipping row {index} - missing numbers for {lottery_type}")
                                continue
                            
                            # If we got here, we have at least lottery_type and draw_number
                            if not numbers:
                                numbers = []
                            
                            # Log what we found
                            logger.info(f"Found {lottery_type} Draw #{draw_number}: {numbers}, Bonus: {bonus_numbers}")
                            
                            # Check if record already exists
                            existing = LotteryResult.query.filter_by(
                                lottery_type=lottery_type,
                                draw_number=draw_number
                            ).first()
                            
                            # Update statistics
                            if lottery_type not in stats["lottery_types"]:
                                stats["lottery_types"][lottery_type] = {
                                    "processed": 0,
                                    "updated": 0,
                                    "new": 0,
                                    "errors": 0
                                }
                            
                            # Create JSON data
                            numbers_json = json.dumps(numbers)
                            bonus_numbers_json = json.dumps(bonus_numbers) if bonus_numbers else None
                            
                            if existing:
                                try:
                                    # Update existing record
                                    existing.draw_date = draw_date
                                    existing.numbers = numbers_json
                                    existing.bonus_numbers = bonus_numbers_json
                                    existing.source_url = "imported-from-excel-file"
                                    existing.ocr_provider = "excel-import"
                                    db.session.commit()
                                    
                                    stats["updated_records"] += 1
                                    stats["lottery_types"][lottery_type]["updated"] += 1
                                    sheet_stats["updated"] += 1
                                    
                                    logger.info(f"Updated: {lottery_type} Draw {draw_number}")
                                except Exception as db_error:
                                    db.session.rollback()
                                    logger.error(f"Database error updating {lottery_type} Draw {draw_number}: {db_error}")
                                    stats["errors"] += 1
                                    stats["lottery_types"][lottery_type]["errors"] += 1
                                    sheet_stats["errors"] += 1
                            else:
                                # Create new record
                                lottery_result = LotteryResult(
                                    lottery_type=lottery_type,
                                    draw_number=draw_number,
                                    draw_date=draw_date,
                                    numbers=numbers_json,
                                    bonus_numbers=bonus_numbers_json,
                                    source_url="imported-from-excel-file",
                                    ocr_provider="excel-import",
                                    ocr_timestamp=datetime.utcnow().isoformat()
                                )
                                try:
                                    db.session.add(lottery_result)
                                    db.session.commit()
                                    
                                    stats["new_records"] += 1
                                    stats["lottery_types"][lottery_type]["new"] += 1
                                    sheet_stats["new"] += 1
                                    
                                    logger.info(f"Created: {lottery_type} Draw {draw_number}")
                                except Exception as db_error:
                                    db.session.rollback()
                                    logger.error(f"Database error creating {lottery_type} Draw {draw_number}: {db_error}")
                                    stats["errors"] += 1
                                    stats["lottery_types"][lottery_type]["errors"] += 1
                                    sheet_stats["errors"] += 1
                                
                            # Update stats
                            stats["total_processed"] += 1
                            stats["lottery_types"][lottery_type]["processed"] += 1
                            sheet_stats["processed"] += 1
                        
                        except Exception as e:
                            logger.error(f"Error processing row {index}: {e}")
                            logger.error(traceback.format_exc())
                            stats["errors"] += 1
                            sheet_stats["errors"] += 1
                            
                            # Make sure we have an entry for this lottery type
                            try:
                                if 'lottery_type' in locals() and lottery_type:
                                    if lottery_type not in stats["lottery_types"]:
                                        stats["lottery_types"][lottery_type] = {
                                            "processed": 0, "updated": 0, "new": 0, "errors": 0
                                        }
                                    stats["lottery_types"][lottery_type]["errors"] += 1
                            except Exception as inner_e:
                                logger.error(f"Error updating stats: {inner_e}")
                    
                    # Update sheet processed count
                    stats["sheets_processed"] += 1
                    
                    # Log sheet stats
                    logger.info(f"Sheet {sheet} processed: {sheet_stats['processed']} rows "
                               f"({sheet_stats['new']} new, {sheet_stats['updated']} updated, "
                               f"{sheet_stats['errors']} errors)")
                    
                except Exception as e:
                    logger.error(f"Error processing sheet {sheet}: {e}")
                    logger.error(traceback.format_exc())
                    stats["errors"] += 1
            
            # Update import history
            import_history.records_added = stats["new_records"]
            import_history.records_updated = stats["updated_records"]
            import_history.total_processed = stats["total_processed"]
            import_history.errors = stats["errors"]
            db.session.commit()
            
            logger.info(f"Import completed: {stats['total_processed']} records processed "
                       f"({stats['new_records']} new, {stats['updated_records']} updated, "
                       f"{stats['errors']} errors)")
            
            return stats
        
        except Exception as e:
            logger.error(f"Error importing Excel file: {e}")
            logger.error(traceback.format_exc())
            return {"error": str(e)}

# If run directly, find and import the Excel file
if __name__ == "__main__":
    from main import app
    
    # Check if file path was provided as command line argument
    if len(sys.argv) > 1 and os.path.exists(sys.argv[1]):
        excel_path = sys.argv[1]
        print(f"Importing from specified file: {excel_path}")
        stats = improved_excel_import(excel_path, app)
    else:
        # Find the most recent Excel file in uploads and attached_assets folders
        excel_files = []
        for directory in ["uploads", "attached_assets"]:
            if os.path.exists(directory):
                for filename in os.listdir(directory):
                    if filename.endswith(".xlsx"):
                        full_path = os.path.join(directory, filename)
                        excel_files.append((full_path, os.path.getmtime(full_path)))
        
        if not excel_files:
            print("No Excel files found in uploads or attached_assets directories")
            sys.exit(1)
        
        # Sort by modification time (newest first)
        excel_files.sort(key=lambda x: x[1], reverse=True)
        newest_file = excel_files[0][0]
        
        print(f"Importing from newest file: {newest_file}")
        stats = improved_excel_import(newest_file, app)
    
    # Print summary
    print("\nImport Summary:")
    print(f"Total processed: {stats.get('total_processed', 0)}")
    print(f"New records: {stats.get('new_records', 0)}")
    print(f"Updated records: {stats.get('updated_records', 0)}")
    print(f"Errors: {stats.get('errors', 0)}")
    print("\nBy lottery type:")
    for lottery_type, type_stats in stats.get('lottery_types', {}).items():
        print(f"  {lottery_type}: {type_stats['processed']} processed "
             f"({type_stats['new']} new, {type_stats['updated']} updated, "
             f"{type_stats['errors']} errors)")