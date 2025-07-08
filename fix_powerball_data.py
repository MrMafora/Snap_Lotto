#!/usr/bin/env python3
"""
Fix POWERBALL data with correct information from official screenshot
"""

import json
import logging
from datetime import datetime
from models import db, LotteryResult
from main import app
from cache_manager import cache

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def fix_powerball():
    """Update POWERBALL with correct data from official screenshot"""
    
    correct_data = {
        'lottery_type': 'POWERBALL',
        'draw_number': 1630,  # Correct draw number
        'draw_date': '2025-07-04',  # Correct date
        'main_numbers': [15, 16, 22, 30, 32],  # Correct numbers from screenshot
        'bonus_numbers': [7],
        'divisions': [
            {"division": 1, "winners": 0, "prize": "R0.00"},
            {"division": 2, "winners": 2, "prize": "R203,163.70"},
            {"division": 3, "winners": 29, "prize": "R8,773.90"},
            {"division": 4, "winners": 470, "prize": "R917.80"},
            {"division": 5, "winners": 1159, "prize": "R420.80"},
            {"division": 6, "winners": 19667, "prize": "R20.60"},
            {"division": 7, "winners": 16937, "prize": "R18.00"},
            {"division": 8, "winners": 87798, "prize": "R15.00"},
            {"division": 9, "winners": 143621, "prize": "R10.00"}
        ],
        'more_info': {
            'rollover_amount': 'R51,334,513.69',  # Corrected amount
            'rollover_no': 12,
            'total_pool_size': 'R56,377,543.59',
            'total_sales': 'R22,046,305.00',  # Corrected sales
            'next_jackpot': 'R56,000,000.00',
            'draw_machine': 'RNG 3/RNG 3',
            'next_draw_date': '2025-07-08'
        }
    }
    
    with app.app_context():
        try:
            # Delete incorrect entry if exists
            wrong_entry = db.session.query(LotteryResult).filter_by(
                lottery_type='POWERBALL',
                draw_number=1632
            ).first()
            
            if wrong_entry:
                db.session.delete(wrong_entry)
                logger.info("Removed incorrect POWERBALL draw 1632")
            
            # Find or create correct entry
            existing = db.session.query(LotteryResult).filter_by(
                lottery_type='POWERBALL',
                draw_number=1630
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
                
                logger.info("Updated POWERBALL draw 1630 with correct data")
            else:
                # Create new correct entry
                new_result = LotteryResult(
                    lottery_type='POWERBALL',
                    draw_number=1630,
                    draw_date=datetime.strptime(correct_data['draw_date'], '%Y-%m-%d').date(),
                    main_numbers=correct_data['main_numbers'],
                    bonus_numbers=correct_data['bonus_numbers'],
                    divisions=json.dumps(correct_data['divisions'])
                )
                db.session.add(new_result)
                logger.info("Added POWERBALL draw 1630")
            
            db.session.commit()
            
            # Clear cache
            cache.clear()
            logger.info("Cache cleared")
            
            # Verify the update
            logger.info(f"Verified - Numbers: {correct_data['main_numbers']}")
            logger.info(f"Verified - Draw date: {correct_data['draw_date']}")
                
        except Exception as e:
            logger.error(f"Failed to update: {e}")
            db.session.rollback()

if __name__ == "__main__":
    logger.info("=== FIXING POWERBALL DATA ===")
    fix_powerball()
    logger.info("=== DONE ===")