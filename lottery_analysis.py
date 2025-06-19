"""
Lottery Analysis Module
Provides comprehensive lottery data analysis and visualization
"""
import logging
import json
from collections import Counter
from flask import Blueprint, jsonify, request
from models import db, LotteryResult
from datetime import datetime, timedelta
import io
import os

logger = logging.getLogger(__name__)

# Create blueprint
lottery_analysis_bp = Blueprint('lottery_analysis', __name__)

# Cache for analysis results
analysis_cache = {}

def get_optimized_lottery_stats():
    """Get lottery statistics with caching"""
    cache_key = "lottery_stats"
    
    if cache_key in analysis_cache:
        return analysis_cache[cache_key]
    
    try:
        # Get latest results
        latest_results = LotteryResult.query.order_by(LotteryResult.draw_date.desc()).limit(50).all()
        
        stats = {
            'total_draws': len(latest_results),
            'lottery_types': len(set([r.lottery_type for r in latest_results])),
            'latest_draw_date': latest_results[0].draw_date.strftime('%Y-%m-%d') if latest_results else None
        }
        
        analysis_cache[cache_key] = stats
        return stats
    except Exception as e:
        logger.error(f"Error getting lottery stats: {e}")
        return {}

@lottery_analysis_bp.route('/api/lottery-analysis/frequency')
def frequency_analysis():
    """API endpoint for frequency analysis"""
    logger.info("=== FREQUENCY ANALYSIS API CALLED ===")
    
    try:
        lottery_type = request.args.get('lottery_type')
        days = int(request.args.get('days', 365))
        
        logger.info(f"Performing optimized analysis for: lottery_type={lottery_type}, days={days}")
        
        # Check cache first
        cache_key = f"frequency_{lottery_type}_{days}"
        if cache_key in analysis_cache:
            logger.info(f"Returning cached frequency analysis for {cache_key}")
            return jsonify(analysis_cache[cache_key])
        
        # Get lottery results
        cutoff_date = datetime.now() - timedelta(days=days)
        
        query = LotteryResult.query.filter(LotteryResult.draw_date >= cutoff_date)
        if lottery_type and lottery_type != 'All Lottery Types':
            query = query.filter(LotteryResult.lottery_type == lottery_type)
        
        results = query.all()
        logger.info(f"Retrieved {len(results)} lottery results for analysis")
        
        # Process numbers
        all_numbers = []
        for result in results:
            try:
                if result.main_numbers:
                    numbers = json.loads(result.main_numbers) if isinstance(result.main_numbers, str) else result.main_numbers
                    if isinstance(numbers, list):
                        all_numbers.extend([int(n) for n in numbers if isinstance(n, (int, str)) and str(n).isdigit()])
            except Exception as e:
                logger.warning(f"Error processing numbers for result {result.id}: {e}")
                continue
        
        if not all_numbers:
            return jsonify({
                "All Lottery Types": {
                    "frequency": [0] * 50,
                    "top_numbers": [],
                    "chart_path": "",
                    "chart_base64": ""
                }
            })
        
        # Calculate frequency
        frequency = [0] * 50
        for num in all_numbers:
            if 1 <= num <= 50:
                frequency[num - 1] += 1
        
        # Get top numbers
        number_counts = {}
        for num in all_numbers:
            if 1 <= num <= 50:
                number_counts[num] = number_counts.get(num, 0) + 1
        
        top_numbers = sorted(number_counts.items(), key=lambda x: x[1], reverse=True)[:10]
        
        # Chart generation disabled to avoid numpy dependency
        chart_base64 = ""
        
        result = {
            (lottery_type or "All Lottery Types"): {
                "frequency": frequency,
                "top_numbers": top_numbers,
                "chart_path": f"/static/analysis/frequency_{lottery_type or 'All_Lottery_Types'}.png",
                "chart_base64": chart_base64
            }
        }
        
        # Cache the result for future requests
        analysis_cache[cache_key] = result
        logger.info(f"Cached frequency analysis result for {cache_key}")
        
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Error in frequency analysis: {e}")
        return jsonify({"error": str(e)}), 500

def generate_frequency_chart(frequency, lottery_type):
    """Placeholder chart generation function"""
    # Chart generation disabled to avoid numpy/matplotlib dependencies
    return ""

# Register blueprint
def init_lottery_analysis():
    """Initialize lottery analysis module"""
    logger.info("Lottery analysis routes registered")
    return lottery_analysis_bp

def register_analysis_routes(app, db):
    """Register lottery analysis routes with the Flask app"""
    app.register_blueprint(lottery_analysis_bp)
    logger.info("Lottery analysis routes registered")