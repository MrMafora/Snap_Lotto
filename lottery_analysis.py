"""
Lottery Analysis Module
Provides comprehensive lottery data analysis and visualization
"""
import logging
import json
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import seaborn as sns
from flask import Blueprint, jsonify, request
from models import db, LotteryResult
from datetime import datetime, timedelta
import base64
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
        
        # Clear cache to force fresh data
        analysis_cache.clear()
        logger.info("Cleared all cached analysis results to force fresh integer-safe processing")
        
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
                if result.numbers:
                    numbers = json.loads(result.numbers) if isinstance(result.numbers, str) else result.numbers
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
        
        # Generate chart
        chart_base64 = generate_frequency_chart(frequency, lottery_type or "All Lottery Types")
        
        result = {
            (lottery_type or "All Lottery Types"): {
                "frequency": frequency,
                "top_numbers": top_numbers,
                "chart_path": f"/static/analysis/frequency_{lottery_type or 'All_Lottery_Types'}.png",
                "chart_base64": chart_base64
            }
        }
        
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Error in frequency analysis: {e}")
        return jsonify({"error": str(e)}), 500

def generate_frequency_chart(frequency, lottery_type):
    """Generate frequency chart and return base64 encoded image"""
    try:
        plt.figure(figsize=(16, 8))
        
        numbers = list(range(1, 51))
        bars = plt.bar(numbers, frequency, alpha=0.7, color='steelblue')
        
        # Highlight top numbers
        max_freq = max(frequency) if frequency else 0
        for i, freq in enumerate(frequency):
            if freq == max_freq and freq > 0:
                bars[i].set_color('red')
                bars[i].set_alpha(0.8)
        
        plt.xlabel('Lottery Numbers')
        plt.ylabel('Frequency')
        plt.title(f'Number Frequency Analysis - {lottery_type}')
        plt.grid(True, alpha=0.3)
        plt.tight_layout()
        
        # Convert to base64
        img_buffer = io.BytesIO()
        plt.savefig(img_buffer, format='png', dpi=100, bbox_inches='tight')
        img_buffer.seek(0)
        img_base64 = base64.b64encode(img_buffer.getvalue()).decode()
        plt.close()
        
        return img_base64
        
    except Exception as e:
        logger.error(f"Error generating chart: {e}")
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