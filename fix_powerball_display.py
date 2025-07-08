#!/usr/bin/env python3
"""
Fix POWERBALL display issue - remove incorrect draw 1631 and ensure draw 1630 is shown
"""

import json
import logging
from datetime import datetime
from models import db, LotteryResult
from main import app
from cache_manager import cache

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def fix_powerball_display():
    """Fix POWERBALL to show draw 1630 instead of 1631"""
    
    with app.app_context():
        try:
            # Remove POWERBALL draw 1631 (incorrect)
            pb_1631 = db.session.query(LotteryResult).filter_by(
                lottery_type='POWERBALL',
                draw_number=1631
            ).first()
            
            if pb_1631:
                db.session.delete(pb_1631)
                logger.info("Removed incorrect POWERBALL draw 1631")
            
            # Ensure POWERBALL draw 1630 has correct data
            pb_1630 = db.session.query(LotteryResult).filter_by(
                lottery_type='POWERBALL', 
                draw_number=1630
            ).first()
            
            if pb_1630:
                # Make sure numbers are stored correctly
                if isinstance(pb_1630.main_numbers, set):
                    pb_1630.main_numbers = [15, 16, 22, 30, 32]
                    pb_1630.bonus_numbers = [7]
                    logger.info("Fixed POWERBALL draw 1630 number storage")
                logger.info(f"POWERBALL draw 1630 exists with date: {pb_1630.draw_date}")
            else:
                logger.info("POWERBALL draw 1630 not found - needs to be added")
            
            db.session.commit()
            
            # Clear cache
            cache.clear()
            logger.info("Cache cleared")
            
            # Verify final state
            logger.info("\n=== POWERBALL entries after fix ===")
            pb_all = db.session.query(LotteryResult).filter_by(
                lottery_type='POWERBALL'
            ).order_by(LotteryResult.draw_date.desc()).all()
            
            for pb in pb_all:
                logger.info(f"Draw {pb.draw_number} - {pb.draw_date} - Numbers: {pb.main_numbers}")
                
        except Exception as e:
            logger.error(f"Failed to fix: {e}")
            db.session.rollback()

if __name__ == "__main__":
    logger.info("=== FIXING POWERBALL DISPLAY ===")
    fix_powerball_display()
    logger.info("=== DONE ===")