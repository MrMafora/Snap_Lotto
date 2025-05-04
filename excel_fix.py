#!/usr/bin/env python
"""
Critical fix for Excel import issues.
This script manually applies the fix we need to ensure row 2 (index 1) data is properly imported.
"""

import os
import sys
import logging
import pandas as pd
import json
from datetime import datetime
from models import db, LotteryResult

# Set up logging
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def fix_excel_import():
    """Directly apply the fix to ensure row 2 is imported"""
    # Find the most recent Excel file
    excel_files = []
    directory = "attached_assets"
    pattern = "lottery_data_"
    
    for filename in os.listdir(directory):
        if pattern in filename and filename.endswith(".xlsx"):
            excel_files.append(os.path.join(directory, filename))
    
    if not excel_files:
        logger.error("No Excel files found")
        return False
    
    # Use the most recent file
    latest_file = max(excel_files, key=os.path.getmtime)
    logger.info(f"Using most recent file: {latest_file}")
    
    try:
        # Read the Excel file
        df_raw = pd.read_excel(latest_file)
        logger.info(f"Excel has {len(df_raw)} rows total")
        
        # Get the first row (Excel row 2, index 1) which is typically missed
        if len(df_raw) < 1:
            logger.error("Excel file has no data rows")
            return False
        
        # Get the first row data (the one that's usually missed)
        row_1 = df_raw.iloc[0]
        
        # Extract essential data
        game_name = row_1['Game Name']
        draw_number = str(row_1['Draw Number']).strip()
        draw_date = row_1['Draw Date']
        winning_numbers = row_1['Winning Numbers (Numerical)']
        bonus_ball = row_1['Bonus Ball'] if 'Bonus Ball' in row_1 else None
        
        logger.info(f"Found critical row data: Game={game_name}, Draw={draw_number}, Date={draw_date}")
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
        
        # Parse numbers
        if isinstance(winning_numbers, str):
            numbers = [int(num.strip()) for num in winning_numbers.split() if num.strip().isdigit()]
        else:
            numbers = []
            
        # Parse bonus ball
        if pd.isna(bonus_ball):
            bonus_numbers = []
        elif isinstance(bonus_ball, (int, float)):
            bonus_numbers = [int(bonus_ball)]
        else:
            bonus_numbers = []
        
        # Build divisions structure
        divisions = {}
        for i in range(1, 9):
            winners_col = f'Div {i} Winners'
            prize_col = f'Div {i} Winnings'
            
            if winners_col in row_1 and prize_col in row_1 and not pd.isna(row_1[winners_col]) and not pd.isna(row_1[prize_col]):
                divisions[f"Division {i}"] = {
                    "winners": str(int(row_1[winners_col]) if isinstance(row_1[winners_col], (int, float)) else row_1[winners_col]),
                    "prize": row_1[prize_col] if isinstance(row_1[prize_col], str) else f"R{row_1[prize_col]}"
                }
        
        # Check if we have valid data
        if not lottery_type or not draw_number or not draw_date or not numbers:
            logger.error("Missing critical data in row 1")
            return False
            
        # Check if this result already exists in the database
        from flask import current_app
        with current_app.app_context():
            existing = LotteryResult.query.filter_by(
                lottery_type=lottery_type,
                draw_number=draw_number
            ).first()
            
            if existing:
                logger.info(f"Row 1 draw {draw_number} already exists in database")
            else:
                logger.info(f"Creating new entry for row 1 draw {draw_number}")
                # Create new result
                new_result = LotteryResult(
                    lottery_type=lottery_type,
                    draw_number=draw_number,
                    draw_date=draw_date,
                    numbers=json.dumps(numbers),
                    bonus_numbers=json.dumps(bonus_numbers) if bonus_numbers else None,
                    divisions=json.dumps(divisions) if divisions else None,
                    source_url="manual-row2-fix",
                    ocr_provider="manual-row2-fix",
                    ocr_model="excel-direct-access",
                    ocr_timestamp=datetime.utcnow().isoformat()
                )
                db.session.add(new_result)
                db.session.commit()
                logger.info(f"Successfully added missing row 1 (draw {draw_number})")
        
        return True
    except Exception as e:
        logger.error(f"Error applying Excel fix: {str(e)}")
        return False

if __name__ == "__main__":
    print("This script must be run from a Flask context")
    print("Please use the /fix-excel-import route to apply this fix")