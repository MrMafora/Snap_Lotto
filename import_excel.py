#!/usr/bin/env python
"""
Script to import lottery data from Excel spreadsheet.
This script should be run after purging existing data using purge_data.py.
"""

import os
import sys
import logging
import json
import pandas as pd
from datetime import datetime
from main import app
from models import db, LotteryResult, Screenshot

# Set up logging
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def parse_date(date_str):
    """Parse date from string format to datetime object"""
    try:
        # Try various date formats
        for fmt in ['%Y-%m-%d', '%d/%m/%Y', '%d-%m-%Y', '%Y/%m/%d']:
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
        # Remove any non-digit characters and split by whitespace
        clean_str = ''.join(c if c.isdigit() or c.isspace() else ' ' for c in str(numbers_str))
        numbers = [int(num) for num in clean_str.split() if num.strip()]
        return numbers
    except Exception as e:
        logger.error(f"Error parsing numbers {numbers_str}: {str(e)}")
        return []

def import_excel_data(excel_file):
    """
    Import lottery data from Excel spreadsheet.
    
    Args:
        excel_file (str): Path to Excel file
    """
    try:
        with app.app_context():
            logger.info(f"Starting import from {excel_file}...")
            
            # Read Excel file
            df = pd.read_excel(excel_file)
            
            # Log column headers for debugging
            logger.info(f"Excel columns: {', '.join(df.columns)}")
            
            # Count records before import
            initial_count = LotteryResult.query.count()
            logger.info(f"Database has {initial_count} records before import")
            
            # Track results
            imported_count = 0
            errors_count = 0
            
            # Process each row
            for idx, row in df.iterrows():
                try:
                    # Extract data from row (adjust column names as needed)
                    lottery_type = str(row.get('Game Type', '')).strip()
                    draw_number = str(row.get('Draw ID', '')).strip()
                    draw_date_str = str(row.get('Game Date', ''))
                    numbers_str = str(row.get('Winning Numbers', ''))
                    bonus_numbers_str = str(row.get('Bonus Numbers', ''))
                    divisions_str = str(row.get('Divisions', ''))
                    
                    # Skip rows with missing essential data
                    if not lottery_type or not draw_date_str or not numbers_str:
                        logger.warning(f"Skipping row {idx+2} due to missing data: {row.to_dict()}")
                        errors_count += 1
                        continue
                    
                    # Parse date
                    draw_date = parse_date(draw_date_str)
                    if not draw_date:
                        logger.warning(f"Skipping row {idx+2} due to invalid date: {draw_date_str}")
                        errors_count += 1
                        continue
                    
                    # Parse numbers
                    numbers = parse_numbers(numbers_str)
                    if not numbers:
                        logger.warning(f"Skipping row {idx+2} due to invalid numbers: {numbers_str}")
                        errors_count += 1
                        continue
                    
                    # Parse bonus numbers
                    bonus_numbers = parse_numbers(bonus_numbers_str) if bonus_numbers_str else []
                    
                    # Parse divisions
                    divisions = {}
                    if divisions_str and divisions_str.strip().lower() != 'nan':
                        try:
                            # Try to parse as JSON if it looks like a dictionary
                            if '{' in divisions_str:
                                divisions = json.loads(divisions_str)
                            else:
                                # Otherwise, try to parse from custom format
                                division_parts = divisions_str.split(';')
                                for part in division_parts:
                                    if ':' in part:
                                        div_name, div_data = part.split(':', 1)
                                        div_name = div_name.strip()
                                        div_data = div_data.strip()
                                        if ',' in div_data:
                                            winners, prize = div_data.split(',', 1)
                                            divisions[div_name] = {
                                                "winners": winners.strip(),
                                                "prize": prize.strip()
                                            }
                        except Exception as e:
                            logger.warning(f"Error parsing divisions for row {idx+2}: {str(e)}")
                    
                    # Check if this result already exists
                    existing = LotteryResult.query.filter_by(
                        lottery_type=lottery_type,
                        draw_number=draw_number
                    ).first()
                    
                    if existing:
                        logger.info(f"Updating existing result for {lottery_type} draw {draw_number}")
                        existing.draw_date = draw_date
                        existing.numbers = json.dumps(numbers)
                        existing.bonus_numbers = json.dumps(bonus_numbers) if bonus_numbers else None
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
                            numbers=json.dumps(numbers),
                            bonus_numbers=json.dumps(bonus_numbers) if bonus_numbers else None,
                            divisions=json.dumps(divisions) if divisions else None,
                            source_url="imported-from-excel",
                            ocr_provider="manual-import",
                            ocr_model="excel-spreadsheet",
                            ocr_timestamp=datetime.utcnow().isoformat()
                        )
                        db.session.add(new_result)
                    
                    # Commit each result individually to avoid losing all data if one fails
                    db.session.commit()
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
            
            return True
    except Exception as e:
        logger.error(f"Error during import operation: {str(e)}")
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