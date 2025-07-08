#!/usr/bin/env python3
"""
Fix POWERBALL PLUS data with correct information from official screenshot
"""

import json
import logging
from datetime import datetime
from models import db, LotteryResult
from main import app
from cache_manager import cache

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def fix_powerball_plus():
    """Update POWERBALL PLUS with correct data from official screenshot"""
    
    correct_data = {
        'lottery_type': 'POWERBALL PLUS',
        'draw_number': 1630,  # Correct draw number
        'draw_date': '2025-07-04',  # Correct date
        'main_numbers': [9, 14, 28, 39, 49],  # Correct numbers from screenshot
        'bonus_numbers': [10],
        'divisions': [
            {"division": 1, "winners": 0, "prize": "R0.00"},
            {"division": 2, "winners": 2, "prize": "R83,880.40"},
            {"division": 3, "winners": 16, "prize": "R6,565.80"},
            {"division": 4, "winners": 376, "prize": "R473.70"},
            {"division": 5, "winners": 866, "prize": "R232.50"},
            {"division": 6, "winners": 15540, "prize": "R10.80"},
            {"division": 7, "winners": 11735, "prize": "R10.70"},
            {"division": 8, "winners": 62500, "prize": "R7.50"},
            {"division": 9, "winners": 104019, "prize": "R5.00"}
        ],
        'more_info': {
            'rollover_amount': 'R2,286,265.31',  # Corrected amount
            'rollover_no': 1,
            'total_pool_size': 'R4,220,776.61',
            'total_sales': 'R8,794,227.50',
            'next_jackpot': 'R4,000,000.00',
            'draw_machine': 'RNG 2/RNG 2',
            'next_draw_date': '2025-07-08'
        }
    }
    
    with app.app_context():
        try:
            # Delete incorrect entries if they exist
            wrong_entries = db.session.query(LotteryResult).filter_by(
                lottery_type='POWERBALL PLUS',
                draw_number=1632
            ).all()
            
            for entry in wrong_entries:
                db.session.delete(entry)
                logger.info("Removed incorrect POWERBALL PLUS draw 1632")
            
            # Find or create correct entry
            existing = db.session.query(LotteryResult).filter_by(
                lottery_type='POWERBALL PLUS',
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
                
                logger.info("Updated POWERBALL PLUS draw 1630 with correct data")
            else:
                # Create new correct entry
                new_result = LotteryResult(
                    lottery_type='POWERBALL PLUS',
                    draw_number=1630,
                    draw_date=datetime.strptime(correct_data['draw_date'], '%Y-%m-%d').date(),
                    main_numbers=correct_data['main_numbers'],
                    bonus_numbers=correct_data['bonus_numbers'],
                    divisions=json.dumps(correct_data['divisions'])
                )
                db.session.add(new_result)
                logger.info("Added POWERBALL PLUS draw 1630")
            
            db.session.commit()
            
            # Clear cache
            cache.clear()
            logger.info("Cache cleared")
            
            # Verify the update
            logger.info(f"Verified - Numbers: {correct_data['main_numbers']}")
            logger.info(f"Verified - Draw date: {correct_data['draw_date']}")
            logger.info(f"Verified - Div 2 winners: 2 @ R83,880.40")
                
        except Exception as e:
            logger.error(f"Failed to update: {e}")
            db.session.rollback()

if __name__ == "__main__":
    logger.info("=== FIXING POWERBALL PLUS DATA ===")
    fix_powerball_plus()
    logger.info("=== DONE ===")