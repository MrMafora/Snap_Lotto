#!/usr/bin/env python3
"""
Script to detect and clean up duplicate lottery results in the database.
This script scans the database for entries with the same lottery_type and draw_number,
keeping only the most complete record and removing duplicates.
"""

import os
import sys
import logging
import argparse
from datetime import datetime
from typing import Dict, List, Tuple

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('cleanup_duplicates')

def setup_flask_context():
    """
    Set up a Flask application context for database operations.
    
    Returns:
        Tuple containing the Flask app and SQLAlchemy db objects
    """
    try:
        from flask import Flask
        from flask_sqlalchemy import SQLAlchemy
        from sqlalchemy.orm import DeclarativeBase
        import os
        
        class Base(DeclarativeBase):
            pass
            
        db = SQLAlchemy(model_class=Base)
        app = Flask(__name__)
        
        # Configure database from environment
        app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL", "sqlite:///lottery.db")
        app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
        app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
            "pool_recycle": 300,
            "pool_pre_ping": True,
        }
        
        db.init_app(app)
        logger.info("Created new application context")
        return app, db
    except Exception as e:
        logger.error(f"Error setting up Flask context: {str(e)}")
        raise

def is_better_record(record1, record2):
    """
    Determines which record is more complete/better quality.
    
    Args:
        record1: First LotteryResult record
        record2: Second LotteryResult record
        
    Returns:
        True if record1 is better, False if record2 is better
    """
    # Count non-None fields as a simple metric of record completeness
    def count_non_none(record):
        count = 0
        for attr in ['ball_1', 'ball_2', 'ball_3', 'ball_4', 'ball_5', 'ball_6', 
                    'bonus_ball', 'division_1_winners', 'division_1_prize', 
                    'division_2_winners', 'division_2_prize', 'division_3_winners']:
            if getattr(record, attr, None) is not None:
                count += 1
        return count
    
    score1 = count_non_none(record1)
    score2 = count_non_none(record2)
    
    # If scores are equal, prefer the newer record (higher ID assuming autoincrement)
    if score1 == score2:
        return record1.id > record2.id
    return score1 > score2

def find_duplicates(db):
    """
    Find duplicate lottery results in the database.
    
    Args:
        db: SQLAlchemy database object
        
    Returns:
        Dict mapping (lottery_type, draw_number) to list of record IDs
    """
    from models import LotteryResult
    from sqlalchemy import func
    
    # Get all lottery results
    results = db.session.query(LotteryResult).all()
    
    # Group by lottery_type and draw_number
    grouped = {}
    for result in results:
        key = (result.lottery_type, result.draw_number)
        if key not in grouped:
            grouped[key] = []
        grouped[key].append(result)
    
    # Find groups with duplicates
    duplicates = {k: v for k, v in grouped.items() if len(v) > 1}
    
    if duplicates:
        logger.info(f"Found {len(duplicates)} duplicate groups")
        for key, group in duplicates.items():
            logger.info(f"Duplicate group: {key} has {len(group)} records")
    else:
        logger.info("No duplicates found")
    
    return duplicates

def remove_duplicates(db, duplicates):
    """
    Remove duplicate records, keeping only the best one from each group.
    
    Args:
        db: SQLAlchemy database object
        duplicates: Dict mapping (lottery_type, draw_number) to list of record IDs
        
    Returns:
        int: Number of records removed
    """
    removed_count = 0
    
    for key, group in duplicates.items():
        lottery_type, draw_number = key
        
        if len(group) <= 1:
            continue
            
        # Find the best record
        best_record = group[0]
        for record in group[1:]:
            if is_better_record(record, best_record):
                best_record = record
        
        # Remove all other records
        for record in group:
            if record.id != best_record.id:
                logger.info(f"Removing duplicate: ID {record.id}, {lottery_type} Draw #{draw_number}")
                db.session.delete(record)
                removed_count += 1
    
    # Commit changes
    if removed_count > 0:
        db.session.commit()
        logger.info(f"Removed {removed_count} duplicate records")
    
    return removed_count

def prevent_future_duplicates(db):
    """
    Add database constraints to prevent future duplicates.
    Note: This may fail if existing duplicates haven't been cleaned up.
    
    Args:
        db: SQLAlchemy database object
        
    Returns:
        bool: Success status
    """
    try:
        from sqlalchemy import UniqueConstraint, text
        
        # Check if the constraint already exists
        # This is PostgreSQL-specific code
        constraint_check = text("""
            SELECT COUNT(*) FROM pg_constraint 
            WHERE conname = 'uq_lottery_result_type_draw'
        """)
        
        with db.engine.connect() as conn:
            result = conn.execute(constraint_check)
            exists = result.scalar() > 0
        
        if exists:
            logger.info("Unique constraint already exists")
            return True
            
        # Add the constraint
        create_constraint = text("""
            ALTER TABLE lottery_result 
            ADD CONSTRAINT uq_lottery_result_type_draw 
            UNIQUE (lottery_type, draw_number)
        """)
        
        with db.engine.connect() as conn:
            conn.execute(create_constraint)
            conn.commit()
            
        logger.info("Added unique constraint to prevent future duplicates")
        return True
        
    except Exception as e:
        logger.error(f"Failed to add constraint: {str(e)}")
        return False

def main():
    parser = argparse.ArgumentParser(description='Clean up duplicate lottery results in the database.')
    parser.add_argument('--dry-run', action='store_true', help='Only detect duplicates, don\'t remove them')
    parser.add_argument('--add-constraint', action='store_true', help='Add database constraint to prevent future duplicates')
    
    args = parser.parse_args()
    
    try:
        # Set up Flask context
        app, db = setup_flask_context()
        
        with app.app_context():
            # Import models inside app context
            from models import LotteryResult
            
            # Find duplicates
            duplicates = find_duplicates(db)
            
            if not duplicates:
                logger.info("No duplicates found, database is clean")
                if args.add_constraint:
                    prevent_future_duplicates(db)
                return 0
                
            if args.dry_run:
                logger.info("Dry run mode, not removing duplicates")
                for key, group in duplicates.items():
                    lottery_type, draw_number = key
                    logger.info(f"Would remove {len(group) - 1} duplicates for {lottery_type} Draw #{draw_number}")
            else:
                # Remove duplicates
                removed = remove_duplicates(db, duplicates)
                logger.info(f"Removed {removed} duplicate records")
                
                # Verify duplicates are gone
                remaining = find_duplicates(db)
                if remaining:
                    logger.warning(f"Still have {len(remaining)} duplicate groups after cleanup")
                else:
                    logger.info("All duplicates successfully removed")
                    
                    # Add constraint if requested
                    if args.add_constraint:
                        prevent_future_duplicates(db)
            
        return 0
        
    except Exception as e:
        logger.error(f"Error: {str(e)}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == '__main__':
    sys.exit(main())