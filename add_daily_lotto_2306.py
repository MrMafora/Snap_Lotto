#!/usr/bin/env python3
"""
Add DAILY LOTTO draw 2306 from July 7, 2025 to database
"""

import json
import logging
from datetime import datetime
from models import db, LotteryResult
from main import app
from cache_manager import cache

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def add_daily_lotto_2306():
    """Add DAILY LOTTO draw 2306 with authentic data"""
    
    lottery_data = {
        'lottery_type': 'DAILY LOTTO',
        'draw_number': 2306,
        'draw_date': '2025-07-07',
        'main_numbers': [1, 3, 22, 28, 33],  # Numbers from screenshot
        'bonus_numbers': [],  # Daily Lotto has no bonus
        'divisions': [
            {"division": 1, "winners": 0, "prize": "R0.00"},
            {"division": 2, "winners": 376, "prize": "R1,574.70"},
            {"division": 3, "winners": 11001, "prize": "R20.10"},
            {"division": 4, "winners": 108669, "prize": "R5.00"}
        ],
        'more_info': {
            'total_pool_size': 'R1,356,552.30',
            'total_sales': 'R2,703,639.00',
            'draw_machine': 'RNG 2',
            'next_draw_date': '2025-07-08'
        }
    }
    
    with app.app_context():
        try:
            # Check if already exists
            existing = db.session.query(LotteryResult).filter_by(
                lottery_type='DAILY LOTTO',
                draw_number=2306
            ).first()
            
            if existing:
                logger.info("DAILY LOTTO draw 2306 already exists, updating...")
                existing.draw_date = datetime.strptime(lottery_data['draw_date'], '%Y-%m-%d').date()
                existing.main_numbers = lottery_data['main_numbers']
                existing.bonus_numbers = lottery_data['bonus_numbers']
                existing.divisions = json.dumps(lottery_data['divisions'])
                
                if hasattr(existing, 'more_info'):
                    existing.more_info = json.dumps(lottery_data['more_info'])
            else:
                # Create new entry
                new_result = LotteryResult(
                    lottery_type='DAILY LOTTO',
                    draw_number=2306,
                    draw_date=datetime.strptime(lottery_data['draw_date'], '%Y-%m-%d').date(),
                    main_numbers=lottery_data['main_numbers'],
                    bonus_numbers=lottery_data['bonus_numbers'],
                    divisions=json.dumps(lottery_data['divisions'])
                )
                
                # Add more_info if column exists
                if hasattr(new_result, 'more_info'):
                    new_result.more_info = json.dumps(lottery_data['more_info'])
                
                db.session.add(new_result)
                logger.info("Added new DAILY LOTTO draw 2306")
            
            db.session.commit()
            
            # Clear cache
            cache.clear()
            logger.info("Cache cleared")
            
            # Verify
            logger.info(f"Verified - Numbers: {lottery_data['main_numbers']}")
            logger.info(f"Verified - Draw date: {lottery_data['draw_date']}")
            logger.info(f"Verified - Div 2: 376 winners @ R1,574.70")
                
        except Exception as e:
            logger.error(f"Failed to add/update: {e}")
            db.session.rollback()

if __name__ == "__main__":
    logger.info("=== ADDING DAILY LOTTO DRAW 2306 ===")
    add_daily_lotto_2306()
    logger.info("=== DONE ===")