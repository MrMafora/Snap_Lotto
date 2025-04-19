#!/usr/bin/env python
"""
Script to manually add a missing Lotto draw 2534 record to the database.
This addresses the specific issue where Lotto Plus 1 and Lotto Plus 2 for draw 2534
exist in the database, but the main Lotto draw is missing.
"""

import json
from datetime import datetime
import sys

from models import db, LotteryResult
import main  # Import main to get Flask application context

# Define the winning numbers for Lotto draw 2534
# IMPORTANT: These need to be the actual winning numbers for draw 2534!
# Replace these placeholder values with the real numbers
WINNING_NUMBERS = []  # Enter the 6 winning numbers for Lotto draw 2534
BONUS_NUMBER = []     # Enter the bonus number for Lotto draw 2534

def add_lotto_2534():
    """Add Lotto draw 2534 record to the database"""
    
    # Validate input
    if not WINNING_NUMBERS or len(WINNING_NUMBERS) != 6:
        print("Error: Please provide exactly 6 winning numbers for Lotto draw 2534")
        print("Edit the WINNING_NUMBERS list in this script with the correct numbers")
        return False
    
    if not BONUS_NUMBER:
        print("Error: Please provide the bonus number for Lotto draw 2534")
        print("Edit the BONUS_NUMBER list in this script with the correct bonus number")
        return False
    
    # Use the app context
    with main.app.app_context():
        # Check if this record already exists
        existing = LotteryResult.query.filter_by(
            lottery_type='Lotto',
            draw_number='2534'
        ).first()
        
        if existing:
            print(f"Lotto draw 2534 already exists in the database (ID: {existing.id})")
            return True
        
        # The draw date should be the same as Lotto Plus 1 and Lotto Plus 2 draw 2534
        reference = LotteryResult.query.filter_by(
            lottery_type='Lotto Plus 1',
            draw_number='2534'
        ).first()
        
        if not reference:
            print("Error: Could not find reference draw (Lotto Plus 1, draw 2534)")
            return False
        
        draw_date = reference.draw_date
        
        print(f"Creating Lotto draw 2534 with date {draw_date} and numbers {WINNING_NUMBERS}")
        
        # Create the new record
        new_result = LotteryResult(
            lottery_type='Lotto',
            draw_number='2534',
            draw_date=draw_date,
            numbers=json.dumps(WINNING_NUMBERS),
            bonus_numbers=json.dumps(BONUS_NUMBER),
            divisions=None,  # We don't have division data
            source_url='manually-added',
            ocr_provider='manual-entry',
            ocr_model='script',
            ocr_timestamp=datetime.utcnow()
        )
        
        db.session.add(new_result)
        db.session.commit()
        
        print(f"Successfully added Lotto draw 2534 (ID: {new_result.id})")
        return True

if __name__ == "__main__":
    # Check if numbers are provided as command-line arguments
    if len(sys.argv) >= 7:
        # Get the main numbers from command line args
        WINNING_NUMBERS = [int(sys.argv[1]), int(sys.argv[2]), int(sys.argv[3]), 
                           int(sys.argv[4]), int(sys.argv[5]), int(sys.argv[6])]
        
        # Get the bonus number if provided
        if len(sys.argv) >= 8:
            BONUS_NUMBER = [int(sys.argv[7])]
    
    if add_lotto_2534():
        print("Operation completed successfully")
    else:
        print("Operation failed")