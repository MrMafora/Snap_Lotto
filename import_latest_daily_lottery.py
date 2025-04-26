"""
Script to import the latest Daily Lottery data from the newest spreadsheet.
This will specifically target the Daily Lottery records from the mixed sheet.
"""
import os
import sys
import pandas as pd
import logging
from datetime import datetime
from flask import Flask
from models import db, LotteryResult, ImportHistory
import json

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def import_daily_lottery_data(filepath):
    """Import Daily Lottery data from the specified Excel file."""
    try:
        # Read the Excel file
        logger.info(f"Reading Excel file: {filepath}")
        
        # Check if the file exists
        if not os.path.exists(filepath):
            logger.error(f"File does not exist: {filepath}")
            return {
                "success": False,
                "message": f"File not found: {filepath}",
                "imported_count": 0,
                "errors": []
            }
        
        # Load the Excel file
        df = pd.read_excel(filepath)
        
        # Filter to only Daily Lottery records
        daily_lottery_df = df[df['Game Name'] == 'Daily Lottery']
        
        if daily_lottery_df.empty:
            logger.error("No Daily Lottery data found in the spreadsheet")
            return {
                "success": False,
                "message": "No Daily Lottery data found in the spreadsheet",
                "imported_count": 0,
                "errors": []
            }
        
        logger.info(f"Found {len(daily_lottery_df)} Daily Lottery records")
        
        # Create Flask app and context for database operations
        app = Flask(__name__)
        app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL")
        app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
        app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
            "pool_recycle": 300,
            "pool_pre_ping": True,
        }
        db.init_app(app)
        
        # Create import history record
        import_history = ImportHistory(
            file_name=os.path.basename(filepath),
            import_date=datetime.now(),
            import_type="daily_lottery_update"
        )
        
        imported_count = 0
        errors = []
        
        with app.app_context():
            # Save the import history record
            db.session.add(import_history)
            db.session.commit()
            import_history_id = import_history.id
            
            # Process each Daily Lottery record
            for _, row in daily_lottery_df.iterrows():
                try:
                    draw_number = str(row['Draw Number'])
                    draw_date = row['Draw Date']
                    
                    # Skip rows with missing essential data
                    if pd.isna(draw_number) or pd.isna(draw_date):
                        continue
                    
                    # Extract the winning numbers from the "Winning Numbers (Numerical)" column
                    winning_numbers_str = row['Winning Numbers (Numerical)']
                    if pd.isna(winning_numbers_str):
                        errors.append(f"Draw {draw_number}: Missing winning numbers")
                        continue
                        
                    # Parse the numbers from the string
                    try:
                        # The winning numbers might be in different formats, try to handle them all
                        numbers_str = str(winning_numbers_str).strip()
                        
                        # Check for comma-separated format
                        if ',' in numbers_str:
                            numbers = [int(n.strip()) for n in numbers_str.split(',')]
                        # Check for space-separated format
                        elif ' ' in numbers_str:
                            numbers = [int(n.strip()) for n in numbers_str.split()]
                        # Try to extract digits if it's a single string
                        else:
                            # Handle single string of digits like "12345" -> [1,2,3,4,5]
                            numbers = [int(n) for n in numbers_str.replace(' ', '')]
                    except Exception as e:
                        logger.error(f"Error parsing winning numbers '{winning_numbers_str}': {e}")
                        errors.append(f"Draw {draw_number}: Error parsing winning numbers '{winning_numbers_str}'")
                        continue
                    
                    # Daily Lottery should have 5 numbers
                    if len(numbers) != 5:
                        logger.error(f"Draw {draw_number}: Expected 5 numbers, got {len(numbers)}: {numbers}")
                        errors.append(f"Draw {draw_number}: Expected 5 numbers, got {len(numbers)}: {numbers}")
                        continue
                    
                    # Extract division data (prize information) using the correct column names
                    divisions = {}
                    
                    # Daily Lottery has 4 divisions
                    for div in range(1, 5):
                        winners_col = f'Div {div} Winners'
                        prize_col = f'Div {div} Winnings'
                        
                        # Add division data if both winners and prize data exist
                        if winners_col in row and prize_col in row and not pd.isna(row[winners_col]) and not pd.isna(row[prize_col]):
                            divisions[f"Division {div}"] = {
                                "winners": str(row[winners_col]).replace("R", ""),
                                "prize": str(row[prize_col])
                                    if "R" in str(row[prize_col]) 
                                    else f"R{row[prize_col]}" if not pd.isna(row[prize_col]) else "",
                                "match": "" # We don't have match information in this spreadsheet
                            }
                    
                    # Check if this draw already exists
                    existing_result = LotteryResult.query.filter_by(
                        lottery_type="Daily Lottery",
                        draw_number=draw_number
                    ).first()
                    
                    if existing_result:
                        # Update existing record
                        existing_result.numbers = json.dumps(numbers)
                        existing_result.divisions = json.dumps(divisions)
                        logger.info(f"Updated existing Draw {draw_number}")
                    else:
                        # Create new record
                        new_result = LotteryResult(
                            lottery_type="Daily Lottery",
                            draw_number=draw_number,
                            draw_date=draw_date,
                            numbers=json.dumps(numbers),
                            bonus_numbers=json.dumps([]),
                            divisions=json.dumps(divisions),
                            source_url="imported-from-excel",
                            ocr_provider="manual-import",
                            ocr_model="excel-spreadsheet",
                            ocr_timestamp=datetime.now()
                        )
                        db.session.add(new_result)
                        logger.info(f"Added new Draw {draw_number}")
                    
                    imported_count += 1
                    
                except Exception as e:
                    error_msg = f"Error processing row {draw_number}: {str(e)}"
                    logger.error(error_msg)
                    errors.append(error_msg)
            
            # Update import history with results
            import_history.records_added = imported_count
            import_history.records_updated = 0
            import_history.total_processed = imported_count
            import_history.errors = len(errors)
            
            # Commit all changes
            db.session.commit()
            
            return {
                "success": True,
                "message": f"Imported {imported_count} Daily Lottery records with {len(errors)} errors",
                "imported_count": imported_count,
                "errors": errors,
                "import_history_id": import_history_id
            }
    
    except Exception as e:
        logger.exception(f"Import failed: {str(e)}")
        return {
            "success": False,
            "message": f"Import failed: {str(e)}",
            "imported_count": 0,
            "errors": [str(e)]
        }

if __name__ == "__main__":
    # Get the filename from command-line arguments or use default
    if len(sys.argv) > 1:
        filepath = sys.argv[1]
    else:
        filepath = "attached_assets/lottery_data_template_20250426_012917.xlsx"
    
    result = import_daily_lottery_data(filepath)
    print(json.dumps(result, indent=2))