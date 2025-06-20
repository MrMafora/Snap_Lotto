#!/usr/bin/env python3
"""
Update database with current draw numbers based on user input
"""

import os
import json
import logging
from datetime import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models import LotteryResult
from config import Config

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def update_with_current_draws():
    """Update database with current draw numbers"""
    
    # Current draw numbers from user input
    current_draws = {
        'LOTTO': {'draw_number': 2551, 'date': '2025-06-20'},
        'LOTTO PLUS 1': {'draw_number': 2551, 'date': '2025-06-18'}, 
        'LOTTO PLUS 2': {'draw_number': 2551, 'date': '2025-06-18'},
        'PowerBall': {'draw_number': 1625, 'date': '2025-06-20'},
        'POWERBALL PLUS': {'draw_number': 1625, 'date': '2025-06-17'},
        'DAILY LOTTO': {'draw_number': 2288, 'date': '2025-06-20'}
    }
    
    try:
        engine = create_engine(Config.SQLALCHEMY_DATABASE_URI)
        Session = sessionmaker(bind=engine)
        session = Session()
        
        updated_count = 0
        
        for lottery_type, draw_info in current_draws.items():
            try:
                # Find existing result with old draw number
                existing = session.query(LotteryResult).filter_by(
                    lottery_type=lottery_type
                ).order_by(LotteryResult.created_at.desc()).first()
                
                if existing:
                    # Update with correct draw number
                    existing.draw_number = draw_info['draw_number']
                    existing.draw_date = datetime.strptime(draw_info['date'], '%Y-%m-%d').date()
                    logger.info(f"Updated {lottery_type}: Draw {draw_info['draw_number']}")
                    updated_count += 1
                else:
                    logger.warning(f"No existing record found for {lottery_type}")
                    
            except Exception as e:
                logger.error(f"Failed to update {lottery_type}: {str(e)}")
                continue
        
        session.commit()
        session.close()
        
        logger.info(f"Successfully updated {updated_count} lottery results")
        return updated_count > 0
        
    except Exception as e:
        logger.error(f"Database update failed: {str(e)}")
        return False

if __name__ == "__main__":
    logger.info("Updating database with current draw numbers...")
    
    if update_with_current_draws():
        logger.info("✓ Database updated with correct draw numbers")
    else:
        logger.error("✗ Failed to update database")