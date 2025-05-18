#!/usr/bin/env python3
"""
Simple script to fix lottery draw IDs in the database.
"""

import os
import sys
import json
from datetime import datetime
import logging
from sqlalchemy import text

# Import app and database
try:
    from main import app, db
    from models import LotteryResult
except ImportError:
    print("Could not import app or models. Make sure you're in the right directory.")
    sys.exit(1)

# Configure logging
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('draw_id_fix')

# Direct SQL commands to execute
SQL_COMMANDS = [
    "UPDATE lottery_result SET draw_number = '2542' WHERE lottery_type = 'Lottery' AND draw_number = '2642'",
    "UPDATE lottery_result SET draw_number = '2541' WHERE lottery_type = 'Lottery' AND draw_number = '2641'",
    "UPDATE lottery_result SET draw_number = '2542' WHERE lottery_type = 'Lottery Plus 1' AND draw_number = '2642'",
    "UPDATE lottery_result SET draw_number = '2541' WHERE lottery_type = 'Lottery Plus 1' AND draw_number = '2641'",
    "UPDATE lottery_result SET draw_number = '2542' WHERE lottery_type = 'Lottery Plus 2' AND draw_number = '2642'",
    "UPDATE lottery_result SET draw_number = '2541' WHERE lottery_type = 'Lottery Plus 2' AND draw_number = '2641'",
    "UPDATE lottery_result SET draw_number = '1615' WHERE lottery_type = 'Powerball' AND draw_number = '1616'",
    "UPDATE lottery_result SET draw_number = '1614' WHERE lottery_type = 'Powerball' AND draw_number = '1615'",
    "UPDATE lottery_result SET draw_number = '1615' WHERE lottery_type = 'Powerball Plus' AND draw_number = '1616'",
    "UPDATE lottery_result SET draw_number = '1614' WHERE lottery_type = 'Powerball Plus' AND draw_number = '1615'",
    "UPDATE lottery_result SET draw_number = '2256' WHERE lottery_type = 'Daily Lottery' AND draw_number = '2258'",
    "UPDATE lottery_result SET draw_number = '2255' WHERE lottery_type = 'Daily Lottery' AND draw_number = '2257'",
    "UPDATE lottery_result SET draw_number = '2254' WHERE lottery_type = 'Daily Lottery' AND draw_number = '2256'",
    "UPDATE lottery_result SET draw_number = '2253' WHERE lottery_type = 'Daily Lottery' AND draw_number = '2255'"
]

def check_current_draws():
    """Check what draw IDs exist in the database."""
    print("Current lottery draw IDs in database:")
    print("-" * 80)
    
    with app.app_context():
        # Check the draw IDs for each lottery type
        lottery_types = [
            "Lottery", "Lottery Plus 1", "Lottery Plus 2", 
            "Powerball", "Powerball Plus", "Daily Lottery"
        ]
        
        for lottery_type in lottery_types:
            # Get the most recent draw for this lottery type
            draw = LotteryResult.query.filter_by(
                lottery_type=lottery_type
            ).order_by(db.desc(LotteryResult.draw_date)).first()
            
            if draw:
                print(f"{lottery_type}: Draw #{draw.draw_number} on {draw.draw_date.strftime('%Y-%m-%d')}")
            else:
                print(f"{lottery_type}: No records found")

def fix_draw_ids():
    """Fix lottery draw IDs using direct SQL commands."""
    
    with app.app_context():
        total_fixed = 0
        for sql in SQL_COMMANDS:
            try:
                result = db.session.execute(text(sql))
                rows_affected = result.rowcount
                total_fixed += rows_affected
                print(f"Fixed {rows_affected} rows with: {sql}")
                db.session.commit()
            except Exception as e:
                db.session.rollback()
                print(f"Error executing SQL: {sql}")
                print(f"Error details: {e}")
        
        return total_fixed

def main():
    """Main function to fix lottery draw IDs."""
    try:
        print("Checking current lottery draw IDs (before fix)...")
        check_current_draws()
        
        print("\nFixing lottery draw IDs...")
        total_fixed = fix_draw_ids()
        print(f"Successfully fixed {total_fixed} lottery draw IDs.")
        
        print("\nChecking lottery draw IDs (after fix)...")
        check_current_draws()
        
    except Exception as e:
        logger.error(f"Error fixing lottery draw IDs: {e}")
        print(f"Error: {e}")

if __name__ == "__main__":
    main()