"""
Script to import the latest lottery results from the structured text data.
This script extracts data from a formatted text string and updates the database.
"""
import re
import json
import logging
from datetime import datetime
from flask import Flask
import pandas as pd
import io
from dateutil import parser
from models import db, LotteryResult, ImportHistory, ImportedRecord

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def parse_text_data(text_data):
    """
    Parse structured text data into a pandas DataFrame
    
    Args:
        text_data (str): Formatted text data containing lottery results
        
    Returns:
        pandas.DataFrame: DataFrame containing parsed lottery data
    """
    # Split text by lines and find where the table data starts (after "Sheet 1: Lottery Games")
    lines = text_data.strip().split('\n')
    
    start_idx = 0
    for i, line in enumerate(lines):
        if "Game Name\tDraw Number\tDraw Date" in line:
            start_idx = i
            break
    
    if start_idx == 0:
        raise ValueError("Could not find table header in the data")
    
    # Extract header and data rows
    header_line = lines[start_idx]
    data_lines = lines[start_idx+1:]
    
    # Create a list of dictionaries (each dict = one row)
    data_rows = []
    
    # Process each data line
    for line in data_lines:
        if not line.strip():
            continue
            
        # Split by tabs
        fields = line.split('\t')
        if len(fields) < 10:  # Basic validation - need at least game, draw, date, numbers
            logger.warning(f"Skipping line with insufficient fields: {line}")
            continue
            
        # Create entry with basic fields
        try:
            lottery_type = fields[0]
            draw_number = fields[1]
            draw_date_str = fields[2]
            
            # Parse date
            try:
                draw_date = parser.parse(draw_date_str)
            except Exception as e:
                logger.error(f"Error parsing date {draw_date_str}: {e}")
                continue
                
            # Extract winning numbers as a list (skip any empty cells)
            winning_numbers_str = fields[3]
            winning_numbers = [num.strip() for num in winning_numbers_str.split() if num.strip()]
            
            # Extract bonus number
            bonus_number = fields[4].strip() if len(fields) > 4 else ""
            bonus_numbers = [bonus_number] if bonus_number else []
            
            # Extract prize division information
            divisions = {}
            
            # Extract prize divisions (assuming fields are in order)
            # We need to capture 3 fields per division: description, winners, winnings
            div_idx = 5  # Starting index for Division 1 Description
            for div_num in range(1, 9):  # Assuming 8 divisions
                if div_idx + 2 >= len(fields):
                    break
                    
                try:
                    div_desc = fields[div_idx].strip()
                    div_winners = fields[div_idx + 1].strip()
                    div_winnings = fields[div_idx + 2].strip()
                    
                    # Skip if any of the fields is "Data N/A"
                    if "Data N/A" in (div_desc, div_winners, div_winnings):
                        div_idx += 3
                        continue
                        
                    # Only add if we have a description
                    if div_desc:
                        divisions[f"division_{div_num}"] = {
                            "description": div_desc,
                            "winners": div_winners,
                            "prize": div_winnings
                        }
                except IndexError:
                    # Reached the end of the fields
                    break
                    
                div_idx += 3
            
            # Create the data row
            data_row = {
                "lottery_type": lottery_type,
                "draw_number": draw_number,
                "draw_date": draw_date,
                "numbers": winning_numbers,
                "bonus_numbers": bonus_numbers,
                "divisions": divisions,
            }
            
            data_rows.append(data_row)
            
        except Exception as e:
            logger.error(f"Error processing line: {e}")
            logger.error(f"Line content: {line}")
            continue
    
    return data_rows

