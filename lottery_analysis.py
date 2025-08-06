"""
Lottery Analysis Module
Provides frequency analysis and statistics for lottery numbers
"""

from flask import Blueprint, jsonify, request
from models import db, LotteryResult
from datetime import datetime, timedelta
import json
import logging
from collections import Counter
from cache_manager import cached_query

logger = logging.getLogger(__name__)

# Create blueprint
bp = Blueprint('lottery_analysis', __name__, url_prefix='/api/lottery-analysis')

def map_frontend_to_db_lottery_type(frontend_type):
    """Map frontend lottery type names to database values"""
    mapping = {
        'Lottery': 'LOTTO',
        'Lottery Plus 1': 'LOTTO PLUS 1',
        'Lottery Plus 2': 'LOTTO PLUS 2',
        'Powerball': 'POWERBALL',
        'Powerball Plus': 'POWERBALL PLUS',
        'Daily Lottery': 'DAILY LOTTO'
    }
    return mapping.get(frontend_type, frontend_type)

@bp.route('/frequency')
def frequency_analysis():
    """Get frequency analysis of lottery numbers"""
    try:
        logger.info("=== FREQUENCY ANALYSIS API CALLED ===")
        
        # Get query parameters
        lottery_type = request.args.get('lottery_type')
        days = int(request.args.get('days', 365))
        
        # Map frontend lottery type to database value
        if lottery_type and lottery_type != 'all':
            lottery_type = map_frontend_to_db_lottery_type(lottery_type)
        
        logger.info(f"Performing optimized analysis for: lottery_type={lottery_type}, days={days}")
        
        # Use direct database connection to get real lottery data
        import psycopg2
        import os
        from collections import Counter
        
        connection_string = os.environ.get('DATABASE_URL')
        all_numbers = []
        lottery_types = set()
        
        try:
            with psycopg2.connect(connection_string) as conn:
                with conn.cursor() as cur:
                    # Get lottery results from the database (filtered by lottery type if specified)
                    if lottery_type and lottery_type != 'all':
                        cur.execute("""
                            SELECT lottery_type, main_numbers, bonus_numbers
                            FROM lottery_results 
                            WHERE main_numbers IS NOT NULL AND lottery_type = %s
                            ORDER BY draw_date DESC
                        """, (lottery_type,))
                    else:
                        cur.execute("""
                            SELECT lottery_type, main_numbers, bonus_numbers
                            FROM lottery_results 
                            WHERE main_numbers IS NOT NULL
                            ORDER BY draw_date DESC
                        """)
                    
                    results = cur.fetchall()
                    
                    for row in results:
                        row_lottery_type, numbers, bonus_numbers = row
                        lottery_types.add(row_lottery_type)
                        
                        # Add main numbers
                        if numbers:
                            parsed_numbers = []
                            
                            if isinstance(numbers, str):
                                try:
                                    # Handle PostgreSQL array format {1,2,3} or JSON format [1,2,3]
                                    if numbers.startswith('{') and numbers.endswith('}'):
                                        # PostgreSQL array format
                                        numbers_str = numbers.strip('{}')
                                        if numbers_str:
                                            parsed_numbers = [int(x.strip()) for x in numbers_str.split(',')]
                                    else:
                                        # JSON format
                                        parsed_numbers = json.loads(numbers)
                                except:
                                    continue
                            elif isinstance(numbers, list):
                                parsed_numbers = numbers
                            
                            all_numbers.extend(parsed_numbers)
                        
                        # Add bonus numbers  
                        if bonus_numbers:
                            parsed_bonus = []
                            
                            if isinstance(bonus_numbers, str):
                                try:
                                    # Handle PostgreSQL array format {1} or JSON format [1]
                                    if bonus_numbers.startswith('{') and bonus_numbers.endswith('}'):
                                        # PostgreSQL array format
                                        bonus_str = bonus_numbers.strip('{}')
                                        if bonus_str:
                                            parsed_bonus = [int(x.strip()) for x in bonus_str.split(',')]
                                    else:
                                        # JSON format
                                        parsed_bonus = json.loads(bonus_numbers)
                                except:
                                    continue
                            elif isinstance(bonus_numbers, list):
                                parsed_bonus = bonus_numbers
                            elif isinstance(bonus_numbers, (int, float)):
                                parsed_bonus = [int(bonus_numbers)]
                            
                            all_numbers.extend(parsed_bonus)
                        
        except Exception as e:
            logger.error(f"Database error in frequency analysis: {e}")
            all_numbers = []
            lottery_types = set()
        
        # Calculate frequency
        frequency = Counter(all_numbers)
        
        # Get top numbers (most frequent)
        top_numbers = frequency.most_common(50)
        
        # Get hot numbers (most frequent)
        hot_numbers = [num for num, freq in frequency.most_common(10)]
        
        # Get cold numbers (least frequent numbers that appear)
        cold_numbers = [num for num, freq in frequency.most_common()[-10:]]
        
        # Get absent numbers (numbers not in our data)
        all_possible_numbers = set(range(1, 53))  # SA lottery numbers typically 1-52
        present_numbers = set(all_numbers)
        absent_numbers = list(all_possible_numbers - present_numbers)[:10]
        
        response = {
            'lottery_types': list(lottery_types),
            'total_draws': len(results) if 'results' in locals() else 0,
            'total_numbers': len(all_numbers),
            'unique_numbers': len(set(all_numbers)),
            'frequency_data': [
                {
                    'number': num,
                    'frequency': freq,
                    'percentage': round((freq / len(all_numbers)) * 100, 2) if all_numbers else 0
                }
                for num, freq in top_numbers
            ],
            'hot_numbers': hot_numbers,
            'cold_numbers': cold_numbers,
            'absent_numbers': absent_numbers,
            'message': 'Real-time analytics from authentic lottery database'
        }
        
        logger.info(f"Returning real analytics data with {len(response['frequency_data'])} entries")
        return jsonify(response)
        
    except Exception as e:
        logger.error(f"Frequency analysis error: {e}")
        return jsonify({'error': str(e)}), 500

