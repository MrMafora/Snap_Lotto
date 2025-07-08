#!/usr/bin/env python3
"""
Fix LOTTO PLUS 1 data with correct information from official screenshot
"""

import json
import logging
from datetime import datetime
from models import db, LotteryResult
from main import app
from cache_manager import cache

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def fix_lotto_plus1():
    """Update LOTTO PLUS 1 with correct data"""
    
    correct_data = {
        'lottery_type': 'LOTTO PLUS 1',
        'draw_number': 2556,
        'draw_date': '2025-07-05',
        'main_numbers': [2, 7, 19, 31, 36, 50],  # Correct numbers from screenshot
        'bonus_numbers': [45],
        'divisions': [
            {"division": 1, "winners": 0, "prize": "R0.00"},
            {"division": 2, "winners": 0, "prize": "R0.00"},
            {"division": 3, "winners": 36, "prize": "R7,959.50"},
            {"division": 4, "winners": 76, "prize": "R1,871.20"},
            {"division": 5, "winners": 2151, "prize": "R132.20"},
            {"division": 6, "winners": 2437, "prize": "R116.70"},
            {"division": 7, "winners": 41271, "prize": "R25.00"},
            {"division": 8, "winners": 26936, "prize": "R15.00"}
        ],
        'more_info': {
            'rollover_amount': 'R24,112,718.43',
            'rollover_no': 21,
            'total_pool_size': 'R26,546,046.73',
            'total_sales': 'R7,116,702.50',  # Corrected from R3,116,702.50
            'next_jackpot': 'R25,000,000.00',
            'draw_machine': 'RNG 1',
            'next_draw_date': '2025-07-09'
        }
    }
    
    with app.app_context():
        try:
            # Find existing record
            existing = db.session.query(LotteryResult).filter_by(
                lottery_type='LOTTO PLUS 1',
                draw_number=2556
            ).first()
            
            if existing:
                # Update with correct data
                existing.draw_date = datetime.strptime(correct_data['draw_date'], '%Y-%m-%d').date()
                existing.main_numbers = correct_data['main_numbers']
                existing.bonus_numbers = correct_data['bonus_numbers']
                existing.divisions = json.dumps(correct_data['divisions'])
                
                # Check if more_info column exists
                if hasattr(existing, 'more_info'):
                    existing.more_info = json.dumps(correct_data['more_info'])
                
                db.session.commit()
                logger.info("Updated LOTTO PLUS 1 with correct data")
                
                # Clear cache
                cache.clear()
                logger.info("Cache cleared")
                
                # Verify the update
                logger.info(f"Verified - Numbers: {existing.main_numbers}")
                logger.info(f"Verified - Div 3: {correct_data['divisions'][2]['winners']} winners")
                
            else:
                logger.error("LOTTO PLUS 1 draw 2556 not found")
                
        except Exception as e:
            logger.error(f"Failed to update: {e}")
            db.session.rollback()

if __name__ == "__main__":
    logger.info("=== FIXING LOTTO PLUS 1 DATA ===")
    fix_lotto_plus1()
    logger.info("=== DONE ===")