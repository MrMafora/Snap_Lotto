#!/usr/bin/env python3
"""
Direct JSON migration script that doesn't load the full Flask application
"""
import json
import os
import sys
import psycopg2
import logging

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

def migrate_data_to_json():
    """Directly connect to the database and migrate plain text to JSON"""
    try:
        # Get database URL from environment
        db_url = os.environ.get('DATABASE_URL')
        if not db_url:
            logger.error("DATABASE_URL environment variable not set")
            return False
            
        # Connect to the database
        conn = psycopg2.connect(db_url)
        cursor = conn.cursor()
        
        # Find all plain text entries
        cursor.execute("SELECT id, lottery_type, draw_number, numbers, bonus_numbers FROM lottery_result WHERE numbers NOT LIKE '[%]'")
        text_entries = cursor.fetchall()
        
        logger.info(f"Found {len(text_entries)} entries to migrate")
        
        # Process each entry
        for (entry_id, lottery_type, draw_number, numbers, bonus_numbers) in text_entries:
            # Convert to JSON format
            json_numbers, json_bonus = get_json_numbers(numbers)
            
            # If entry already has bonus_numbers in JSON format, keep it
            if bonus_numbers and isinstance(bonus_numbers, str) and bonus_numbers.startswith('['):
                json_bonus = bonus_numbers
            
            # Update the entry
            cursor.execute(
                "UPDATE lottery_result SET numbers = %s, bonus_numbers = %s WHERE id = %s",
                (json_numbers, json_bonus, entry_id)
            )
            
            logger.info(f"Migrated entry {entry_id}: {numbers} -> {json_numbers}")
        
        # Commit all changes
        conn.commit()
        logger.info("Migration completed successfully")
        
        # Close the database connection
        cursor.close()
        conn.close()
        
        return True
        
    except Exception as e:
        logger.error(f"Error during migration: {str(e)}")
        return False

if __name__ == "__main__":
    success = migrate_data_to_json()
    if success:
        print("Migration completed successfully!")
        sys.exit(0)
    else:
        print("Migration failed, see logs for details.")
        sys.exit(1)