"""
Script to fix lottery number formats in the database to ensure consistency.
This will convert all lottery numbers to string format to prevent type comparison errors.
"""
import os
import sys
import json
import logging
from datetime import datetime

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Import the necessary modules
sys.path.append('.')
from main import app, db
from models import LotteryResult

def fix_number_formats():
    """
    Fix lottery number formats in the database.
    Convert all numbers to strings to ensure consistency.
    """
    with app.app_context():
        # Get all lottery results
        results = LotteryResult.query.all()
        
        # Count variables for reporting
        total_results = len(results)
        fixed_count = 0
        already_correct = 0
        
        logger.info(f"Processing {total_results} lottery results...")
        
        # Process each result
        for result in results:
            # Handle main numbers
            needs_update = False
            
            if result.numbers:
                try:
                    # Parse the numbers
                    numbers = json.loads(result.numbers)
                    
                    # Check if conversion is needed (if any number is not a string)
                    if any(not isinstance(num, str) for num in numbers):
                        # Convert all numbers to strings
                        string_numbers = [str(num).zfill(2) for num in numbers]
                        result.numbers = json.dumps(string_numbers)
                        needs_update = True
                        logger.info(f"Fixed numbers for {result.lottery_type} (ID: {result.id}): {numbers} -> {string_numbers}")
                except (json.JSONDecodeError, TypeError) as e:
                    logger.error(f"Error parsing numbers for {result.lottery_type} (ID: {result.id}): {e}")
                    continue
            
            # Handle bonus numbers
            if result.bonus_numbers:
                try:
                    # Parse the bonus numbers
                    bonus_numbers = json.loads(result.bonus_numbers)
                    
                    # Check if conversion is needed (if any number is not a string)
                    if any(not isinstance(num, str) for num in bonus_numbers):
                        # Convert all bonus numbers to strings
                        string_bonus = [str(num).zfill(2) for num in bonus_numbers]
                        result.bonus_numbers = json.dumps(string_bonus)
                        needs_update = True
                        logger.info(f"Fixed bonus numbers for {result.lottery_type} (ID: {result.id}): {bonus_numbers} -> {string_bonus}")
                except (json.JSONDecodeError, TypeError) as e:
                    logger.error(f"Error parsing bonus numbers for {result.lottery_type} (ID: {result.id}): {e}")
                    continue
            
            # Update count
            if needs_update:
                fixed_count += 1
            else:
                already_correct += 1
        
        # Commit all the changes
        db.session.commit()
        
        # Log final statistics
        logger.info(f"Database update complete:")
        logger.info(f"  - Total lottery results: {total_results}")
        logger.info(f"  - Fixed entries: {fixed_count}")
        logger.info(f"  - Already correct: {already_correct}")
        
        return {
            "total": total_results,
            "fixed": fixed_count,
            "correct": already_correct
        }

if __name__ == "__main__":
    fix_number_formats()