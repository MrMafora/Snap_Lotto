#!/usr/bin/env python3
"""
Script to migrate plain text lottery results to JSON format
"""
import json
import os
import logging
import sys
from sqlalchemy import text

# Setup logging
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def get_json_numbers(number_text):
    """Convert text format numbers to JSON format"""
    if not number_text:
        return '[]', '[]'
        
    if '+' in number_text:
        # Split main numbers and bonus number
        main_part, bonus_part = number_text.split('+', 1)
        # Clean and convert main numbers
        main_numbers = [num.strip() for num in main_part.strip().split() if num.strip()]
        # Clean and get bonus number
        bonus_number = bonus_part.strip()
        return json.dumps(main_numbers), json.dumps([bonus_number]) if bonus_number else '[]'
    else:
        # Just main numbers, no bonus
        main_numbers = [num.strip() for num in number_text.strip().split() if num.strip()]
        return json.dumps(main_numbers), '[]'

def migrate_text_to_json():
    """Find all plain text format entries and convert them to JSON format"""
    # Use the existing Flask app structure - import at runtime
    from main import app, db
    from models import LotteryResult
    
    with app.app_context():
        try:
            # Get all entries with plain text format (not starting with '[')
            text_entries = db.session.execute(
                text("SELECT id, lottery_type, draw_number, numbers, bonus_numbers FROM lottery_result WHERE numbers NOT LIKE '[%]'")
            ).fetchall()
            
            logger.info(f"Found {len(text_entries)} entries to migrate")
            
            for entry in text_entries:
                entry_id = entry.id
                old_numbers = entry.numbers
                old_bonus = entry.bonus_numbers
                
                # Convert to JSON format
                json_numbers, json_bonus = get_json_numbers(old_numbers)
                
                # If entry already has bonus_numbers in JSON format, keep it
                if old_bonus and isinstance(old_bonus, str) and old_bonus.startswith('['):
                    json_bonus = old_bonus
                
                # Update the entry directly with SQL
                db.session.execute(
                    text("UPDATE lottery_result SET numbers = :numbers, bonus_numbers = :bonus WHERE id = :id"),
                    {"numbers": json_numbers, "bonus": json_bonus, "id": entry_id}
                )
                
                logger.info(f"Migrated entry {entry_id}: {old_numbers} -> {json_numbers}")
            
            # Commit all changes
            db.session.commit()
            logger.info("Migration completed successfully")
            return True
            
        except Exception as e:
            logger.error(f"Error during migration: {str(e)}")
            db.session.rollback()
            return False

if __name__ == "__main__":
    success = migrate_text_to_json()
    if success:
        print("Migration completed successfully!")
        sys.exit(0)
    else:
        print("Migration failed, see logs for details.")
        sys.exit(1)