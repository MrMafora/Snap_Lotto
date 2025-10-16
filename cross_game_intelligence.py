#!/usr/bin/env python3
"""
Cross-Game Intelligence System
Shares insights between lottery games with the same number pool
(LOTTO, LOTTO PLUS 1, LOTTO PLUS 2 all use 1-52)
"""

import logging
import psycopg2
import json
import os
from collections import Counter
from typing import Dict, List, Tuple
import pandas as pd

logger = logging.getLogger(__name__)

# Games that share the same number pool
SHARED_POOL_GROUPS = {
    'LOTTO_FAMILY': ['LOTTO', 'LOTTO PLUS 1', 'LOTTO PLUS 2'],  # 1-52
    'POWERBALL_FAMILY': ['POWERBALL', 'POWERBALL PLUS'],  # Main: 1-50
    'DAILY_LOTTO_FAMILY': ['DAILY LOTTO']  # 1-36 (standalone)
}


def get_game_family(lottery_type: str) -> List[str]:
    """Get all games that share the same number pool"""
    for family_games in SHARED_POOL_GROUPS.values():
        if lottery_type in family_games:
            return family_games
    return [lottery_type]  # Standalone game


def get_cross_game_frequency_boost(lottery_type: str, number: int, days_back: int = 180) -> float:
    """
    Calculate frequency boost from related games
    If a number is hot in LOTTO, it's likely hot in LOTTO PLUS too
    
    Returns:
        Boost factor (0.0 to 1.0) to add to number's score
    """
    try:
        family_games = get_game_family(lottery_type)
        
        # If standalone game, no cross-game boost
        if len(family_games) <= 1:
            return 0.0
        
        # Get frequency from all family games
        connection_string = os.environ.get('DATABASE_URL')
        conn = psycopg2.connect(connection_string)
        cur = conn.cursor()
        
        # Count appearances across ALL games in family
        total_appearances = 0
        total_possible = 0
        
        for game_type in family_games:
            cur.execute('''
                SELECT main_numbers
                FROM lottery_results
                WHERE lottery_type = %s
                  AND draw_date >= CURRENT_DATE - make_interval(days => %s)
                ORDER BY draw_date DESC
                LIMIT 30
            ''', (game_type, days_back))
            
            results = cur.fetchall()
            
            for (main_nums,) in results:
                # Parse numbers
                if isinstance(main_nums, str):
                    if main_nums.startswith('{') and main_nums.endswith('}'):
                        nums_str = main_nums.strip('{}')
                        if nums_str:
                            numbers = [int(x.strip()) for x in nums_str.split(',')]
                        else:
                            continue
                    else:
                        numbers = json.loads(main_nums)
                elif isinstance(main_nums, list):
                    numbers = main_nums
                else:
                    continue
                
                if number in numbers:
                    total_appearances += 1
                total_possible += 1
        
        cur.close()
        conn.close()
        
        if total_possible == 0:
            return 0.0
        
        # Calculate frequency across all games
        cross_game_frequency = total_appearances / total_possible
        
        # Convert to boost (0.0 to 0.15 boost)
        # Hot in family = up to 15% boost
        boost = min(cross_game_frequency * 0.15, 0.15)
        
        logger.debug(f"Cross-game boost for {number} in {lottery_type}: {boost:.3f} ({total_appearances}/{total_possible} appearances)")
        
        return boost
        
    except Exception as e:
        logger.warning(f"Error calculating cross-game boost: {e}")
        return 0.0


def get_cross_game_hot_numbers(lottery_type: str, top_n: int = 10, days_back: int = 90) -> List[int]:
    """
    Get hot numbers across entire game family
    More reliable than single-game analysis
    """
    try:
        family_games = get_game_family(lottery_type)
        
        connection_string = os.environ.get('DATABASE_URL')
        conn = psycopg2.connect(connection_string)
        cur = conn.cursor()
        
        # Collect all numbers from family games
        all_numbers = []
        
        for game_type in family_games:
            cur.execute('''
                SELECT main_numbers
                FROM lottery_results
                WHERE lottery_type = %s
                  AND draw_date >= CURRENT_DATE - make_interval(days => %s)
                ORDER BY draw_date DESC
                LIMIT 50
            ''', (game_type, days_back))
            
            results = cur.fetchall()
            
            for (main_nums,) in results:
                # Parse numbers
                if isinstance(main_nums, str):
                    if main_nums.startswith('{') and main_nums.endswith('}'):
                        nums_str = main_nums.strip('{}')
                        if nums_str:
                            numbers = [int(x.strip()) for x in nums_str.split(',')]
                            all_numbers.extend(numbers)
                    else:
                        numbers = json.loads(main_nums)
                        all_numbers.extend(numbers)
                elif isinstance(main_nums, list):
                    all_numbers.extend(main_nums)
        
        cur.close()
        conn.close()
        
        if not all_numbers:
            return []
        
        # Get top N most frequent
        frequency = Counter(all_numbers)
        hot_numbers = [num for num, _ in frequency.most_common(top_n)]
        
        logger.info(f"Cross-game hot numbers for {lottery_type} family: {hot_numbers}")
        
        return hot_numbers
        
    except Exception as e:
        logger.warning(f"Error getting cross-game hot numbers: {e}")
        return []


