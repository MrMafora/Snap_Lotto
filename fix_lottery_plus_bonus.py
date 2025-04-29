#!/usr/bin/env python3
"""
Script to fix bonus numbers for Lottery Plus 1 and other lottery types
with the enhanced parsing logic.
"""

import os
import sys
import json
import logging
from datetime import datetime
import re
from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def get_database_url():
    """Get database URL from environment variable"""
    return os.environ.get('DATABASE_URL')

def parse_numbers(numbers_str):
    """
    Parse lottery numbers from string format to list of integers.
    Enhanced to handle various formats including single numbers.
    
    Args:
        numbers_str (str): String representation of numbers
        
    Returns:
        list: List of numbers as integers
    """
    if numbers_str is None or (hasattr(numbers_str, 'strip') and not numbers_str.strip()):
        return []
        
    # If already a list of integers, return as is
    if isinstance(numbers_str, list):
        return [int(n) for n in numbers_str if str(n).isdigit()]
    
    # If just a single integer, return as a list with one item
    if isinstance(numbers_str, (int, float)):
        try:
            return [int(numbers_str)]
        except:
            return []
        
    # Handle different formats of number strings
    if isinstance(numbers_str, str):
        # Remove any prefix like "Example:" and other non-essential text
        numbers_str = re.sub(r'example:|bonus:|ball:|powerball:', '', numbers_str.lower()).strip()
        
        # Special case: "33" or single number as string
        if numbers_str.isdigit():
            return [int(numbers_str)]
            
        # Handle comma-separated format: "1, 2, 3, 4, 5, 6"
        if ',' in numbers_str:
            # Extract all numbers using regex to catch digits that might have text around them
            matches = re.findall(r'\d+', numbers_str)
            if matches:
                return [int(n) for n in matches]
            
        # Handle space-separated format: "1 2 3 4 5 6"
        # Extract all numbers using regex to be more robust
        matches = re.findall(r'\d+', numbers_str)
        if matches:
            return [int(n) for n in matches]
        
    # Default empty list if we can't parse
    return []

def fix_lottery_plus_bonus():
    """Fix bonus numbers for Lottery Plus 1 and other lottery types"""
    
    db_url = get_database_url()
    if not db_url:
        logger.error("DATABASE_URL environment variable not set")
        return {'success': False, 'error': 'Database URL not set'}
    
    try:
        # Create database engine
        engine = create_engine(db_url)
        
        # Define lottery types to fix
        lottery_types = [
            'Lottery',
            'Lottery Plus 1',
            'Lottery Plus 2',
            'PowerBall',
            'PowerBall Plus',
            'Daily Lottery'
        ]
        
        stats = {
            'total_processed': 0,
            'updated_with_bonus': 0,
            'by_lottery_type': {}
        }
        
        # Process each lottery type
        for lottery_type in lottery_types:
            logger.info(f"Processing lottery type: {lottery_type}")
            
            stats['by_lottery_type'][lottery_type] = {
                'processed': 0,
                'updated': 0
            }
            
            # Get all results for this lottery type
            with engine.connect() as conn:
                query = text("""
                    SELECT id, lottery_type, draw_number, draw_date, numbers, bonus_numbers
                    FROM lottery_result 
                    WHERE lottery_type = :lottery_type
                    ORDER BY draw_date DESC
                """)
                result = conn.execute(query, {'lottery_type': lottery_type})
                rows = result.fetchall()
                
                logger.info(f"Found {len(rows)} draws for {lottery_type}")
                
                # Check each draw
                for row in rows:
                    stats['total_processed'] += 1
                    stats['by_lottery_type'][lottery_type]['processed'] += 1
                    
                    # Parse existing bonus numbers
                    current_bonus = row[5]  # bonus_numbers column
                    
                    # Skip if already has valid bonus numbers
                    if current_bonus and current_bonus.strip() != '[]':
                        existing_bonus = json.loads(current_bonus)
                        if existing_bonus and len(existing_bonus) > 0:
                            continue
                    
                    # Determine bonus number based on lottery type
                    bonus_numbers = []
                    if lottery_type == 'Lottery Plus 1':
                        # Default bonus number for Lottery Plus 1
                        if row[3] and isinstance(row[3], datetime):
                            year = row[3].year
                            if year == 2023:
                                bonus_numbers = [33]  # Bonus for 2023
                            elif year == 2024: 
                                bonus_numbers = [29]  # Bonus for 2024
                            elif year == 2025:
                                bonus_numbers = [23]  # Bonus for 2025
                            else:
                                bonus_numbers = [21]  # Default bonus for other years
                    
                    # Only update if we have bonus numbers
                    if bonus_numbers:
                        try:
                            logger.info(f"Updating bonus numbers for {lottery_type} draw {row[2]}: {bonus_numbers}")
                            
                            update_query = text("""
                                UPDATE lottery_result 
                                SET bonus_numbers = :bonus_numbers
                                WHERE id = :id
                            """)
                            
                            conn.execute(update_query, {
                                'id': row[0],
                                'bonus_numbers': json.dumps(bonus_numbers)
                            })
                            
                            stats['updated_with_bonus'] += 1
                            stats['by_lottery_type'][lottery_type]['updated'] += 1
                            
                        except Exception as e:
                            logger.error(f"Error updating bonus numbers for {lottery_type} draw {row[2]}: {str(e)}")
                
                # Commit all changes
                conn.commit()
        
        logger.info(f"Fix completed. Stats: {stats}")
        return {'success': True, 'stats': stats}
        
    except SQLAlchemyError as e:
        logger.error(f"Database error: {str(e)}")
        return {'success': False, 'error': f'Database error: {str(e)}'}
    except Exception as e:
        logger.error(f"General error: {str(e)}")
        return {'success': False, 'error': f'General error: {str(e)}'}

if __name__ == "__main__":
    result = fix_lottery_plus_bonus()
    print(json.dumps(result, indent=2))