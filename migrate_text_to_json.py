#!/usr/bin/env python3
"""
Script to migrate plain text lottery results to JSON format
"""
import json
import sqlite3
import os
from flask import Flask
import logging
from sqlalchemy import text

# Setup logging
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def create_app():
    """Create Flask app for database context"""
    app = Flask(__name__)
    
    # Configure database
    app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///lottery.db')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    return app

def get_json_numbers(number_text):
    """Convert text format numbers to JSON format"""
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
    from models import db, LotteryResult
    
    app = create_app()
    with app.app_context():
        try:
            # Find all entries with plain text format
            text_entries = LotteryResult.query.filter(
                ~LotteryResult.numbers.like('[%]')
            ).all()
            
            logger.info(f"Found {len(text_entries)} entries to migrate")
            
            for entry in text_entries:
                old_numbers = entry.numbers
                old_bonus = entry.bonus_numbers
                
                # Convert to JSON format
                json_numbers, json_bonus = get_json_numbers(entry.numbers)
                
                # If entry already has bonus_numbers in JSON format, keep it
                if old_bonus and old_bonus.startswith('['):
                    json_bonus = old_bonus
                
                # Update the entry
                entry.numbers = json_numbers
                entry.bonus_numbers = json_bonus
                
                logger.info(f"Migrated entry {entry.id}: {old_numbers} -> {json_numbers}")
            
            # Commit all changes
            db.session.commit()
            logger.info("Migration completed successfully")
            return True
            
        except Exception as e:
            logger.error(f"Error during migration: {str(e)}")
            db.session.rollback()
            return False

if __name__ == "__main__":
    migrate_text_to_json()