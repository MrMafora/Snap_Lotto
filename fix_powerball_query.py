#!/usr/bin/env python3
"""
Fix POWERBALL query issue - ensure it appears in homepage results
"""

import logging
from models import db, LotteryResult
from main import app
from cache_manager import cache
from sqlalchemy import text

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def fix_powerball_query():
    """Debug and fix POWERBALL query issue"""
    
    with app.app_context():
        try:
            # First, check what the raw SQL query returns
            logger.info("=== Checking raw SQL query ===")
            
            raw_query = text('''
                WITH ranked_results AS (
                    SELECT *, 
                           ROW_NUMBER() OVER (PARTITION BY lottery_type ORDER BY draw_date DESC, id DESC) as rn
                    FROM lottery_results
                    WHERE lottery_type IN ('LOTTO', 'LOTTO PLUS 1', 'LOTTO PLUS 2', 'POWERBALL', 'POWERBALL PLUS', 'DAILY LOTTO')
                )
                SELECT lottery_type, draw_number, draw_date, id, rn
                FROM ranked_results 
                WHERE rn = 1
                ORDER BY draw_date DESC
            ''')
            
            results = db.session.execute(raw_query).fetchall()
            
            logger.info("Raw query results:")
            for r in results:
                logger.info(f"  {r.lottery_type} - Draw {r.draw_number} - {r.draw_date} (ID: {r.id}, Rank: {r.rn})")
            
            # Check if there are multiple entries causing issues
            logger.info("\n=== Checking for problematic entries ===")
            
            # Get all POWERBALL entries for July 4
            pb_july4 = db.session.query(LotteryResult).filter_by(
                lottery_type='POWERBALL',
                draw_date='2025-07-04'
            ).all()
            
            if len(pb_july4) > 1:
                logger.info(f"Found {len(pb_july4)} POWERBALL entries for July 4, keeping only one")
                # Keep the first one, delete others
                for i, pb in enumerate(pb_july4[1:]):
                    logger.info(f"  Deleting duplicate POWERBALL ID: {pb.id}")
                    db.session.delete(pb)
                db.session.commit()
            
            # Clear cache
            cache.clear()
            logger.info("\nCache cleared")
            
            # Verify final state
            logger.info("\n=== Final verification ===")
            
            final_query = text('''
                WITH ranked_results AS (
                    SELECT *, 
                           ROW_NUMBER() OVER (PARTITION BY lottery_type ORDER BY draw_date DESC) as rn
                    FROM lottery_results
                )
                SELECT lottery_type, draw_number, draw_date
                FROM ranked_results 
                WHERE rn = 1
                ORDER BY lottery_type
            ''')
            
            final_results = db.session.execute(final_query).fetchall()
            
            for r in final_results:
                logger.info(f"✓ {r.lottery_type} - Draw {r.draw_number} - {r.draw_date}")
                
        except Exception as e:
            logger.error(f"Failed to fix: {e}")
            db.session.rollback()

if __name__ == "__main__":
    logger.info("=== FIXING POWERBALL QUERY ISSUE ===")
    fix_powerball_query()
    logger.info("=== DONE ===")