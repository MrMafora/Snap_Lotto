#!/usr/bin/env python3
"""
Check and fix homepage display to show correct lottery results
"""

import logging
from models import db, LotteryResult
from main import app
from cache_manager import cache
from sqlalchemy import func

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

with app.app_context():
    # First, let's see what the homepage query actually returns
    logger.info("=== Checking homepage query ===")
    
    # This is the query used in the homepage
    subquery = db.session.query(
        LotteryResult.lottery_type,
        func.max(LotteryResult.draw_date).label('max_date')
    ).group_by(LotteryResult.lottery_type).subquery()

    latest_results = db.session.query(LotteryResult).join(
        subquery,
        (LotteryResult.lottery_type == subquery.c.lottery_type) &
        (LotteryResult.draw_date == subquery.c.max_date)
    ).order_by(LotteryResult.draw_date.desc()).all()

    logger.info(f"Homepage query returns {len(latest_results)} results:")
    for result in latest_results:
        logger.info(f"  {result.lottery_type} - Draw {result.draw_number} ({result.draw_date})")
        logger.info(f"    Numbers: {result.main_numbers}")
        if result.bonus_numbers:
            logger.info(f"    Bonus: {result.bonus_numbers}")
    
    # Check for duplicate lottery types with wrong dates
    logger.info("\n=== Checking for incorrect latest results ===")
    
    # PowerBall should be draw 1630 (July 4), not 1631 (July 8)
    pb_wrong = db.session.query(LotteryResult).filter_by(
        lottery_type='POWERBALL',
        draw_number=1631
    ).all()
    
    if pb_wrong:
        logger.info(f"Found {len(pb_wrong)} incorrect POWERBALL draw 1631 entries, removing...")
        for entry in pb_wrong:
            db.session.delete(entry)
    
    # PowerBall Plus should be draw 1630 (July 4), not 1631 (July 8)
    pbp_wrong = db.session.query(LotteryResult).filter_by(
        lottery_type='POWERBALL PLUS',
        draw_number=1631
    ).all()
    
    if pbp_wrong:
        logger.info(f"Found {len(pbp_wrong)} incorrect POWERBALL PLUS draw 1631 entries, removing...")
        for entry in pbp_wrong:
            db.session.delete(entry)
    
    # Also check for "PowerBall" vs "POWERBALL" naming inconsistency
    pb_inconsistent = db.session.query(LotteryResult).filter_by(
        lottery_type='PowerBall'
    ).all()
    
    if pb_inconsistent:
        logger.info(f"Found {len(pb_inconsistent)} entries with 'PowerBall' (should be 'POWERBALL'), fixing...")
        for entry in pb_inconsistent:
            entry.lottery_type = 'POWERBALL'
    
    # Keep only draw 4524 for Daily Lotto (July 8)
    daily_old = db.session.query(LotteryResult).filter(
        LotteryResult.lottery_type == 'DAILY LOTTO',
        LotteryResult.draw_number != 4524,
        LotteryResult.draw_number != 2306
    ).all()
    
    if daily_old:
        logger.info(f"Found {len(daily_old)} old DAILY LOTTO entries, removing...")
        for entry in daily_old:
            db.session.delete(entry)
    
    # Commit all changes
    db.session.commit()
    
    # Clear cache to ensure fresh data
    cache.clear()
    logger.info("\nCache cleared - homepage will show updated results")
    
    # Verify final state
    logger.info("\n=== Final lottery results that should appear ===")
    
    final_check = [
        ('LOTTO', 2556),
        ('LOTTO PLUS 1', 2556),
        ('LOTTO PLUS 2', 2556),
        ('POWERBALL', 1630),
        ('POWERBALL PLUS', 1630),
        ('DAILY LOTTO', 4524),
        ('DAILY LOTTO', 2306)
    ]
    
    for lottery_type, draw_num in final_check:
        result = db.session.query(LotteryResult).filter_by(
            lottery_type=lottery_type,
            draw_number=draw_num
        ).first()
        
        if result:
            logger.info(f"✓ {lottery_type} Draw {draw_num} ({result.draw_date})")
        else:
            logger.info(f"✗ {lottery_type} Draw {draw_num} NOT FOUND")