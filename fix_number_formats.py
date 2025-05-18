#!/usr/bin/env python3
"""
Fix the lottery number formats in the database to ensure consistent type handling.
This script converts any string numbers to proper JSON arrays with string elements
to ensure consistent processing in the analysis tools.
"""

import os
import sys
import json
from datetime import datetime
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('number_formats')

# Initialize Flask app and database
from flask import Flask
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL")
app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
    "pool_recycle": 300,
    "pool_pre_ping": True,
}
db = SQLAlchemy(app)

# Import the models
from models import LotteryResult

def normalize_numbers_array(numbers):
    """
    Convert numbers to a consistent format: list of strings
    
    Args:
        numbers: The numbers in any format (string, list, JSON string)
        
    Returns:
        list: List of strings representing the numbers
    """
    # Handle empty data
    if not numbers:
        return []
    
    # Already a list of strings
    if isinstance(numbers, list) and all(isinstance(n, str) for n in numbers):
        return numbers
    
    # String representation of a list
    if isinstance(numbers, str) and numbers.startswith('[') and numbers.endswith(']'):
        try:
            parsed = json.loads(numbers)
            # Convert all elements to strings
            return [str(n) for n in parsed]
        except json.JSONDecodeError:
            logger.warning(f"Failed to parse JSON string: {numbers}")
            # Try to parse as comma-separated values
            try:
                return [str(n.strip()) for n in numbers.strip('[]').split(',')]
            except Exception:
                logger.error(f"Could not parse as CSV either: {numbers}")
                return []
    
    # List of non-string elements
    if isinstance(numbers, list):
        return [str(n) for n in numbers]
    
    # Single string that might be comma-separated
    if isinstance(numbers, str):
        return [str(n.strip()) for n in numbers.split(',')]
    
    # Unknown format
    logger.warning(f"Unknown number format: {numbers} (type: {type(numbers)})")
    return []

def fix_number_formats():
    """
    Fix number formats in the database for all lottery results.
    Converts all numbers to consistent string arrays in JSON format.
    """
    with app.app_context():
        # Get all lottery results
        results = LotteryResult.query.all()
        logger.info(f"Found {len(results)} lottery results to process")
        
        fixed_count = 0
        for result in results:
            try:
                # Check and fix main numbers
                original_numbers = result.numbers
                fixed_numbers = normalize_numbers_array(original_numbers)
                
                # Check and fix bonus numbers
                original_bonus = result.bonus_numbers
                fixed_bonus = normalize_numbers_array(original_bonus)
                
                # Update if changed
                if fixed_numbers != original_numbers or fixed_bonus != original_bonus:
                    result.numbers = fixed_numbers
                    result.bonus_numbers = fixed_bonus
                    fixed_count += 1
                    db.session.add(result)
            except Exception as e:
                logger.error(f"Error fixing result {result.id}: {e}")
        
        # Commit changes
        if fixed_count > 0:
            db.session.commit()
            logger.info(f"Fixed {fixed_count} lottery results with number format issues")
        else:
            logger.info("No number format issues found")

def check_lottery_number_formats():
    """
    Check and report on the various number formats in the database.
    """
    with app.app_context():
        results = LotteryResult.query.all()
        logger.info(f"Checking number formats for {len(results)} lottery results")
        
        # Track format types
        format_types = {
            'list_of_strings': 0,
            'list_of_ints': 0,
            'json_string': 0,
            'csv_string': 0,
            'other': 0
        }
        
        for result in results:
            numbers = result.numbers
            
            if isinstance(numbers, list):
                if all(isinstance(n, str) for n in numbers):
                    format_types['list_of_strings'] += 1
                elif all(isinstance(n, int) for n in numbers):
                    format_types['list_of_ints'] += 1
                else:
                    format_types['other'] += 1
            elif isinstance(numbers, str):
                if numbers.startswith('[') and numbers.endswith(']'):
                    format_types['json_string'] += 1
                else:
                    format_types['csv_string'] += 1
            else:
                format_types['other'] += 1
        
        # Display results
        logger.info("Number format analysis:")
        for format_type, count in format_types.items():
            logger.info(f"  {format_type}: {count}")

if __name__ == "__main__":
    # Check formats first
    check_lottery_number_formats()
    
    # Fix number formats
    fix_number_formats()
    
    # Check formats again to verify
    check_lottery_number_formats()