"""
Enhanced lottery data import script with enforced draw ID integrity
This script ensures that related lottery games (drawn together) maintain consistent draw IDs
"""
import json
import logging
import sys
from datetime import datetime
from dateutil import parser
from flask import Flask
from main import app, db
from models import LotteryResult, ImportHistory, ImportedRecord

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Define related lottery games that must share the same draw ID
LOTTERY_GROUPS = {
    'lottery': ['Lottery', 'Lottery Plus 1', 'Lottery Plus 2'],
    'powerball': ['Powerball', 'Powerball Plus']
}

# Reverse mapping to quickly identify which group a lottery type belongs to
LOTTERY_TYPE_TO_GROUP = {}
for group_name, lottery_types in LOTTERY_GROUPS.items():
    for lottery_type in lottery_types:
        LOTTERY_TYPE_TO_GROUP[lottery_type] = group_name

def parse_text_data(text_data):
    """
    Parse structured text data into a list of data dictionaries
    
    Args:
        text_data (str): Formatted text data containing lottery results
        
    Returns:
        list: List of dictionaries containing parsed lottery data
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

def get_draw_date_for_group(lottery_type, draw_date):
    """
    For a given lottery type and draw date, find other draws in the same group 
    from a similar time period to ensure consistent draw IDs
    
    Args:
        lottery_type (str): The lottery type
        draw_date (datetime): The draw date
        
    Returns:
        datetime: The standardized draw date for the group
    """
    # Get the group this lottery type belongs to
    group = LOTTERY_TYPE_TO_GROUP.get(lottery_type)
    if not group:
        return draw_date
        
    # For this group, find the most recent draw date that's not in the future
    # compared to the provided draw_date
    latest_draw = None
    
    # Look within a 3-day window to find related draws
    date_range = 3  # days
    
    # Find draws in the same group from around the same date
    for related_type in LOTTERY_GROUPS[group]:
        recent_draws = LotteryResult.query.filter(
            LotteryResult.lottery_type == related_type,
            LotteryResult.draw_date >= draw_date.replace(hour=0, minute=0, second=0, microsecond=0),
            LotteryResult.draw_date <= draw_date.replace(hour=23, minute=59, second=59, microsecond=999999)
        ).order_by(LotteryResult.draw_date.desc()).all()
        
        if recent_draws:
            for draw in recent_draws:
                if latest_draw is None or draw.draw_date > latest_draw:
                    latest_draw = draw.draw_date
    
    return latest_draw or draw_date

def get_draw_number_for_group(lottery_type, draw_date):
    """
    For a given lottery type and draw date, find the correct draw number
    to use based on other draws in the same group
    
    Args:
        lottery_type (str): The lottery type
        draw_date (datetime): The draw date
        
    Returns:
        str: The draw number to use, or None if not found
    """
    # Get the group this lottery type belongs to
    group = LOTTERY_TYPE_TO_GROUP.get(lottery_type)
    if not group:
        return None
        
    # For this group, find draws on the same date
    same_day_draws = {}
    
    # Find draws in the same group from the same date
    for related_type in LOTTERY_GROUPS[group]:
        draws = LotteryResult.query.filter(
            LotteryResult.lottery_type == related_type,
            LotteryResult.draw_date >= draw_date.replace(hour=0, minute=0, second=0, microsecond=0),
            LotteryResult.draw_date <= draw_date.replace(hour=23, minute=59, second=59, microsecond=999999)
        ).all()
        
        for draw in draws:
            same_day_draws[related_type] = draw.draw_number
    
    if same_day_draws:
        # Return the first draw number found
        for type_name, draw_num in same_day_draws.items():
            logger.info(f"Using existing draw number {draw_num} from {type_name} for {lottery_type}")
            return draw_num
    
    return None

def import_latest_results(text_data):
    """
    Import latest lottery results from text data into the database,
    enforcing draw ID consistency between related lottery games
    
    Args:
        text_data (str): Formatted text data containing lottery results
        
    Returns:
        dict: Import statistics
    """
    with app.app_context():
        stats = {
            "success": True,
            "total_processed": 0,
            "imported": 0,
            "updated": 0,
            "errors": 0,
            "fixed_relationships": 0,
            "by_lottery_type": {},
            "imported_records": []
        }
        
        try:
            # Parse the text data into a list of dictionaries
            data_rows = parse_text_data(text_data)
            
            # Create import history record
            import_history = ImportHistory(
                import_type='integrity_text_import',
                file_name='latest_results_text.txt',
                records_added=0,
                records_updated=0,
                errors=0,
                total_processed=len(data_rows)
            )
            db.session.add(import_history)
            db.session.commit()
            
            logger.info(f"Created import history record with ID {import_history.id}")
            
            # Group data rows by draw date to process related draws together
            grouped_rows = {}
            for row in data_rows:
                lottery_type = row["lottery_type"]
                draw_date = row["draw_date"]
                
                # Get the lottery group (if any)
                group = LOTTERY_TYPE_TO_GROUP.get(lottery_type)
                if group:
                    date_key = draw_date.strftime('%Y-%m-%d')
                    if date_key not in grouped_rows:
                        grouped_rows[date_key] = {}
                    if group not in grouped_rows[date_key]:
                        grouped_rows[date_key][group] = []
                    grouped_rows[date_key][group].append(row)
                else:
                    # Handle non-grouped lottery types separately
                    date_key = draw_date.strftime('%Y-%m-%d')
                    if date_key not in grouped_rows:
                        grouped_rows[date_key] = {}
                    if 'other' not in grouped_rows[date_key]:
                        grouped_rows[date_key]['other'] = []
                    grouped_rows[date_key]['other'].append(row)
            
            # Process data by groups and dates
            for date_key, groups in grouped_rows.items():
                # Process each lottery group separately
                for group_name, rows in groups.items():
                    if group_name == 'other':
                        # Process non-grouped lottery types normally
                        for row in rows:
                            process_single_row(row, stats, import_history)
                    else:
                        # Process grouped lottery types together
                        process_group_rows(group_name, rows, stats, import_history)
            
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

def process_single_row(row, stats, import_history):
    """
    Process a single data row (for non-grouped lottery types)
    
    Args:
        row (dict): Data row to process
        stats (dict): Statistics dictionary to update
        import_history (ImportHistory): Import history record
    """
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

def process_group_rows(group_name, rows, stats, import_history):
    """
    Process a group of related lottery draws together to ensure consistent draw IDs
    
    Args:
        group_name (str): The name of the lottery group
        rows (list): List of data rows for this group
        stats (dict): Statistics dictionary to update
        import_history (ImportHistory): Import history record
    """
    # First check if any of the rows already have a record in the database
    # If so, use that draw number for all rows in the group
    common_draw_number = None
    common_draw_date = None
    
    # Sort rows by lottery type to ensure consistent processing order
    rows.sort(key=lambda x: x["lottery_type"])
    
    # Try to find an existing draw number from the database
    for row in rows:
        lottery_type = row["lottery_type"]
        draw_date = row["draw_date"]
        
        # Find if there's already a draw number for this lottery type on this date
        existing_draw_number = get_draw_number_for_group(lottery_type, draw_date)
        if existing_draw_number:
            common_draw_number = existing_draw_number
            common_draw_date = get_draw_date_for_group(lottery_type, draw_date)
            logger.info(f"Found existing draw {common_draw_number} for {lottery_type} on {common_draw_date}")
            break
    
    # If no existing draw number was found, use the first one from the data
    if common_draw_number is None:
        # Use the first row's draw number as the common one
        common_draw_number = rows[0]["draw_number"]
        common_draw_date = rows[0]["draw_date"]
        logger.info(f"Using draw number {common_draw_number} from {rows[0]['lottery_type']} as the common draw number")
    
    # Now process all rows with the common draw number
    for row in rows:
        stats["total_processed"] += 1
        
        try:
            lottery_type = row["lottery_type"]
            original_draw_number = row["draw_number"]
            
            # Use the common draw number for all rows in this group
            if original_draw_number != common_draw_number:
                logger.info(f"Fixing draw number for {lottery_type}: {original_draw_number} -> {common_draw_number}")
                row["draw_number"] = common_draw_number
                stats["fixed_relationships"] += 1
            
            # Use the common draw date for better consistency
            row["draw_date"] = common_draw_date
            
            # Check if this record already exists with the common draw number
            existing_result = LotteryResult.query.filter_by(
                lottery_type=lottery_type,
                draw_number=common_draw_number
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
                existing_result.draw_date = common_draw_date
                existing_result.numbers = numbers_json
                existing_result.bonus_numbers = bonus_numbers_json
                existing_result.divisions = divisions_json
                db.session.commit()
                
                stats["updated"] += 1
                logger.info(f"Updated existing {lottery_type} draw {common_draw_number}")
                lottery_result_id = existing_result.id
            else:
                # Create new record
                new_result = LotteryResult(
                    lottery_type=lottery_type,
                    draw_number=common_draw_number,
                    draw_date=common_draw_date,
                    numbers=numbers_json,
                    bonus_numbers=bonus_numbers_json,
                    divisions=divisions_json,
                    source_url="imported_from_text_data"
                )
                db.session.add(new_result)
                db.session.commit()
                
                stats["imported"] += 1
                is_new = True
                logger.info(f"Imported new {lottery_type} draw {common_draw_number}")
                lottery_result_id = new_result.id
            
            # Add entry to imported records
            imported_record = ImportedRecord(
                import_id=import_history.id,
                lottery_type=lottery_type,
                draw_number=common_draw_number,
                draw_date=common_draw_date,
                is_new=is_new,
                lottery_result_id=lottery_result_id
            )
            db.session.add(imported_record)
            
            # Add to list of imported records
            stats["imported_records"].append({
                "lottery_type": lottery_type,
                "draw_number": common_draw_number,
                "draw_date": common_draw_date.isoformat(),
                "is_new": is_new,
                "lottery_result_id": lottery_result_id
            })
            
        except Exception as e:
            logger.error(f"Error processing row {row}: {str(e)}")
            stats["errors"] += 1

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python integrity_import.py <text_file_path>")
        sys.exit(1)
    
    file_path = sys.argv[1]
    
    try:
        with open(file_path, 'r') as f:
            text_data = f.read()
            
        result = import_latest_results(text_data)
        print(f"Import result: {result}")
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)