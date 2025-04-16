#!/usr/bin/env python
"""
Script to import South African lottery data from Excel spreadsheet.
This script purges existing data and imports new data from the provided Excel file.
"""

import os
import sys
import logging
import json
import pandas as pd
import numpy as np
from datetime import datetime
from flask import current_app
from models import db, LotteryResult, Screenshot

# Set up logging
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def parse_date(date_str):
    """Parse date from string format to datetime object"""
    try:
        if pd.isna(date_str):
            return None
            
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

def parse_divisions(divisions_data):
    """Parse divisions data from various formats to a structured dictionary"""
    if pd.isna(divisions_data):
        return {}
        
    divisions = {}
    try:
        # If it's already a string that looks like JSON
        if isinstance(divisions_data, str) and ('{' in divisions_data or ':' in divisions_data):
            try:
                # Try to parse as JSON if it looks like a dictionary
                if '{' in divisions_data:
                    return json.loads(divisions_data)
                
                # Try to parse from semicolon-separated format
                # Division 1: 0 winners, R0.00; Division 2: 5 winners, R100,563.40
                if ';' in divisions_data:
                    division_parts = divisions_data.split(';')
                    for part in division_parts:
                        if ':' in part:
                            div_name, div_data = part.split(':', 1)
                            div_name = div_name.strip()
                            div_data = div_data.strip()
                            if ',' in div_data:
                                winners_part, prize_part = div_data.split(',', 1)
                                # Clean up winners part to extract just the number
                                winners = ''.join(c for c in winners_part if c.isdigit())
                                # Keep the prize as is with R and commas
                                prize = prize_part.strip()
                                divisions[div_name] = {
                                    "winners": winners,
                                    "prize": prize
                                }
            except Exception as e:
                logger.warning(f"Error parsing divisions string: {str(e)}")
                
        # For more complex division data that might be in columns
        # We'll handle this in the main import function
                
    except Exception as e:
        logger.error(f"Error parsing divisions: {str(e)}")
        
    return divisions

def standardize_lottery_type(lottery_type):
    """Standardize lottery type names for consistency"""
    if pd.isna(lottery_type):
        return ""
        
    lt = str(lottery_type).strip().lower()
    
    # Normalize common variations
    if 'lotto plus 1' in lt or 'lotto+1' in lt or 'lotto + 1' in lt:
        return 'Lotto Plus 1'
    elif 'lotto plus 2' in lt or 'lotto+2' in lt or 'lotto + 2' in lt:
        return 'Lotto Plus 2'
    elif 'powerball plus' in lt or 'powerball+' in lt or 'power ball plus' in lt:
        return 'Powerball Plus'
    elif 'powerball' in lt or 'power ball' in lt:
        return 'Powerball'
    elif 'daily lotto' in lt or 'dailylotto' in lt:
        return 'Daily Lotto'
    elif 'lotto' in lt:
        return 'Lotto'
    
    # If no match, return original with proper capitalization
    return str(lottery_type).strip()

