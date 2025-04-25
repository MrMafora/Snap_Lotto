#!/usr/bin/env python
"""
Direct fix for row 2 import issue.
This script will find the latest Excel file and directly import row 2 data.
It must be run from a Flask context.
"""

import os
import sys
import logging
import pandas as pd
import json
from datetime import datetime
import numpy as np

# Set up logging
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def direct_import_row2():
    """Directly import row 2 data from the latest Excel file"""
    # This must be run from within Flask context
    try:
        from models import db, LotteryResult, ImportHistory
        from flask import current_app
        from flask_login import current_user
        
        # Find the most recent Excel file
        excel_files = []
        for directory in ["uploads", "attached_assets"]:
            if os.path.exists(directory):
                for filename in os.listdir(directory):
                    if filename.endswith(".xlsx"):
                        excel_files.append(os.path.join(directory, filename))
        
        if not excel_files:
            logger.error("No Excel files found")
            return False
        
        # Use the most recent file
        latest_file = max(excel_files, key=os.path.getmtime)
        logger.info(f"Using most recent file: {latest_file}")
        
        # Read the Excel file - DO NOT SKIP ANY ROWS
        df_raw = pd.read_excel(latest_file)
        logger.info(f"Excel has {len(df_raw)} rows total")
        
        if len(df_raw) == 0:
            logger.error("Excel file has no data")
            return False
        
        # Specifically look at row 1 (index 0)
        row_1 = df_raw.iloc[0]
        
        # Extract essential data
        game_name = row_1['Game Name'] if 'Game Name' in row_1 else None
        
        if game_name is None:
            logger.error("Could not find 'Game Name' column in Excel file")
            return False
            
        draw_number = str(row_1['Draw Number']).strip() if 'Draw Number' in row_1 else None
        draw_date = row_1['Draw Date'] if 'Draw Date' in row_1 else None
        winning_numbers = row_1['Winning Numbers (Numerical)'] if 'Winning Numbers (Numerical)' in row_1 else None
        bonus_ball = row_1['Bonus Ball'] if 'Bonus Ball' in row_1 else None
        
        logger.info(f"Row 1 data: Game={game_name}, Draw={draw_number}, Date={draw_date}")
        logger.info(f"Numbers: {winning_numbers}, Bonus: {bonus_ball}")
        
        # Standardize lottery type
        lottery_type = str(game_name).strip()
        if lottery_type.upper() == 'LOTTO':
            lottery_type = 'Lotto'
        elif 'LOTTO PLUS 1' in lottery_type.upper():
            lottery_type = 'Lotto Plus 1'
        elif 'LOTTO PLUS 2' in lottery_type.upper():
            lottery_type = 'Lotto Plus 2'
        elif 'POWERBALL PLUS' in lottery_type.upper():
            lottery_type = 'Powerball Plus'
        elif 'POWERBALL' in lottery_type.upper():
            lottery_type = 'Powerball'
        elif 'DAILY LOTTO' in lottery_type.upper():
            lottery_type = 'Daily Lotto'
        
        logger.info(f"Standardized lottery type: {lottery_type}")
        
        # Parse numbers
        numbers = []
        if winning_numbers is not None:
            if isinstance(winning_numbers, str):
                numbers = [int(num.strip()) for num in winning_numbers.split() if num.strip().isdigit()]
            elif isinstance(winning_numbers, (int, float)) and not np.isnan(winning_numbers):
                numbers = [int(winning_numbers)]
            
        logger.info(f"Parsed numbers: {numbers}")
                
        # Parse bonus ball
        bonus_numbers = []
        if bonus_ball is not None:
            if pd.isna(bonus_ball):
                bonus_numbers = []
            elif isinstance(bonus_ball, (int, float)) and not np.isnan(bonus_ball):
                bonus_numbers = [int(bonus_ball)]
            elif isinstance(bonus_ball, str):
                bonus_numbers = [int(num.strip()) for num in bonus_ball.split() if num.strip().isdigit()]
        
        logger.info(f"Parsed bonus numbers: {bonus_numbers}")
        
        # Build divisions structure
        divisions = {}
        for i in range(1, 9):
            winners_col = f'Div {i} Winners'
            prize_col = f'Div {i} Winnings'
            
            if winners_col in row_1 and prize_col in row_1 and not pd.isna(row_1[winners_col]) and not pd.isna(row_1[prize_col]):
                winners_value = row_1[winners_col]
                prize_value = row_1[prize_col]
                
                # Ensure winners is a string
                if isinstance(winners_value, (int, float)):
                    winners_value = str(int(winners_value))
                elif isinstance(winners_value, str):
                    winners_value = winners_value.strip()
                else:
                    winners_value = "0"
                
                # Ensure prize has R prefix
                if isinstance(prize_value, str):
                    prize_value = prize_value.strip()
                    if not prize_value.startswith('R'):
                        prize_value = f"R{prize_value}"
                elif isinstance(prize_value, (int, float)):
                    prize_value = f"R{prize_value}"
                else:
                    prize_value = "R0.00"
                
                divisions[f"Division {i}"] = {
                    "winners": winners_value,
                    "prize": prize_value
                }
        
        logger.info(f"Parsed divisions: {divisions}")
        
        # Check if we have valid data
        if not lottery_type:
            logger.error("Missing lottery type")
            return False
        if not draw_number:
            logger.error("Missing draw number")
            return False
        if not draw_date:
            logger.error("Missing draw date")
            return False
        if not numbers:
            logger.error("Missing winning numbers")
            return False
            
        # Check if this result already exists
        existing = LotteryResult.query.filter_by(
            lottery_type=lottery_type,
            draw_number=draw_number
        ).first()
        
        if existing:
            logger.info(f"Row 1 (Excel row 2) draw {draw_number} already exists in database - updating")
            existing.draw_date = draw_date
            existing.numbers = json.dumps(numbers)
            existing.bonus_numbers = json.dumps(bonus_numbers) if bonus_numbers else None
            existing.divisions = json.dumps(divisions) if divisions else None
            existing.source_url = "imported-from-excel"
            existing.ocr_provider = "manual-import"
            existing.ocr_model = "excel-spreadsheet"
            existing.ocr_timestamp = datetime.utcnow().isoformat()
            db.session.commit()
            logger.info(f"Updated existing record: {lottery_type} Draw {draw_number}")
            print(f"SUCCESS: Updated existing record: {lottery_type} Draw {draw_number}")
        else:
            logger.info(f"Creating new entry for row 1 (Excel row 2) draw {draw_number}")
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
            db.session.commit()
            logger.info(f"Created new record: {lottery_type} Draw {draw_number}")
            print(f"SUCCESS: Created new record: {lottery_type} Draw {draw_number}")
            
        # Create import history record with proper association to the imported record
        try:
            # Step 1: Create the import history record
            import_history = ImportHistory(
                import_type='Excel',
                file_name=os.path.basename(latest_file),
                records_added=1 if not existing else 0,
                records_updated=1 if existing else 0,
                total_processed=1,
                errors=0,
                user_id=1  # Admin user
            )
            db.session.add(import_history)
            db.session.commit()
            logger.info("Created import history record")
            
            # Step 2: Now create the ImportDetail records to link the history with the lottery results
            from models import ImportDetail
            
            # Get the ID of the lottery result we just imported/updated
            lottery_result_id = existing.id if existing else LotteryResult.query.filter_by(
                lottery_type=lottery_type, 
                draw_number=draw_number
            ).first().id
            
            # Create import detail record
            import_detail = ImportDetail(
                import_history_id=import_history.id,
                lottery_result_id=lottery_result_id,
                lottery_type=lottery_type,
                draw_number=draw_number,
                draw_date=draw_date,
                is_new=not existing
            )
            db.session.add(import_detail)
            db.session.commit()
            
            logger.info(f"Created import detail record linking import {import_history.id} with lottery result {lottery_result_id}")
        except Exception as e:
            logger.error(f"Error creating import history/details: {str(e)}")
        
        return True
    except Exception as e:
        logger.error(f"Error: {str(e)}")
        print(f"ERROR: {str(e)}")
        return False

# Usage script with Flask app context
if __name__ == "__main__":
    print("This script must be run from a Flask context")
    print("To run, execute the following from a Python shell:")
    print("from fix_row2 import direct_import_row2")
    print("from main import app")
    print("with app.app_context():")
    print("    direct_import_row2()")