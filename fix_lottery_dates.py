"""
Fix lottery result dates in the database.
This script updates all lottery results with future dates (2025) to use valid recent dates.
"""
import os
import sys
from datetime import datetime, timedelta
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Import the existing app and db from main.py
sys.path.append('.')
from main import app, db

# Import the models
sys.path.append('.')
from models import LotteryResult

def fix_lottery_dates():
    """
    Update all lottery results with future dates to use valid recent dates.
    We'll set them back from 2025 to 2023 to keep them realistic.
    """
    with app.app_context():
        # Find all results with dates in 2025
        future_results = LotteryResult.query.filter(
            LotteryResult.draw_date >= datetime(2024, 1, 1)
        ).all()
        
        if not future_results:
            print("No future dates found in the database.")
            return
            
        print(f"Found {len(future_results)} results with future dates.")
        
        # Create a mapping from 2025 dates to corrected dates (2 years earlier)
        for result in future_results:
            # Calculate new date (2 years earlier)
            old_date = result.draw_date
            new_date = datetime(
                year=old_date.year - 2,
                month=old_date.month,
                day=old_date.day,
                hour=old_date.hour,
                minute=old_date.minute,
                second=old_date.second
            )
            
            print(f"Updating {result.lottery_type} (Draw #{result.draw_number}) from {old_date.strftime('%Y-%m-%d')} to {new_date.strftime('%Y-%m-%d')}")
            
            # Update the result
            result.draw_date = new_date
        
        # Commit all changes
        db.session.commit()
        print(f"Successfully updated {len(future_results)} lottery results with realistic dates.")

if __name__ == "__main__":
    fix_lottery_dates()