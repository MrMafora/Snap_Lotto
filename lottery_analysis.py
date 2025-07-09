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
@cached_query(ttl=300)
def frequency_analysis():
    """Get frequency analysis of lottery numbers"""
    try:
        logger.info("=== FREQUENCY ANALYSIS API CALLED ===")
        
        # Get query parameters
        lottery_type = request.args.get('lottery_type')
        days = int(request.args.get('days', 365))
        
        logger.info(f"Performing optimized analysis for: lottery_type={lottery_type}, days={days}")
        
        # Calculate date range
        end_date = datetime.now().date()
        start_date = end_date - timedelta(days=days)
        
        # Build query
        query = db.session.query(LotteryResult).filter(
            LotteryResult.draw_date >= start_date,
            LotteryResult.draw_date <= end_date
        )
        
        if lottery_type and lottery_type != 'All Lottery Types':
            query = query.filter(LotteryResult.lottery_type == lottery_type)
        
        # Get results
        results = query.all()
        logger.info(f"Retrieved {len(results)} lottery results for analysis")
        
        # Extract all numbers
        all_numbers = []
        lottery_types = set()
        
        for result in results:
            lottery_types.add(result.lottery_type)
            
            # Parse main numbers
            if result.numbers:
                try:
                    if isinstance(result.numbers, str):
                        numbers = json.loads(result.numbers)
                    else:
                        numbers = result.numbers
                    
                    if isinstance(numbers, list):
                        all_numbers.extend(numbers)
                except (json.JSONDecodeError, TypeError):
                    pass
            
            # Parse bonus numbers
            if result.bonus_numbers:
                try:
                    if isinstance(result.bonus_numbers, str):
                        bonus_numbers = json.loads(result.bonus_numbers)
                    else:
                        bonus_numbers = result.bonus_numbers
                    
                    if isinstance(bonus_numbers, list):
                        all_numbers.extend(bonus_numbers)
                except (json.JSONDecodeError, TypeError):
                    pass
        
        # Calculate frequency
        frequency = Counter(all_numbers)
        
        # Get top numbers
        top_numbers = frequency.most_common(50)
        
        # Prepare response
        response = {
            'lottery_types': list(lottery_types),
            'total_draws': len(results),
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
            'date_range': {
                'start': start_date.isoformat(),
                'end': end_date.isoformat(),
                'days': days
            }
        }
        
        logger.info(f"Cached frequency analysis result for frequency_{lottery_type}_{days}")
        
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