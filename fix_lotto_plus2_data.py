#!/usr/bin/env python3
"""
Fix LOTTO PLUS 2 data with correct information from user
"""

import logging
from models import db, LotteryResult
from main import app
from cache_manager import cache
import json

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def fix_lotto_plus2():
    """Update LOTTO PLUS 2 with correct data"""
    
    with app.app_context():
        try:
            # Find LOTTO PLUS 2 draw 2556
            result = db.session.query(LotteryResult).filter_by(
                lottery_type='LOTTO PLUS 2',
                draw_number=2556
            ).first()
            
            if result:
                logger.info(f"Found LOTTO PLUS 2 draw 2556: {result.main_numbers}")
                
                # Update with correct numbers from user
                result.main_numbers = json.dumps([12, 25, 39, 48, 51, 52])
                result.bonus_numbers = json.dumps([8])
                
                # Update prize divisions with correct data
                result.prize_divisions = json.dumps([
                    {"division": 1, "winners": 0, "payout": 0.00, "description": "6 Correct Numbers"},
                    {"division": 2, "winners": 1, "payout": 170010.10, "description": "5 Correct + Bonus"},
                    {"division": 3, "winners": 27, "payout": 4197.80, "description": "5 Correct"},
                    {"division": 4, "winners": 78, "payout": 1802.90, "description": "4 Correct + Bonus"},
                    {"division": 5, "winners": 1656, "payout": 169.80, "description": "4 Correct"},
                    {"division": 6, "winners": 2386, "payout": 117.90, "description": "3 Correct + Bonus"},
                    {"division": 7, "winners": 34624, "payout": 25.00, "description": "3 Correct"},
                    {"division": 8, "winners": 26896, "payout": 15.00, "description": "2 Correct + Bonus"}
                ])
                
                # Update additional info
                result.additional_info = json.dumps({
                    "rollover_amount": "R18,496,027.36",
                    "rollover_no": "17",
                    "total_pool_size": "R20,751,542.46",
                    "total_sales": "R6,735,860.00",
                    "next_jackpot": "R20,000,000.00",
                    "draw_machine": "RNG 1",
                    "next_draw_date": "2025-07-09"
                })
                
                db.session.commit()
                logger.info("✓ Updated LOTTO PLUS 2 with correct data")
                
                # Clear cache
                cache.clear()
                logger.info("✓ Cache cleared")
                
                # Verify the update
                updated = db.session.query(LotteryResult).filter_by(
                    lottery_type='LOTTO PLUS 2',
                    draw_number=2556
                ).first()
                
                logger.info(f"Verified new numbers: {updated.main_numbers}")
                logger.info(f"Verified bonus: {updated.bonus_numbers}")
                
            else:
                logger.error("LOTTO PLUS 2 draw 2556 not found!")
                
        except Exception as e:
            logger.error(f"Failed to update: {e}")
            db.session.rollback()

if __name__ == "__main__":
    logger.info("=== FIXING LOTTO PLUS 2 DATA ===")
    fix_lotto_plus2()
    logger.info("=== DONE ===")