def import_excel_data(excel_file, flask_app=None):
    """
    Import lottery data from Excel spreadsheet.
    
    Args:
        excel_file (str): Path to Excel file
        flask_app: Flask app object for context (optional)
    """
    try:
        # Use current_app or provided app
        ctx = flask_app.app_context() if flask_app else current_app.app_context()
        
        with ctx:
            logger.info(f"Starting import from {excel_file}...")
            
            # Read Excel file - try multiple sheets if needed
            try:
                # First try reading with default sheet
                df = pd.read_excel(excel_file)
                
                # If we got an empty dataframe or missing expected columns, try reading all sheets
                if df.empty or not any(col for col in df.columns if 'lotto' in str(col).lower() or 'draw' in str(col).lower()):
                    logger.info("Initial sheet appears empty or missing lottery data. Checking all sheets...")
                    xlsx = pd.ExcelFile(excel_file)
                    
                    # Try each sheet until we find one with lottery data
                    for sheet_name in xlsx.sheet_names:
                        logger.info(f"Trying sheet: {sheet_name}")
                        df = pd.read_excel(excel_file, sheet_name=sheet_name)
                        # Check if this sheet has lottery data
                        if any(col for col in df.columns if 'lotto' in str(col).lower() or 'draw' in str(col).lower() or 'game' in str(col).lower()):
                            logger.info(f"Found lottery data in sheet: {sheet_name}")
                            break
            except Exception as e:
                logger.error(f"Error reading Excel file: {str(e)}")
                return False
            
            # Replace NaN values with None for cleaner processing
            df = df.replace({np.nan: None})
            
            # Log column headers for debugging
            logger.info(f"Excel columns: {', '.join(str(col) for col in df.columns)}")
            
            # Map standard column names to actual columns in the spreadsheet
            column_mapping = {}
            for col in df.columns:
                col_lower = str(col).lower()
                
                # Map standard fields to actual column names
                if 'game type' in col_lower or 'lottery' in col_lower or 'lotto type' in col_lower:
                    column_mapping['lottery_type'] = col
                elif 'draw' in col_lower and ('id' in col_lower or 'number' in col_lower or 'no' in col_lower):
                    column_mapping['draw_number'] = col
                elif 'date' in col_lower or 'game date' in col_lower:
                    column_mapping['draw_date'] = col
                elif ('winning' in col_lower and 'number' in col_lower) or ('main' in col_lower and 'number' in col_lower):
                    column_mapping['numbers'] = col
                elif ('bonus' in col_lower or 'ball' in col_lower) and 'number' in col_lower:
                    column_mapping['bonus_numbers'] = col
                elif 'division' in col_lower or 'prize' in col_lower or 'payout' in col_lower:
                    # Note multiple division columns for later
                    if 'divisions' not in column_mapping:
                        column_mapping['divisions'] = []
                    column_mapping['divisions'].append(col)
            
            logger.info(f"Column mapping: {column_mapping}")
            
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
                    # Skip header rows or rows that appear to be titles/headers
                    if idx < 1 and any(isinstance(val, str) and val.isupper() for val in row.values):
                        continue
                        
                    # Determine if this is a valid data row
                    # Skip if row appears empty (more than 50% of values are None/NaN)
                    if row.isna().sum() > len(row) * 0.5:
                        continue
                    
                    # Extract data using our column mapping
                    lottery_type = standardize_lottery_type(row.get(column_mapping.get('lottery_type', ''), None))
                    draw_number = str(row.get(column_mapping.get('draw_number', ''), '')).strip()
                    draw_date_str = row.get(column_mapping.get('draw_date', ''), None)
                    numbers_str = row.get(column_mapping.get('numbers', ''), None)
                    bonus_numbers_str = row.get(column_mapping.get('bonus_numbers', ''), None)
                    
                    # Skip rows with missing essential data
                    if not lottery_type or not draw_date_str or not numbers_str:
                        logger.warning(f"Skipping row {idx+2} due to missing key data")
                        continue
                    
                    # Parse date
                    draw_date = parse_date(draw_date_str)
                    if not draw_date:
                        logger.warning(f"Skipping row {idx+2} due to invalid date: {draw_date_str}")
                        continue
                    
                    # Parse numbers
                    numbers = parse_numbers(numbers_str)
                    if not numbers:
                        logger.warning(f"Skipping row {idx+2} due to invalid numbers: {numbers_str}")
                        continue
                    
                    # Parse bonus numbers
                    bonus_numbers = parse_numbers(bonus_numbers_str) if bonus_numbers_str else []
                    
                    # Handle divisions
                    divisions = {}
                    # First check if we have a dedicated divisions column
                    if 'divisions' in column_mapping and isinstance(column_mapping['divisions'], list):
                        # Check if we have division-specific columns (Div 1, Div 2, etc.)
                        div_columns = column_mapping['divisions']
                        
                        for div_col in div_columns:
                            div_value = row.get(div_col)
                            if not pd.isna(div_value):
                                # Try to extract division number from column name
                                div_name = div_col
                                if 'div' in str(div_col).lower():
                                    div_match = ''.join(c for c in str(div_col) if c.isdigit())
                                    if div_match:
                                        div_name = f"Division {div_match}"
                                
                                # If the value contains winners and prize together
                                if isinstance(div_value, str) and ',' in div_value:
                                    winners_part, prize_part = div_value.split(',', 1)
                                    # Extract just the number for winners
                                    winners = ''.join(c for c in winners_part if c.isdigit())
                                    # Keep the prize with formatting (R, commas)
                                    prize = prize_part.strip()
                                    divisions[div_name] = {
                                        "winners": winners,
                                        "prize": prize
                                    }
                                else:
                                    # If it's just a raw value, assume it's the prize amount
                                    divisions[div_name] = {
                                        "winners": "1",  # Default to 1 winner if not specified
                                        "prize": f"R{div_value}" if not str(div_value).startswith('R') else str(div_value)
                                    }
                    
                    # Check if this result already exists
                    existing = LotteryResult.query.filter_by(
                        lottery_type=lottery_type,
                        draw_number=draw_number
                    ).first()
                    
                    is_new_record = False
                    lottery_result = None

                    if existing:
                        # Update existing record
                        logger.info(f"Updating existing result for {lottery_type} draw {draw_number}")
                        existing.draw_date = draw_date
                        existing.numbers = json.dumps(numbers)
                        existing.bonus_numbers = json.dumps(bonus_numbers) if bonus_numbers else None
                        existing.divisions = json.dumps(divisions) if divisions else None
                        existing.source_url = "imported-from-excel"
                        existing.ocr_provider = "manual-import"
                        existing.ocr_model = "excel-spreadsheet"
                        existing.ocr_timestamp = datetime.utcnow().isoformat()
                        lottery_result = existing
                    else:
                        # Create new result
                        is_new_record = True
                        new_result = LotteryResult(
                            lottery_type=lottery_type,
                            draw_number=draw_number,
                            draw_date=draw_date,
                            numbers=json.dumps(numbers),
                            bonus_numbers=json.dumps(bonus_numbers) if bonus_numbers else None,
                            divisions=json.dumps(divisions) if divisions else None,
                            source_url="imported-from-excel",
                            ocr_provider="manual-import",
                            ocr_model="excel-spreadsheet",
                            ocr_timestamp=datetime.utcnow().isoformat()
                        )
                        db.session.add(new_result)
                        lottery_result = new_result
                    
                    # Commit each result individually to avoid losing all data if one fails
                    db.session.commit()
                    
                    # Store this record in import_tracking for later reference
                    # Import history will be created in main.py after this function returns
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
                    logger.error(f"Error processing row {idx+2}: {str(e)}")
                    # Rollback this row only
                    db.session.rollback()
            
            # Count records after import
            final_count = LotteryResult.query.count()
            
            logger.info("Import completed!")
            logger.info(f"Records: {initial_count} -> {final_count} (added {final_count - initial_count})")
            logger.info(f"Successfully imported/updated {imported_count} records")
            logger.info(f"Encountered {errors_count} errors")
            
            # Return detailed import results
            return {
                'success': True,
                'total': imported_count,
                'initial_count': initial_count,
                'final_count': final_count,
                'added': final_count - initial_count,
                'errors': errors_count,
                'imported_records': imported_records  # Include records for import history
            }
    except Exception as e:
        logger.error(f"Error during import operation: {str(e)}")
        return False

