#!/usr/bin/env python3
"""
Complete the update of July 8, 2025 authentic lottery data
"""

import json
import logging
from datetime import datetime
from models import db, LotteryResult
from main import app
from cache_manager import cache

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def complete_updates():
    """Complete updating remaining lottery types"""
    
    # Remaining authentic data from official screenshots
    remaining_updates = [
        {
            'lottery_type': 'LOTTO PLUS 2',
            'draw_number': 2556,
            'draw_date': '2025-07-05',
            'main_numbers': [12, 25, 39, 48, 51, 52],
            'bonus_numbers': [8]
        },
        {
            'lottery_type': 'POWERBALL',
            'draw_number': 1632,
            'draw_date': '2025-07-08',
            'main_numbers': [39, 22, 18, 14, 49],
            'bonus_numbers': [7]
        },
        {
            'lottery_type': 'POWERBALL PLUS',
            'draw_number': 1632,
            'draw_date': '2025-07-08',
            'main_numbers': [29, 9, 16, 17, 5],
            'bonus_numbers': [10]
        },
        {
            'lottery_type': 'DAILY LOTTO',
            'draw_number': 4524,
            'draw_date': '2025-07-08',
            'main_numbers': [3, 23, 26, 1, 22],
            'bonus_numbers': []
        }
    ]
    
    with app.app_context():
        for data in remaining_updates:
            try:
                lottery_type = data['lottery_type']
                draw_number = data['draw_number']
                
                # Check if already exists
                existing = db.session.query(LotteryResult).filter_by(
                    lottery_type=lottery_type,
                    draw_number=draw_number
                ).first()
                
                if existing:
                    # Update with authentic data
                    existing.draw_date = datetime.strptime(data['draw_date'], '%Y-%m-%d').date()
                    existing.main_numbers = data['main_numbers']
                    existing.bonus_numbers = data['bonus_numbers']
                    logger.info(f"Updated {lottery_type} draw {draw_number} with authentic data")
                else:
                    # Create new
                    new_result = LotteryResult(
                        lottery_type=lottery_type,
                        draw_number=draw_number,
                        draw_date=datetime.strptime(data['draw_date'], '%Y-%m-%d').date(),
                        main_numbers=data['main_numbers'],
                        bonus_numbers=data['bonus_numbers'],
                        divisions=json.dumps([])
                    )
                    db.session.add(new_result)
                    logger.info(f"Added {lottery_type} draw {draw_number}")
                
            except Exception as e:
                logger.error(f"Failed to update {lottery_type}: {e}")
        
        # Commit changes
        db.session.commit()
        
        # Clear cache
        cache.clear()
        logger.info("All updates completed - cache cleared")

if __name__ == "__main__":
    logger.info("=== COMPLETING AUTHENTIC LOTTERY DATA UPDATE ===")
    complete_updates()
    logger.info("=== DONE ===")