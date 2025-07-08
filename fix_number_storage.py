#!/usr/bin/env python3
"""
Fix lottery number storage - convert string format to proper lists
"""

import json
import logging
from datetime import datetime
from models import db, LotteryResult
from main import app
from cache_manager import cache

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def fix_number_storage():
    """Fix all lottery results with incorrect number storage"""
    
    with app.app_context():
        try:
            # Get all results that need fixing
            all_results = db.session.query(LotteryResult).all()
            fixed_count = 0
            
            for result in all_results:
                needs_update = False
                
                # Check if main_numbers is stored as string
                if isinstance(result.main_numbers, str) and '{' in result.main_numbers:
                    # Extract numbers from string format "{8,14,29,30,49,52}"
                    numbers_str = result.main_numbers.strip('{}')
                    result.main_numbers = [int(n.strip()) for n in numbers_str.split(',') if n.strip().isdigit()]
                    needs_update = True
                    logger.info(f"Fixed {result.lottery_type} draw {result.draw_number} main numbers: {result.main_numbers}")
                
                # Check bonus numbers
                if result.bonus_numbers and isinstance(result.bonus_numbers, str) and '{' in result.bonus_numbers:
                    bonus_str = result.bonus_numbers.strip('{}')
                    if bonus_str:
                        result.bonus_numbers = [int(n.strip()) for n in bonus_str.split(',') if n.strip().isdigit()]
                    else:
                        result.bonus_numbers = []
                    needs_update = True
                    logger.info(f"Fixed {result.lottery_type} draw {result.draw_number} bonus numbers: {result.bonus_numbers}")
                
                if needs_update:
                    fixed_count += 1
            
            if fixed_count > 0:
                db.session.commit()
                logger.info(f"Fixed {fixed_count} lottery results")
                
                # Clear cache
                cache.clear()
                logger.info("Cache cleared")
            else:
                logger.info("No results needed fixing")
                
        except Exception as e:
            logger.error(f"Failed to fix number storage: {e}")
            db.session.rollback()

if __name__ == "__main__":
    logger.info("=== FIXING NUMBER STORAGE FORMAT ===")
    fix_number_storage()
    logger.info("=== DONE ===")