def get_cross_game_cold_numbers(lottery_type: str, top_n: int = 10, days_back: int = 90) -> List[int]:
    """
    Get cold numbers across entire game family
    Numbers that haven't appeared recently across ALL family games
    """
    try:
        family_games = get_game_family(lottery_type)
        
        connection_string = os.environ.get('DATABASE_URL')
        conn = psycopg2.connect(connection_string)
        cur = conn.cursor()
        
        # Collect all numbers from family games
        all_numbers = []
        
        for game_type in family_games:
            cur.execute('''
                SELECT main_numbers
                FROM lottery_results
                WHERE lottery_type = %s
                  AND draw_date >= CURRENT_DATE - make_interval(days => %s)
                ORDER BY draw_date DESC
                LIMIT 50
            ''', (game_type, days_back))
            
            results = cur.fetchall()
            
            for (main_nums,) in results:
                # Parse numbers
                if isinstance(main_nums, str):
                    if main_nums.startswith('{') and main_nums.endswith('}'):
                        nums_str = main_nums.strip('{}')
                        if nums_str:
                            numbers = [int(x.strip()) for x in nums_str.split(',')]
                            all_numbers.extend(numbers)
                    else:
                        numbers = json.loads(main_nums)
                        all_numbers.extend(numbers)
                elif isinstance(main_nums, list):
                    all_numbers.extend(main_nums)
        
        cur.close()
        conn.close()
        
        if not all_numbers:
            return []
        
        # Get top N least frequent
        frequency = Counter(all_numbers)
        # Get numbers in valid range that appear least
        # For LOTTO family: 1-52
        if lottery_type in SHARED_POOL_GROUPS['LOTTO_FAMILY']:
            valid_range = range(1, 53)
        elif lottery_type in SHARED_POOL_GROUPS['POWERBALL_FAMILY']:
            valid_range = range(1, 51)
        else:  # DAILY LOTTO
            valid_range = range(1, 37)
        
        # Include all numbers in range, even if they didn't appear (0 frequency)
        for num in valid_range:
            if num not in frequency:
                frequency[num] = 0
        
        cold_numbers = [num for num, _ in frequency.most_common()[-top_n:]]
        
        logger.info(f"Cross-game cold numbers for {lottery_type} family: {cold_numbers}")
        
        return cold_numbers
        
    except Exception as e:
        logger.warning(f"Error getting cross-game cold numbers: {e}")
        return []


def get_cross_game_intelligence_summary(lottery_type: str) -> Dict:
    """
    Get comprehensive cross-game intelligence summary
    Returns insights from all games in the family
    """
    try:
        family_games = get_game_family(lottery_type)
        
        intelligence = {
            'lottery_type': lottery_type,
            'game_family': family_games,
            'family_size': len(family_games),
            'cross_game_hot': get_cross_game_hot_numbers(lottery_type, top_n=10),
            'cross_game_cold': get_cross_game_cold_numbers(lottery_type, top_n=10),
            'shared_pool': len(family_games) > 1
        }
        
        logger.info(f"📊 Cross-Game Intelligence for {lottery_type}:")
        logger.info(f"   Family: {family_games}")
        logger.info(f"   Hot across family: {intelligence['cross_game_hot']}")
        logger.info(f"   Cold across family: {intelligence['cross_game_cold']}")
        
        return intelligence
        
    except Exception as e:
        logger.error(f"Error generating cross-game intelligence: {e}")
        return {
            'lottery_type': lottery_type,
            'error': str(e)
        }


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    # Test cross-game intelligence
    print("Testing Cross-Game Intelligence...")
    
    for lottery_type in ['LOTTO', 'LOTTO PLUS 1', 'POWERBALL', 'DAILY LOTTO']:
        print(f"\n{'='*60}")
        summary = get_cross_game_intelligence_summary(lottery_type)
        print(f"Lottery: {lottery_type}")
        print(f"Family: {summary.get('game_family', [])}")
        print(f"Hot: {summary.get('cross_game_hot', [])}")
        print(f"Cold: {summary.get('cross_game_cold', [])}")
