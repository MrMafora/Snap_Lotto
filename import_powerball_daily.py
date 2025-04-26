import pandas as pd
import json
import os
import logging
from datetime import datetime
import traceback
from flask import Flask
from models import db, LotteryResult, ImportHistory, ImportedRecord
import sys

# Configure logging
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def normalize_lottery_type(lottery_type):
    """
    Normalize lottery type names, prioritizing "Lottery" terminology.
    
    Args:
        lottery_type (str): The lottery type name
        
    Returns:
        str: Normalized lottery type
    """
    if not lottery_type:
        return "Unknown"
    
    # First, handle exact matches for special cases
    cleaned_type = str(lottery_type).strip()
    if cleaned_type == 'PowerBall':
        return 'Powerball'
    elif cleaned_type == 'PowerBall PLUS':
        return 'Powerball Plus'
    
    # Convert to uppercase for case-insensitive matching
    upper_type = cleaned_type.upper()
    
    # Prioritize "Lottery" terminology
    if upper_type == 'LOTTO' or upper_type == 'LOTTERY':
        return 'Lottery'
    elif 'LOTTERY PLUS 1' in upper_type or 'LOTTO PLUS 1' in upper_type:
        return 'Lottery Plus 1'
    elif 'LOTTERY PLUS 2' in upper_type or 'LOTTO PLUS 2' in upper_type:
        return 'Lottery Plus 2' 
    elif 'POWERBALL PLUS' in upper_type or 'POWERBALL PLUS' in upper_type:
        return 'Powerball Plus'
    elif 'POWERBALL' in upper_type:
        return 'Powerball'
    elif 'DAILY LOTTERY' in upper_type or 'DAILY LOTTO' in upper_type:
        return 'Daily Lottery'
        
    # If no match, return original with proper capitalization
    return cleaned_type

