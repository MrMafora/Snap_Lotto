#!/usr/bin/env python
"""
Script to fix the incorrect bonus number for Daily Lotto draws.
Daily Lotto drawings don't have bonus numbers, but some draws might 
have incorrect bonus numbers in the database.
"""

import logging
import json
from app import app
from models import db, LotteryResult

# Set up logging
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def fix_daily_lotto_bonus_numbers():
    """
    Find Daily Lotto records with bonus numbers and remove them.
    """
    try:
        with app.app_context():
            # Find all Daily Lotto results with bonus numbers
            daily_lotto_with_bonus = LotteryResult.query.filter(
                LotteryResult.lottery_type == "Daily Lotto",
                LotteryResult.bonus_numbers.isnot(None)
            ).all()
            
            if not daily_lotto_with_bonus:
                logger.info("No Daily Lotto records with bonus numbers found.")
                return 0
                
            logger.info(f"Found {len(daily_lotto_with_bonus)} Daily Lotto records with bonus numbers")
            
            # Update each record to remove bonus numbers
            fixed_count = 0
            for result in daily_lotto_with_bonus:
                logger.info(f"Fixing Daily Lotto Draw {result.draw_number} - removing bonus numbers {result.bonus_numbers}")
                result.bonus_numbers = None
                fixed_count += 1
                
            # Commit changes
            db.session.commit()
            logger.info(f"Successfully fixed {fixed_count} Daily Lotto records")
            return fixed_count
            
    except Exception as e:
        logger.error(f"Error fixing Daily Lotto bonus numbers: {str(e)}")
        return 0

if __name__ == "__main__":
    fixed_count = fix_daily_lotto_bonus_numbers()
    print(f"Fixed {fixed_count} Daily Lotto records")