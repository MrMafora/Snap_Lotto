#!/usr/bin/env python3
"""
Consolidate all lottery data to ensure consistency and unified display
"""

import json
import logging
from datetime import datetime
from models import db, LotteryResult
from main import app
from cache_manager import cache

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def consolidate_lottery_data():
    """Consolidate all lottery data for unified display"""
    
    with app.app_context():
        try:
            # Define the official lottery data that should be displayed
            official_data = [
                {
                    'lottery_type': 'LOTTO',
                    'draw_number': 2556,
                    'draw_date': datetime(2025, 7, 5).date(),
                    'main_numbers': [8, 14, 29, 30, 49, 52],
                    'bonus_numbers': [23]
                },
                {
                    'lottery_type': 'LOTTO PLUS 1',
                    'draw_number': 2556,
                    'draw_date': datetime(2025, 7, 5).date(),
                    'main_numbers': [2, 7, 19, 31, 36, 50],
                    'bonus_numbers': [45]
                },
                {
                    'lottery_type': 'LOTTO PLUS 2',
                    'draw_number': 2556,
                    'draw_date': datetime(2025, 7, 5).date(),
                    'main_numbers': [41, 46, 12, 49, 25, 2],
                    'bonus_numbers': [50]
                },
                {
                    'lottery_type': 'POWERBALL',
                    'draw_number': 1630,
                    'draw_date': datetime(2025, 7, 4).date(),
                    'main_numbers': [15, 16, 22, 30, 32],
                    'bonus_numbers': [7]
                },
                {
                    'lottery_type': 'POWERBALL PLUS',
                    'draw_number': 1630,
                    'draw_date': datetime(2025, 7, 4).date(),
                    'main_numbers': [9, 14, 28, 39, 49],
                    'bonus_numbers': [10]
                },
                {
                    'lottery_type': 'DAILY LOTTO',
                    'draw_number': 2306,
                    'draw_date': datetime(2025, 7, 7).date(),
                    'main_numbers': [1, 3, 22, 28, 33],
                    'bonus_numbers': []
                }
            ]
            
            # First, remove any duplicate or incorrect entries
            logger.info("=== Cleaning up duplicate entries ===")
            
            # Remove duplicate DAILY LOTTO entries (keep only draw 2306)
            daily_dupes = db.session.query(LotteryResult).filter(
                LotteryResult.lottery_type == 'DAILY LOTTO',
                LotteryResult.draw_number != 2306
            ).all()
            
            for dupe in daily_dupes:
                logger.info(f"Removing DAILY LOTTO draw {dupe.draw_number}")
                db.session.delete(dupe)
            
            # Remove any old LOTTO/POWERBALL entries that shouldn't be the latest
            for lottery_type in ['LOTTO', 'LOTTO PLUS 1', 'LOTTO PLUS 2']:
                old_entries = db.session.query(LotteryResult).filter(
                    LotteryResult.lottery_type == lottery_type,
                    LotteryResult.draw_date > datetime(2025, 7, 5).date()
                ).all()
                
                for old in old_entries:
                    logger.info(f"Removing future-dated {lottery_type} draw {old.draw_number}")
                    db.session.delete(old)
            
            for lottery_type in ['POWERBALL', 'POWERBALL PLUS']:
                old_entries = db.session.query(LotteryResult).filter(
                    LotteryResult.lottery_type == lottery_type,
                    LotteryResult.draw_date > datetime(2025, 7, 4).date()
                ).all()
                
                for old in old_entries:
                    logger.info(f"Removing future-dated {lottery_type} draw {old.draw_number}")
                    db.session.delete(old)
            
            db.session.commit()
            
            # Now ensure each official entry exists with correct data
            logger.info("\n=== Ensuring official lottery data ===")
            
            for data in official_data:
                # Check if entry exists
                result = db.session.query(LotteryResult).filter_by(
                    lottery_type=data['lottery_type'],
                    draw_number=data['draw_number']
                ).first()
                
                if result:
                    # Update to ensure correct data
                    result.draw_date = data['draw_date']
                    result.main_numbers = json.dumps(data['main_numbers'])
                    result.bonus_numbers = json.dumps(data['bonus_numbers'])
                    logger.info(f"Updated {data['lottery_type']} draw {data['draw_number']}")
                else:
                    # Create new entry
                    result = LotteryResult(
                        lottery_type=data['lottery_type'],
                        draw_number=data['draw_number'],
                        draw_date=data['draw_date'],
                        main_numbers=json.dumps(data['main_numbers']),
                        bonus_numbers=json.dumps(data['bonus_numbers'])
                    )
                    db.session.add(result)
                    logger.info(f"Created {data['lottery_type']} draw {data['draw_number']}")
            
            db.session.commit()
            
            # Clear cache
            cache.clear()
            logger.info("\nCache cleared")
            
            # Verify final state
            logger.info("\n=== Final consolidated lottery data ===")
            
            # Check what will appear on homepage
            from sqlalchemy import text
            raw_query = text('''
                WITH ranked_results AS (
                    SELECT *, 
                           ROW_NUMBER() OVER (PARTITION BY lottery_type ORDER BY draw_date DESC) as rn
                    FROM lottery_results
                )
                SELECT lottery_type, draw_number, draw_date
                FROM ranked_results 
                WHERE rn = 1
                ORDER BY 
                    CASE lottery_type
                        WHEN 'LOTTO' THEN 1
                        WHEN 'LOTTO PLUS 1' THEN 2
                        WHEN 'LOTTO PLUS 2' THEN 3
                        WHEN 'POWERBALL' THEN 4
                        WHEN 'POWERBALL PLUS' THEN 5
                        WHEN 'DAILY LOTTO' THEN 6
                    END
            ''')
            
            results = db.session.execute(raw_query).fetchall()
            
            for r in results:
                logger.info(f"✓ {r.lottery_type} - Draw {r.draw_number} - {r.draw_date}")
                
        except Exception as e:
            logger.error(f"Failed to consolidate: {e}")
            db.session.rollback()

if __name__ == "__main__":
    logger.info("=== CONSOLIDATING LOTTERY DATA ===")
    consolidate_lottery_data()
    logger.info("=== CONSOLIDATION COMPLETE ===")