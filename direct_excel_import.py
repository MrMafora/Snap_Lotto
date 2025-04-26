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
    
    # Convert to uppercase for case-insensitive matching
    upper_type = str(lottery_type).upper()
    
    # Prioritize "Lottery" terminology
    if upper_type == 'LOTTO' or upper_type == 'LOTTERY':
        return 'Lottery'
    elif 'LOTTERY PLUS 1' in upper_type or 'LOTTO PLUS 1' in upper_type:
        return 'Lottery Plus 1'
    elif 'LOTTERY PLUS 2' in upper_type or 'LOTTO PLUS 2' in upper_type:
        return 'Lottery Plus 2' 
    elif 'POWERBALL PLUS' in upper_type:
        return 'Powerball Plus'
    elif 'POWERBALL' in upper_type:
        return 'Powerball'
    elif 'DAILY LOTTERY' in upper_type or 'DAILY LOTTO' in upper_type:
        return 'Daily Lottery'
        
    # If no match, return original with proper capitalization
    return str(lottery_type).strip()

def direct_excel_import(excel_path, app):
    """
    Directly import Excel data into database without any intermediary services.
    
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
            
            # Get list of sheets in Excel file
            xlsx = pd.ExcelFile(excel_path)
            sheets = [sheet for sheet in xlsx.sheet_names if sheet.lower() not in ['instructions', 'info', 'readme']]
            
            logger.info(f"Processing Excel file: {excel_path}")
            logger.info(f"Found {len(sheets)} sheets: {', '.join(sheets)}")
            
            # Process each sheet
            for sheet in sheets:
                try:
                    logger.info(f"Processing sheet: {sheet}")
                    
                    # Try to determine lottery type from sheet name
                    sheet_lottery_type = normalize_lottery_type(sheet)
                    logger.info(f"Sheet name suggests lottery type: {sheet_lottery_type}")
                    
                    # Read sheet
                    df = pd.read_excel(excel_path, sheet_name=sheet)
                    
                    # Skip empty sheets
                    if df.empty:
                        logger.info(f"Sheet {sheet} is empty, skipping")
                        continue
                    
                    # Replace NaN with None
                    df = df.replace({pd.NA: None})
                    
                    # Process rows
                    sheet_stats = {
                        "processed": 0,
                        "updated": 0,
                        "new": 0,
                        "errors": 0
                    }
                    
                    for index, row in df.iterrows():
                        try:
                            # Skip rows with insufficient data
                            if pd.isna(row.get('Game Name')) or pd.isna(row.get('Draw Number')):
                                continue
                            
                            # Get lottery type - prefer from data, fallback to sheet name
                            if not pd.isna(row.get('Game Name')):
                                lottery_type = normalize_lottery_type(row['Game Name'])
                            else:
                                lottery_type = sheet_lottery_type
                            
                            # Get draw number
                            draw_number = str(row['Draw Number'])
                            
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
                                        draw_date = datetime.strptime(str(row['Draw Date']).split()[0], "%Y-%m-%d")
                                    except:
                                        try:
                                            draw_date = datetime.strptime(str(row['Draw Date']).split()[0], "%d-%m-%Y")
                                        except:
                                            draw_date = datetime.utcnow()
                            else:
                                draw_date = datetime.utcnow()
                            
                            # Parse winning numbers - accommodate both "Winning Numbers" and "Winning Numbers (Numerical)" column names
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
                            
                            # Parse divisions - check various column naming patterns
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
                            
                            # Skip if missing essential data
                            if not lottery_type or not draw_number or not numbers:
                                logger.warning(f"Skipping row {index} - missing essential data")
                                continue
                            
                            # Check if already exists
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
                            
                            # Create JSON strings
                            numbers_json = json.dumps(numbers)
                            bonus_numbers_json = json.dumps(bonus_numbers) if bonus_numbers else None
                            divisions_json = json.dumps(divisions) if divisions else None
                            
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
                                sheet_stats["updated"] += 1
                                
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
                                sheet_stats["new"] += 1
                                
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
                            sheet_stats["processed"] += 1
                            
                            # Commit every few rows to avoid large transactions
                            if sheet_stats["processed"] % 10 == 0:
                                db.session.commit()
                            
                        except Exception as e:
                            logger.error(f"Error processing row {index}: {str(e)}")
                            stats["errors"] += 1
                            stats["lottery_types"][lottery_type]["errors"] += 1
                            sheet_stats["errors"] += 1
                    
                    # Commit remaining changes
                    db.session.commit()
                    
                    # Log sheet statistics
                    logger.info(f"Sheet {sheet} stats: {sheet_stats['processed']} processed, "
                               f"{sheet_stats['new']} new, {sheet_stats['updated']} updated, "
                               f"{sheet_stats['errors']} errors")
                    
                    stats["sheets_processed"] += 1
                    
                except Exception as e:
                    logger.error(f"Error processing sheet {sheet}: {str(e)}")
                    stats["errors"] += 1
            
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
    stats = direct_excel_import(file_path, app)
    
    # Print summary
    print("\n=== IMPORT SUMMARY ===")
    print(f"Total processed: {stats['total_processed']}")
    print(f"Sheets processed: {stats['sheets_processed']}")
    print(f"New records: {stats['new_records']}")
    print(f"Updated records: {stats['updated_records']}")
    print(f"Errors: {stats['errors']}")
    print("\nBy lottery type:")
    for lottery_type, type_stats in stats['lottery_types'].items():
        print(f"  {lottery_type}: {type_stats['processed']} processed "
             f"({type_stats['new']} new, {type_stats['updated']} updated, "
             f"{type_stats['errors']} errors)")