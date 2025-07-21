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

@bp.route('/frequency')
def frequency_analysis():
    """Get frequency analysis of lottery numbers"""
    try:
        logger.info("=== FREQUENCY ANALYSIS API CALLED ===")
        
        # Get query parameters
        lottery_type = request.args.get('lottery_type')
        days = int(request.args.get('days', 365))
        
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
                            SELECT lottery_type, numbers, bonus_numbers
                            FROM lottery_result 
                            WHERE numbers IS NOT NULL AND lottery_type = %s
                            ORDER BY draw_date DESC
                        """, (lottery_type,))
                    else:
                        cur.execute("""
                            SELECT lottery_type, numbers, bonus_numbers
                            FROM lottery_result 
                            WHERE numbers IS NOT NULL
                            ORDER BY draw_date DESC
                        """)
                    
                    results = cur.fetchall()
                    
                    for row in results:
                        row_lottery_type, numbers, bonus_numbers = row
                        lottery_types.add(row_lottery_type)
                        
                        # Add main numbers
                        if numbers:
                            if isinstance(numbers, str):
                                try:
                                    numbers = json.loads(numbers)
                                except:
                                    continue
                            if isinstance(numbers, list):
                                all_numbers.extend(numbers)
                        
                        # Add bonus numbers  
                        if bonus_numbers:
                            if isinstance(bonus_numbers, str):
                                try:
                                    bonus_numbers = json.loads(bonus_numbers)
                                except:
                                    continue
                            if isinstance(bonus_numbers, list):
                                all_numbers.extend(bonus_numbers)
                            elif isinstance(bonus_numbers, (int, float)):
                                all_numbers.append(int(bonus_numbers))
                        
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
    """Get general lottery statistics"""
    try:
        # Get total draws per lottery type
        stats = db.session.query(
            LotteryResult.lottery_type,
            db.func.count(LotteryResult.id).label('total_draws'),
            db.func.max(LotteryResult.draw_date).label('latest_draw')
        ).group_by(LotteryResult.lottery_type).all()
        
        response = {
            'lottery_types': [
                {
                    'type': stat.lottery_type,
                    'total_draws': stat.total_draws,
                    'latest_draw': stat.latest_draw.isoformat() if stat.latest_draw else None
                }
                for stat in stats
            ],
            'total_draws': sum(stat.total_draws for stat in stats)
        }
        
        return jsonify(response)
        
    except Exception as e:
        logger.error(f"Stats error: {e}")
        return jsonify({'error': str(e)}), 500

@bp.route('/patterns')
@cached_query(ttl=900)
def pattern_analysis():
    """Analyze number patterns"""
    try:
        # Get recent results
        results = db.session.query(LotteryResult).filter(
            LotteryResult.draw_date >= datetime.now().date() - timedelta(days=90)
        ).all()
        
        patterns = {
            'consecutive_pairs': [],
            'even_odd_ratio': {},
            'sum_ranges': {},
            'hot_numbers': [],
            'cold_numbers': []
        }
        
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