def import_powerball_daily_only(excel_path, app):
    """
    Import only PowerBall and Daily Lottery data from Excel.
    
    Args:
        excel_path (str): Path to Excel file
        app (Flask): Flask application instance for context
        
    Returns:
        dict: Import statistics
    """
    stats = {
        "total_processed": 0,
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
                import_type="powerball-daily-import",
                file_name=os.path.basename(excel_path),
                records_added=0,
                records_updated=0,
                total_processed=0,
                errors=0
            )
            db.session.add(import_history)
            db.session.commit()
            import_history_id = import_history.id
            
            logger.info(f"Processing Excel file for PowerBall and Daily Lottery: {excel_path}")
            
            # Read the Excel sheet
            df = pd.read_excel(excel_path, sheet_name='Lotto')
            
            # Filter for just PowerBall and Daily Lottery
            df = df[df['Game Name'].apply(lambda x: 
                                         'powerball' in str(x).lower() or 
                                         'daily' in str(x).lower())]
            
            logger.info(f"Found {len(df)} PowerBall and Daily Lottery records")
            
            # Process rows
            for index, row in df.iterrows():
                try:
                    # Get lottery type
                    lottery_type = normalize_lottery_type(row['Game Name'])
                    
                    # Skip if not PowerBall or Daily Lottery
                    if not ('powerball' in lottery_type.lower() or 'daily' in lottery_type.lower()):
                        continue
                    
                    # Get draw number
                    if pd.isna(row.get('Draw Number')):
                        logger.warning(f"Skipping row {index} - missing draw number")
                        continue
                    draw_number = str(row['Draw Number'])
                    
                    # Parse draw date
                    draw_date = None
                    if not pd.isna(row.get('Draw Date')):
                        if isinstance(row['Draw Date'], datetime):
                            draw_date = row['Draw Date']
                        else:
                            try:
                                draw_date = datetime.strptime(str(row['Draw Date']).split()[0], "%Y-%m-%d")
                            except:
                                try:
                                    draw_date = datetime.strptime(str(row['Draw Date']).split()[0], "%d-%m-%Y")
                                except:
                                    draw_date = datetime.utcnow()
                    else:
                        draw_date = datetime.utcnow()
                    
                    # Parse winning numbers
                    numbers = []
                    for col_name in ['Winning Numbers', 'Winning Numbers (Numerical)']:
                        if col_name in row and not pd.isna(row.get(col_name)):
                            nums_str = str(row[col_name])
                            for delimiter in [',', ' ', ';']:
                                if delimiter in nums_str:
                                    try:
                                        numbers = [int(n.strip()) for n in nums_str.split(delimiter) if n.strip().isdigit()]
                                        if numbers:
                                            break
                                    except:
                                        continue
                            
                            # If no delimiters worked, check if it's a single number
                            if not numbers and nums_str.strip().isdigit():
                                numbers = [int(nums_str.strip())]
                            
                            if numbers:
                                break
                    
                    # Parse bonus ball
                    bonus_numbers = []
                    if not pd.isna(row.get('Bonus Ball')):
                        bonus_str = str(row['Bonus Ball'])
                        if bonus_str.strip().isdigit():
                            bonus_numbers = [int(bonus_str.strip())]
                        else:
                            # Try to parse multiple bonus numbers
                            for delimiter in [',', ' ', ';']:
                                if delimiter in bonus_str:
                                    try:
                                        bonus_numbers = [int(n.strip()) for n in bonus_str.split(delimiter) if n.strip().isdigit()]
                                        if bonus_numbers:
                                            break
                                    except:
                                        continue
                    
                    # Parse divisions
                    divisions = {}
                    for i in range(1, 9):
                        # Check different possible column name formats
                        possible_winners_keys = [
                            f'Division {i} Winners', 
                            f'Div {i} Winners',
                            f'Div{i} Winners'
                        ]
                        possible_payout_keys = [
                            f'Division {i} Payout', 
                            f'Div {i} Winnings',
                            f'Div{i} Winnings',
                            f'Division {i} Winnings'
                        ]
                        
                        # Find matching keys that exist in the row
                        winners_key = None
                        for key in possible_winners_keys:
                            if key in row and not pd.isna(row.get(key)):
                                winners_key = key
                                break
                                
                        payout_key = None
                        for key in possible_payout_keys:
                            if key in row and not pd.isna(row.get(key)):
                                payout_key = key
                                break
                        
                        # If we found both keys, add the division
                        if winners_key and payout_key:
                            winners = str(row[winners_key])
                            payout = str(row[payout_key])
                            
                            # Format payout
                            if not payout.startswith('R'):
                                payout = f'R{payout}'
                            
                            divisions[f'Division {i}'] = {
                                'winners': winners,
                                'prize': payout
                            }
                    
                    # Skip if missing lottery type or draw number
                    if not lottery_type or not draw_number:
                        logger.warning(f"Skipping row {index} - missing lottery_type or draw_number")
                        continue
                    
                    # If we got here, we have at least lottery_type and draw_number
                    if not numbers:
                        numbers = []  # Use empty list if no numbers found
                    
                    # Update statistics
                    if lottery_type not in stats["lottery_types"]:
                        stats["lottery_types"][lottery_type] = {
                            "processed": 0,
                            "updated": 0,
                            "new": 0,
                            "errors": 0
                        }
                    
                    # Create JSON strings
                    numbers_json = json.dumps(numbers)
                    bonus_numbers_json = json.dumps(bonus_numbers) if bonus_numbers else None
                    divisions_json = json.dumps(divisions) if divisions else None
                    
                    # Check if record exists
                    existing = LotteryResult.query.filter_by(
                        lottery_type=lottery_type,
                        draw_number=draw_number
                    ).first()
                    
                    if existing:
                        # Update existing record
                        existing.draw_date = draw_date
                        existing.numbers = numbers_json
                        existing.bonus_numbers = bonus_numbers_json
                        existing.divisions = divisions_json
                        existing.source_url = "imported-from-excel"
                        existing.ocr_provider = "manual-import"
                        existing.ocr_model = "excel-spreadsheet"
                        existing.ocr_timestamp = datetime.utcnow().isoformat()
                        
                        stats["updated_records"] += 1
                        stats["lottery_types"][lottery_type]["updated"] += 1
                        
                        logger.info(f"Updated: {lottery_type} Draw {draw_number}")
                        
                        # Create imported record
                        imported_record = ImportedRecord(
                            import_id=import_history_id,
                            lottery_type=lottery_type,
                            draw_number=draw_number,
                            draw_date=draw_date,
                            is_new=False,
                            lottery_result_id=existing.id
                        )
                        db.session.add(imported_record)
                    else:
                        # Create new record
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
                        
                        stats["new_records"] += 1
                        stats["lottery_types"][lottery_type]["new"] += 1
                        
                        logger.info(f"Created: {lottery_type} Draw {draw_number}")
                        
                        # Create imported record
                        imported_record = ImportedRecord(
                            import_id=import_history_id,
                            lottery_type=lottery_type,
                            draw_number=draw_number,
                            draw_date=draw_date,
                            is_new=True,
                            lottery_result_id=new_result.id
                        )
                        db.session.add(imported_record)
                    
                    # Increment processed counters
                    stats["total_processed"] += 1
                    stats["lottery_types"][lottery_type]["processed"] += 1
                    
                    # Commit every few rows to avoid large transactions
                    if stats["total_processed"] % 10 == 0:
                        db.session.commit()
                    
                except Exception as e:
                    logger.error(f"Error processing row {index}: {str(e)}")
                    stats["errors"] += 1
                    stats["lottery_types"].setdefault(lottery_type, {"errors": 0})["errors"] += 1
            
            # Update import history
            import_history.records_added = stats["new_records"]
            import_history.records_updated = stats["updated_records"]
            import_history.errors = stats["errors"]
            import_history.total_processed = stats["total_processed"]
            db.session.commit()
            
            logger.info(f"Import completed: {stats}")
            
        except Exception as e:
            logger.error(f"Error importing Excel file: {str(e)}")
            logger.error(traceback.format_exc())
            
            # Update import history with error
            if 'import_history_id' in locals():
                import_history = ImportHistory.query.get(import_history_id)
                if import_history:
                    import_history.errors += 1
                    db.session.commit()
            
            stats["errors"] += 1
    
    return stats

if __name__ == "__main__":
    # Import app from main
    from main import app
    
    # Get file path from command line
    if len(sys.argv) > 1:
        file_path = sys.argv[1]
    else:
        file_path = "attached_assets/lottery_data_template_20250426_012917.xlsx"
    
    if not os.path.exists(file_path):
        print(f"File not found: {file_path}")
        sys.exit(1)
    
    # Import data
    stats = import_powerball_daily_only(file_path, app)
    
    # Print summary
    print("\n=== IMPORT SUMMARY ===")
    print(f"Total processed: {stats['total_processed']}")
    print(f"New records: {stats['new_records']}")
    print(f"Updated records: {stats['updated_records']}")
    print(f"Errors: {stats['errors']}")
    print("\nBy lottery type:")
    for lottery_type, type_stats in stats['lottery_types'].items():
        print(f"  {lottery_type}: {type_stats['processed']} processed "
             f"({type_stats['new']} new, {type_stats['updated']} updated, "
             f"{type_stats['errors']} errors)")