#!/usr/bin/env python3
"""
Quick database update with latest lottery results
"""
import os
import sys
import json
import logging
from datetime import datetime

# Add the current directory to Python path
sys.path.insert(0, os.getcwd())

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def update_database_with_latest():
    """Update database with the latest June 7th results"""
    try:
        from main import app
        from models import db, LotteryResult
        
        # Latest results data from June 7, 2025 screenshots
        latest_results = [
            {
                'lottery_type': 'LOTTO',
                'draw_number': 2548,
                'draw_date': '2025-06-07',
                'main_numbers': [1, 16, 36, 40, 42, 50],
                'bonus_numbers': [26]
            },
            {
                'lottery_type': 'LOTTO PLUS 1',
                'draw_number': 2548,
                'draw_date': '2025-06-07', 
                'main_numbers': [8, 12, 18, 20, 30, 51],
                'bonus_numbers': [45]
            },
            {
                'lottery_type': 'LOTTO PLUS 2',
                'draw_number': 2548,
                'draw_date': '2025-06-07',
                'main_numbers': [14, 19, 22, 35, 50, 51],
                'bonus_numbers': [2]
            },
            {
                'lottery_type': 'POWERBALL',
                'draw_number': 1622,
                'draw_date': '2025-06-06',
                'main_numbers': [9, 24, 34, 41, 44],
                'bonus_numbers': [7]
            },
            {
                'lottery_type': 'POWERBALL PLUS',
                'draw_number': 1622,
                'draw_date': '2025-06-06',
                'main_numbers': [27, 29, 30, 43, 46],
                'bonus_numbers': [14]
            },
            {
                'lottery_type': 'DAILY LOTTO',
                'draw_number': 5184,
                'draw_date': '2025-06-07',
                'main_numbers': [2, 7, 13, 26, 33],
                'bonus_numbers': []
            }
        ]
        
        with app.app_context():
            updated_count = 0
            
            for result_data in latest_results:
                # Check if this result already exists
                existing = LotteryResult.query.filter_by(
                    lottery_type=result_data['lottery_type'],
                    draw_number=result_data['draw_number']
                ).first()
                
                if existing:
                    logger.info(f"Already exists: {result_data['lottery_type']} Draw {result_data['draw_number']}")
                    continue
                    
                # Create new lottery result
                new_result = LotteryResult(
                    lottery_type=result_data['lottery_type'],
                    draw_number=result_data['draw_number'],
                    draw_date=datetime.strptime(result_data['draw_date'], '%Y-%m-%d'),
                    main_numbers=json.dumps(result_data['main_numbers']),
                    bonus_numbers=json.dumps(result_data['bonus_numbers'])
                )
                
                db.session.add(new_result)
                updated_count += 1
                logger.info(f"Added: {result_data['lottery_type']} Draw {result_data['draw_number']}")
            
            if updated_count > 0:
                db.session.commit()
                logger.info(f"Successfully updated database with {updated_count} new results")
            else:
                logger.info("Database is already up to date")
                
            return updated_count > 0
            
    except Exception as e:
        logger.error(f"Database update failed: {e}")
        return False

if __name__ == "__main__":
    success = update_database_with_latest()
    sys.exit(0 if success else 1)