@bp.route('/stats')
@cached_query(ttl=600)
def lottery_stats():
    """Get general lottery statistics from authentic database"""
    try:
        import psycopg2
        import os
        
        connection_string = os.environ.get('DATABASE_URL')
        
        with psycopg2.connect(connection_string) as conn:
            with conn.cursor() as cur:
                # Get statistics per lottery type using real database
                cur.execute("""
                    SELECT lottery_type, 
                           COUNT(*) as total_draws,
                           MAX(draw_date) as latest_draw
                    FROM lottery_results 
                    GROUP BY lottery_type
                    ORDER BY lottery_type
                """)
                
                stats = cur.fetchall()
                
                lottery_types = []
                total_draws = 0
                
                for stat in stats:
                    lottery_type, draws_count, latest_draw = stat
                    lottery_types.append({
                        'type': lottery_type,
                        'total_draws': draws_count,
                        'latest_draw': latest_draw.isoformat() if latest_draw else None
                    })
                    total_draws += draws_count
        
        response = {
            'lottery_types': lottery_types,
            'total_draws': total_draws,
            'message': 'Statistics from authentic lottery database'
        }
        
        logger.info(f"Returning stats for {len(lottery_types)} lottery types, {total_draws} total draws")
        return jsonify(response)
        
    except Exception as e:
        logger.error(f"Stats error: {e}")
        return jsonify({'error': str(e)}), 500

@bp.route('/patterns')
@cached_query(ttl=900)
def pattern_analysis():
    """Analyze number patterns from authentic lottery data"""
    try:
        import psycopg2
        import os
        from datetime import datetime, timedelta
        
        connection_string = os.environ.get('DATABASE_URL')
        all_numbers = []
        consecutive_pairs = []
        even_count = 0
        odd_count = 0
        
        with psycopg2.connect(connection_string) as conn:
            with conn.cursor() as cur:
                # Get recent results (last 90 days) with proper type handling
                ninety_days_ago = (datetime.now() - timedelta(days=90)).date()
                
                cur.execute("""
                    SELECT main_numbers::text, bonus_numbers::text 
                    FROM lottery_results 
                    WHERE draw_date >= %s AND main_numbers IS NOT NULL
                    ORDER BY draw_date DESC
                """, (ninety_days_ago,))
                
                results = cur.fetchall()
                
                for row in results:
                    main_numbers, bonus_numbers = row
                    
                    # Parse main numbers
                    if main_numbers:
                        parsed_numbers = []
                        if isinstance(main_numbers, str):
                            if main_numbers.startswith('[') and main_numbers.endswith(']'):
                                parsed_numbers = json.loads(main_numbers)
                            elif main_numbers.startswith('{') and main_numbers.endswith('}'):
                                numbers_str = main_numbers.strip('{}')
                                if numbers_str:
                                    parsed_numbers = [int(x.strip()) for x in numbers_str.split(',')]
                        elif isinstance(main_numbers, list):
                            parsed_numbers = main_numbers
                        
                        all_numbers.extend(parsed_numbers)
                        
                        # Check for consecutive pairs
                        sorted_nums = sorted(parsed_numbers)
                        for i in range(len(sorted_nums) - 1):
                            if sorted_nums[i+1] - sorted_nums[i] == 1:
                                consecutive_pairs.append((sorted_nums[i], sorted_nums[i+1]))
                        
                        # Count even/odd
                        for num in parsed_numbers:
                            if num % 2 == 0:
                                even_count += 1
                            else:
                                odd_count += 1
        
        # Calculate patterns
        total_numbers = len(all_numbers)
        frequency = Counter(all_numbers)
        
        patterns = {
            'consecutive_pairs': list(set(consecutive_pairs))[:10],
            'even_odd_ratio': {
                'even': round((even_count / total_numbers) * 100, 1) if total_numbers > 0 else 0,
                'odd': round((odd_count / total_numbers) * 100, 1) if total_numbers > 0 else 0
            },
            'hot_numbers': [num for num, freq in frequency.most_common(10)],
            'cold_numbers': [num for num, freq in frequency.most_common()[-10:]],
            'total_draws_analyzed': len(results),
            'total_numbers_analyzed': total_numbers,
            'message': 'Pattern analysis from authentic lottery database'
        }
        
        logger.info(f"Pattern analysis complete: {patterns['total_draws_analyzed']} draws, {patterns['total_numbers_analyzed']} numbers")
        return jsonify(patterns)
        
    except Exception as e:
        logger.error(f"Pattern analysis error: {e}")
        return jsonify({'error': str(e)}), 500
        
        # Analyze patterns (simplified)
        all_numbers = []
        for result in results:
            if result.numbers:
                try:
                    if isinstance(result.numbers, str):
                        numbers = json.loads(result.numbers)
                    else:
                        numbers = result.numbers
                    
                    if isinstance(numbers, list):
                        all_numbers.extend(numbers)
                except:
                    pass
        
        # Calculate frequency for hot/cold numbers
        frequency = Counter(all_numbers)
        patterns['hot_numbers'] = frequency.most_common(10)
        patterns['cold_numbers'] = frequency.most_common()[-10:]
        
        return jsonify(patterns)
        
    except Exception as e:
        logger.error(f"Pattern analysis error: {e}")
        return jsonify({'error': str(e)}), 500