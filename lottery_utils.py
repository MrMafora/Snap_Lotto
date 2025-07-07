"""
Lottery Utilities Module
Extracted from main.py for better code organization (Phase 2 refactoring)
Contains lottery-specific data processing and analysis functions
"""

import json
import logging
from datetime import datetime
from models import db, LotteryResult

logger = logging.getLogger(__name__)

class LotteryDisplay:
    """Helper class for displaying lottery results"""
    def __init__(self, lottery_type, draw_number, draw_date, numbers, bonus_numbers):
        self.lottery_type = lottery_type
        self.draw_number = draw_number
        self.draw_date = draw_date
        self.numbers = numbers
        self.bonus_numbers = bonus_numbers
    
    def get_numbers_list(self):
        """Convert numbers string/list to list of integers"""
        if isinstance(self.numbers, str):
            try:
                return json.loads(self.numbers.replace("'", '"'))
            except:
                return []
        return self.numbers or []
    
    def get_bonus_numbers_list(self):
        """Convert bonus numbers string/list to list of integers"""
        if isinstance(self.bonus_numbers, str):
            try:
                return json.loads(self.bonus_numbers.replace("'", '"'))
            except:
                return []
        return self.bonus_numbers or []

def calculate_frequency_analysis(results):
    """Calculate frequency analysis from lottery results for charts"""
    from collections import Counter
    
    all_numbers = []
    
    for result in results:
        # Parse main numbers
        if hasattr(result, 'main_numbers') and result.main_numbers:
            try:
                if isinstance(result.main_numbers, str):
                    numbers = json.loads(result.main_numbers.replace("'", '"'))
                else:
                    numbers = result.main_numbers
                all_numbers.extend(numbers)
            except:
                continue
        
        # Parse bonus numbers  
        if hasattr(result, 'bonus_numbers') and result.bonus_numbers:
            try:
                if isinstance(result.bonus_numbers, str):
                    bonus = json.loads(result.bonus_numbers.replace("'", '"'))
                else:
                    bonus = result.bonus_numbers
                if isinstance(bonus, list):
                    all_numbers.extend(bonus)
                elif isinstance(bonus, int):
                    all_numbers.append(bonus)
            except:
                continue
    
    # Count frequencies
    frequency_counter = Counter(all_numbers)
    
    # Get top 10 most frequent numbers
    top_10 = frequency_counter.most_common(10)
    
    total_numbers = len(set(all_numbers))
    
    logger.info(f"Frequency analysis: Found {total_numbers} unique numbers, top 10: {top_10}")
    
    return {
        'total_unique_numbers': total_numbers,
        'top_10_numbers': top_10,
        'all_frequencies': dict(frequency_counter)
    }

def get_optimized_latest_results(limit=10):
    """Get latest lottery results optimized for display"""
    try:
        results = db.session.query(LotteryResult)\
            .order_by(LotteryResult.draw_date.desc())\
            .limit(limit)\
            .all()
        
        logger.info(f"Loaded {len(results)} latest results from database")
        
        return results
    except Exception as e:
        logger.error(f"Error fetching latest results: {e}")
        return []

def format_lottery_numbers(numbers):
    """Format lottery numbers for display"""
    if isinstance(numbers, str):
        try:
            numbers = json.loads(numbers.replace("'", '"'))
        except:
            return "N/A"
    
    if isinstance(numbers, list):
        return ', '.join(map(str, numbers))
    
    return str(numbers) if numbers else "N/A"

def parse_lottery_divisions(divisions_data):
    """Parse lottery prize divisions from JSON data"""
    if not divisions_data:
        return []
    
    try:
        if isinstance(divisions_data, str):
            divisions = json.loads(divisions_data)
        else:
            divisions = divisions_data
        
        # Handle different division formats
        if isinstance(divisions, dict):
            # Convert dict to list format
            division_list = []
            for key, value in divisions.items():
                if isinstance(value, dict):
                    division_list.append(value)
                else:
                    division_list.append({'division': key, 'details': value})
            return division_list
        elif isinstance(divisions, list):
            return divisions
        
    except Exception as e:
        logger.error(f"Error parsing divisions: {e}")
    
    return []

def get_lottery_statistics_summary():
    """Get summary statistics for all lottery types"""
    try:
        from sqlalchemy import text
        
        query = text("""
            SELECT 
                lottery_type,
                COUNT(*) as total_draws,
                MAX(draw_number) as latest_draw,
                MAX(draw_date) as latest_date,
                MIN(draw_date) as earliest_date
            FROM lottery_result 
            GROUP BY lottery_type 
            ORDER BY lottery_type
        """)
        
        result = db.session.execute(query)
        stats = result.fetchall()
        
        return [dict(row._mapping) for row in stats]
        
    except Exception as e:
        logger.error(f"Error getting lottery statistics: {e}")
        return []