def create_empty_template(output_path):
    """
    Create an empty Excel template for lottery data import.
    
    Args:
        output_path (str): Path to save the Excel file
    
    Returns:
        bool: Success status
    """
    try:
        # Create a Pandas Excel writer
        writer = pd.ExcelWriter(output_path, engine='openpyxl')
        
        # Create template dataframes for each lottery type
        lottery_types = [
            'Lotto', 
            'Lotto Plus 1', 
            'Lotto Plus 2', 
            'Powerball', 
            'Powerball Plus', 
            'Daily Lotto'
        ]
        
        # Define columns for the template
        columns = [
            'Game Type', 
            'Draw Number', 
            'Draw Date', 
            'Winning Numbers', 
            'Bonus Number',
            'Division 1 Prize', 
            'Division 1 Winners',
            'Division 2 Prize', 
            'Division 2 Winners',
            'Division 3 Prize', 
            'Division 3 Winners'
        ]
        
        # Create a sheet for each lottery type
        for lottery_type in lottery_types:
            # Create empty dataframe with headers
            df = pd.DataFrame(columns=columns)
            
            # Add a sample row with format hints
            sample_data = {
                'Game Type': lottery_type,
                'Draw Number': '1234',
                'Draw Date': '2025-01-01',
                'Winning Numbers': '1, 2, 3, 4, 5, 6',
                'Bonus Number': '7' if lottery_type != 'Daily Lotto' else '',
                'Division 1 Prize': 'R1,000,000.00',
                'Division 1 Winners': '1',
                'Division 2 Prize': 'R100,000.00',
                'Division 2 Winners': '5',
                'Division 3 Prize': 'R2,500.00',
                'Division 3 Winners': '100'
            }
            df = pd.concat([df, pd.DataFrame([sample_data])], ignore_index=True)
            
            # Write dataframe to Excel sheet
            df.to_excel(writer, sheet_name=lottery_type, index=False)
            
        # Save the Excel file
        writer.close()
        
        logger.info(f"Empty template created at {output_path}")
        return True
    
    except Exception as e:
        logger.error(f"Error creating empty template: {str(e)}")
        return False

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python import_excel.py <excel_file>")
        sys.exit(1)
    
    excel_file = sys.argv[1]
    if not os.path.exists(excel_file):
        print(f"Error: Excel file {excel_file} not found")
        sys.exit(1)
    
    # First purge existing data
    from purge_data import purge_data
    if purge_data():
        # Then import from Excel
        import_excel_data(excel_file)
    else:
        print("Error: Failed to purge existing data. Import aborted.")
        sys.exit(1)