def import_latest_results(text_data, flask_app=None):
    """
    Import latest lottery results from text data into the database
    
    Args:
        text_data (str): Formatted text data containing lottery results
        flask_app (Flask, optional): Flask application instance
        
    Returns:
        dict: Import statistics
    """
    if flask_app is None:
        from main import app
        flask_app = app
    
    with flask_app.app_context():
        stats = {
            "success": True,
            "total_processed": 0,
            "imported": 0,
            "updated": 0,
            "errors": 0,
            "by_lottery_type": {},
            "imported_records": []
        }
        
        try:
            # Parse the text data into a list of dictionaries
            data_rows = parse_text_data(text_data)
            
            # Create import history record
            import_history = ImportHistory(
                import_type='text_import',
                file_name='latest_results_text.txt',
                records_added=0,
                records_updated=0,
                errors=0,
                total_processed=len(data_rows)
            )
            db.session.add(import_history)
            db.session.commit()
            
            logger.info(f"Created import history record with ID {import_history.id}")
            
            # Process each parsed row
            for row in data_rows:
                stats["total_processed"] += 1
                
                try:
                    lottery_type = row["lottery_type"]
                    draw_number = row["draw_number"]
                    draw_date = row["draw_date"]
                    
                    # Check if this record already exists
                    existing_result = LotteryResult.query.filter_by(
                        lottery_type=lottery_type,
                        draw_number=draw_number
                    ).first()
                    
                    # Prepare data for database
                    numbers_json = json.dumps(row["numbers"])
                    bonus_numbers_json = json.dumps(row["bonus_numbers"])
                    divisions_json = json.dumps(row["divisions"])
                    
                    # Add to lottery type stats
                    if lottery_type not in stats["by_lottery_type"]:
                        stats["by_lottery_type"][lottery_type] = 0
                    stats["by_lottery_type"][lottery_type] += 1
                    
                    is_new = False
                    
                    if existing_result:
                        # Update existing record
                        existing_result.draw_date = draw_date
                        existing_result.numbers = numbers_json
                        existing_result.bonus_numbers = bonus_numbers_json
                        existing_result.divisions = divisions_json
                        db.session.commit()
                        
                        stats["updated"] += 1
                        logger.info(f"Updated existing {lottery_type} draw {draw_number}")
                        lottery_result_id = existing_result.id
                    else:
                        # Create new record
                        new_result = LotteryResult(
                            lottery_type=lottery_type,
                            draw_number=draw_number,
                            draw_date=draw_date,
                            numbers=numbers_json,
                            bonus_numbers=bonus_numbers_json,
                            divisions=divisions_json,
                            source_url="imported_from_text_data"
                        )
                        db.session.add(new_result)
                        db.session.commit()
                        
                        stats["imported"] += 1
                        is_new = True
                        logger.info(f"Imported new {lottery_type} draw {draw_number}")
                        lottery_result_id = new_result.id
                    
                    # Add entry to imported records
                    imported_record = ImportedRecord(
                        import_id=import_history.id,
                        lottery_type=lottery_type,
                        draw_number=draw_number,
                        draw_date=draw_date,
                        is_new=is_new,
                        lottery_result_id=lottery_result_id
                    )
                    db.session.add(imported_record)
                    
                    # Add to list of imported records
                    stats["imported_records"].append({
                        "lottery_type": lottery_type,
                        "draw_number": draw_number,
                        "draw_date": draw_date.isoformat(),
                        "is_new": is_new,
                        "lottery_result_id": lottery_result_id
                    })
                    
                except Exception as e:
                    logger.error(f"Error processing row {row}: {str(e)}")
                    stats["errors"] += 1
            
            # Update import history with results
            import_history.records_added = stats["imported"]
            import_history.records_updated = stats["updated"]
            import_history.errors = stats["errors"]
            
            # Commit changes
            db.session.commit()
            
            logger.info(f"Import completed. Stats: {stats}")
            return stats
        
        except Exception as e:
            logger.exception(f"Import failed: {str(e)}")
            return {
                "success": False,
                "message": f"Import failed: {str(e)}",
                "total_processed": 0,
                "imported": 0,
                "updated": 0,
                "errors": 1
            }

if __name__ == "__main__":
    from main import app
    import sys
    
    if len(sys.argv) != 2:
        print("Usage: python import_latest_results.py <text_file_path>")
        sys.exit(1)
    
    file_path = sys.argv[1]
    
    try:
        with open(file_path, 'r') as f:
            text_data = f.read()
            
        result = import_latest_results(text_data, app)
        print(f"Import result: {result}")
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)