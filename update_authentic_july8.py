#!/usr/bin/env python3
"""
Update database with authentic July 8, 2025 lottery data from official screenshots
"""

import json
import logging
from datetime import datetime
from models import db, LotteryResult
from main import app
from cache_manager import cache

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def update_lottery_results():
    """Update database with authentic lottery data from July 8, 2025 screenshots"""
    
    # Authentic data extracted from official screenshots
    lottery_updates = [
        {
            'lottery_type': 'LOTTO',
            'draw_number': 2556,
            'draw_date': '2025-07-05',
            'main_numbers': [10, 46, 52, 14, 27, 48],
            'bonus_numbers': [23],
            'divisions': [
                {"division": 1, "winners": 0, "prize": "R0.00"},
                {"division": 2, "winners": 0, "prize": "R0.00"},
                {"division": 3, "winners": 13, "prize": "R7,531.30"},
                {"division": 4, "winners": 316, "prize": "R2,427.70"},
                {"division": 5, "winners": 515, "prize": "R190.90"},
                {"division": 6, "winners": 6975, "prize": "R110.70"},
                {"division": 7, "winners": 60579, "prize": "R50.00"},
                {"division": 8, "winners": 103117, "prize": "R20.00"}
            ]
        },
        {
            'lottery_type': 'LOTTO PLUS 1',
            'draw_number': 2556,
            'draw_date': '2025-07-05',
            'main_numbers': [14, 19, 50, 22, 29, 41],
            'bonus_numbers': [45],
            'divisions': [
                {"division": 1, "winners": 0, "prize": "R0.00"},
                {"division": 2, "winners": 0, "prize": "R0.00"},
                {"division": 3, "winners": 7, "prize": "R7,959.50"},
                {"division": 4, "winners": 165, "prize": "R1,821.20"},
                {"division": 5, "winners": 332, "prize": "R132.20"},
                {"division": 6, "winners": 4421, "prize": "R116.70"},
                {"division": 7, "winners": 51271, "prize": "R25.00"},
                {"division": 8, "winners": 88996, "prize": "R15.00"}
            ]
        },
        {
            'lottery_type': 'LOTTO PLUS 2',
            'draw_number': 2556,
            'draw_date': '2025-07-05',
            'main_numbers': [41, 46, 12, 49, 25, 2],
            'bonus_numbers': [50],
            'divisions': [
                {"division": 1, "winners": 0, "prize": "R0.00"},
                {"division": 2, "winners": 1, "prize": "R170,810.10"},
                {"division": 3, "winners": 10, "prize": "R4,197.80"},
                {"division": 4, "winners": 154, "prize": "R1,802.90"},
                {"division": 5, "winners": 444, "prize": "R169.80"},
                {"division": 6, "winners": 5366, "prize": "R117.90"},
                {"division": 7, "winners": 54624, "prize": "R25.00"},
                {"division": 8, "winners": 88894, "prize": "R15.00"}
            ]
        },
        {
            'lottery_type': 'POWERBALL',
            'draw_number': 1632,
            'draw_date': '2025-07-08',
            'main_numbers': [39, 22, 18, 14, 49],
            'bonus_numbers': [7],
            'divisions': [
                {"division": 1, "winners": 0, "prize": "R0.00"},
                {"division": 2, "winners": 0, "prize": "R203,163.70"},
                {"division": 3, "winners": 5, "prize": "R8,773.90"},
                {"division": 4, "winners": 220, "prize": "R917.80"},
                {"division": 5, "winners": 165, "prize": "R420.80"},
                {"division": 6, "winners": 5052, "prize": "R20.60"},
                {"division": 7, "winners": 59798, "prize": "R18.00"},
                {"division": 8, "winners": 105019, "prize": "R15.00"},
                {"division": 9, "winners": 149521, "prize": "R10.00"}
            ]
        },
        {
            'lottery_type': 'POWERBALL PLUS',
            'draw_number': 1632,
            'draw_date': '2025-07-08',
            'main_numbers': [29, 9, 16, 17, 5],
            'bonus_numbers': [10],
            'divisions': [
                {"division": 1, "winners": 0, "prize": "R0.00"},
                {"division": 2, "winners": 0, "prize": "R83,860.40"},
                {"division": 3, "winners": 11, "prize": "R6,565.80"},
                {"division": 4, "winners": 233, "prize": "R473.70"},
                {"division": 5, "winners": 256, "prize": "R232.50"},
                {"division": 6, "winners": 5009, "prize": "R10.80"},
                {"division": 7, "winners": 62506, "prize": "R10.70"},
                {"division": 8, "winners": 106019, "prize": "R7.50"},
                {"division": 9, "winners": 154419, "prize": "R5.00"}
            ]
        },
        {
            'lottery_type': 'DAILY LOTTO',
            'draw_number': 4524,
            'draw_date': '2025-07-08',
            'main_numbers': [3, 23, 26, 1, 22],
            'bonus_numbers': [],
            'divisions': [
                {"division": 1, "winners": 0, "prize": "R0.00"},
                {"division": 2, "winners": 276, "prize": "R1,574.70"},
                {"division": 3, "winners": 7169, "prize": "R20.10"},
                {"division": 4, "winners": 102840, "prize": "R5.00"}
            ]
        }
    ]
    
    with app.app_context():
        success_count = 0
        
        for data in lottery_updates:
            try:
                lottery_type = data['lottery_type']
                draw_number = data['draw_number']
                
                # Find existing record
                existing = db.session.query(LotteryResult).filter_by(
                    lottery_type=lottery_type,
                    draw_number=draw_number
                ).first()
                
                if existing:
                    # Update with authentic data
                    existing.draw_date = datetime.strptime(data['draw_date'], '%Y-%m-%d').date()
                    existing.main_numbers = data['main_numbers']
                    existing.bonus_numbers = data['bonus_numbers']
                    existing.divisions = json.dumps(data['divisions'])
                    logger.info(f"Updated {lottery_type} draw {draw_number}")
                else:
                    # Create new record
                    new_result = LotteryResult(
                        lottery_type=lottery_type,
                        draw_number=draw_number,
                        draw_date=datetime.strptime(data['draw_date'], '%Y-%m-%d').date(),
                        main_numbers=data['main_numbers'],
                        bonus_numbers=data['bonus_numbers'],
                        divisions=json.dumps(data['divisions'])
                    )
                    db.session.add(new_result)
                    logger.info(f"Added new {lottery_type} draw {draw_number}")
                
                success_count += 1
                
            except Exception as e:
                logger.error(f"Failed to update {data.get('lottery_type')}: {e}")
        
        # Commit all changes
        db.session.commit()
        logger.info(f"\nSuccessfully updated {success_count}/{len(lottery_updates)} lottery results")
        
        # Clear cache
        cache.clear()
        logger.info("Cache cleared - authentic data will now be displayed")

if __name__ == "__main__":
    logger.info("=== UPDATING DATABASE WITH AUTHENTIC JULY 8, 2025 LOTTERY DATA ===")
    update_lottery_results()
    logger.info("=== UPDATE COMPLETED ===")