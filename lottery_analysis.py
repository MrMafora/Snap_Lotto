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
from security_utils import require_admin

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

@bp.route('/ai-patterns')
def ai_pattern_analysis():
    """AI-powered comprehensive pattern analysis using Google Gemini"""
    try:
        from gemini_pattern_analyzer import get_comprehensive_ai_analysis
        
        # Get query parameters
        lottery_type = request.args.get('lottery_type', 'all')
        days = int(request.args.get('days', 180))
        
        logger.info(f"Starting AI pattern analysis for: {lottery_type}, {days} days")
        
        # Get comprehensive AI analysis
        analysis_result = get_comprehensive_ai_analysis(lottery_type, days)
        
        if 'error' in analysis_result:
            logger.error(f"AI analysis error: {analysis_result['error']}")
            return jsonify(analysis_result), 500
            
        logger.info(f"AI analysis completed: {len(analysis_result.get('pattern_analyses', []))} patterns, {len(analysis_result.get('game_analyses', []))} game analyses")
        
        return jsonify(analysis_result)
        
    except Exception as e:
        logger.error(f"AI pattern analysis error: {e}")
        return jsonify({
            'error': str(e),
            'pattern_analyses': [],
            'game_analyses': [],
            'ai_summary': 'AI analysis temporarily unavailable.'
        }), 500

@bp.route('/game-insights')
def game_type_insights():
    """Get AI insights for specific game types"""
    try:
        from gemini_pattern_analyzer import get_lottery_data_for_ai, analyze_game_types_with_ai
        
        # Get query parameters
        lottery_type = request.args.get('lottery_type')
        days = int(request.args.get('days', 90))
        
        if not lottery_type or lottery_type == 'all':
            return jsonify({'error': 'Specific lottery type required for game insights'}), 400
            
        # Map frontend to database type
        db_lottery_type = map_frontend_to_db_lottery_type(lottery_type)
        
        logger.info(f"Getting game insights for: {db_lottery_type}")
        
        # Get lottery data
        lottery_data = get_lottery_data_for_ai(db_lottery_type, days)
        
        if not lottery_data:
            return jsonify({'error': f'No data available for {lottery_type}'}), 404
            
        # Analyze with AI
        game_analyses = analyze_game_types_with_ai(lottery_data)
        
        return jsonify({
            'success': True,
            'lottery_type': lottery_type,
            'game_analyses': [g.dict() for g in game_analyses],
            'data_period_days': days,
            'total_draws': sum(len(data['draws']) for data in lottery_data.values())
        })
        
    except Exception as e:
        logger.error(f"Game insights error: {e}")
        return jsonify({'error': str(e)}), 500

@bp.route('/predictions')
@require_admin
def get_lottery_predictions():
    """Get AI-generated lottery predictions for upcoming draws"""
    try:
        from ai_lottery_predictor import predictor
        
        # Get query parameters
        game_type = request.args.get('game_type', 'LOTTO')
        generate_new = request.args.get('generate_new', 'false').lower() == 'true'
        
        # Map frontend to database type
        db_game_type = map_frontend_to_db_lottery_type(game_type)
        
        logger.info(f"Getting predictions for: {db_game_type}, generate_new: {generate_new}")
        
        if generate_new:
            # Generate new prediction
            historical_data = predictor.get_historical_data_for_prediction(db_game_type, 365)
            prediction = predictor.generate_ai_prediction(db_game_type, historical_data)
            prediction_id = predictor.save_prediction(prediction)
            
            response = {
                'success': True,
                'prediction_id': prediction_id,
                'game_type': game_type,
                'prediction': prediction.dict(),
                'is_new': True
            }
        else:
            # Get existing predictions
            with psycopg2.connect(os.environ.get('DATABASE_URL')) as conn:
                with conn.cursor() as cur:
                    cur.execute("""
                        SELECT id, predicted_numbers, bonus_numbers, confidence_score,
                               prediction_method, reasoning, target_draw_date, created_at,
                               is_verified, accuracy_score
                        FROM lottery_predictions 
                        WHERE game_type = %s 
                        ORDER BY created_at DESC 
                        LIMIT 5
                    """, (db_game_type,))
                    
                    results = cur.fetchall()
                    predictions = []
                    
                    for row in results:
                        predictions.append({
                            'id': row[0],
                            'predicted_numbers': row[1],
                            'bonus_numbers': row[2] or [],
                            'confidence_score': row[3],
                            'prediction_method': row[4],
                            'reasoning': row[5],
                            'target_draw_date': row[6].isoformat() if row[6] else None,
                            'created_at': row[7].isoformat() if row[7] else None,
                            'is_verified': row[8],
                            'accuracy_score': row[9]
                        })
                    
                    response = {
                        'success': True,
                        'game_type': game_type,
                        'predictions': predictions,
                        'is_new': False
                    }
        
        return jsonify(response)
        
    except Exception as e:
        logger.error(f"Predictions error: {e}")
        return jsonify({'error': 'Prediction system temporarily unavailable'}), 500

@bp.route('/prediction-accuracy')
@require_admin
def get_prediction_accuracy():
    """Get accuracy statistics for AI predictions"""
    try:
        from ai_lottery_predictor import predictor
        
        # Get query parameters
        game_type = request.args.get('game_type')
        days = int(request.args.get('days', 90))
        
        # Map frontend to database type if specified
        db_game_type = None
        if game_type and game_type != 'all':
            db_game_type = map_frontend_to_db_lottery_type(game_type)
        
        logger.info(f"Getting prediction accuracy for: {db_game_type}, {days} days")
        
        # Verify recent predictions first
        accuracy_results = predictor.verify_predictions()
        
        # Get performance statistics
        performance_stats = predictor.get_prediction_performance_stats(db_game_type, days)
        
        response = {
            'success': True,
            'game_type': game_type or 'all',
            'period_days': days,
            'recent_verifications': len(accuracy_results),
            'performance_stats': performance_stats,
            'last_verified': [acc.dict() for acc in accuracy_results[:5]]  # Last 5 verifications
        }
        
        return jsonify(response)
        
    except Exception as e:
        logger.error(f"Prediction accuracy error: {e}")
        return jsonify({'error': 'Accuracy tracking temporarily unavailable'}), 500

@bp.route('/generate-prediction', methods=['POST'])
@require_admin
def generate_new_prediction():
    """Generate a new AI prediction for specified game"""
    try:
        from ai_lottery_predictor import predictor
        
        data = request.get_json() or {}
        game_type = data.get('game_type', 'LOTTO')
        
        # Map frontend to database type
        db_game_type = map_frontend_to_db_lottery_type(game_type)
        
        logger.info(f"Generating new prediction for: {db_game_type}")
        
        # Get historical data and generate prediction
        historical_data = predictor.get_historical_data_for_prediction(db_game_type, 365)
        prediction = predictor.generate_ai_prediction(db_game_type, historical_data)
        prediction_id = predictor.save_prediction(prediction)
        
        response = {
            'success': True,
            'prediction_id': prediction_id,
            'game_type': game_type,
            'prediction': prediction.dict(),
            'historical_data_points': len(historical_data.get('draws', [])),
            'confidence_score': prediction.confidence_score
        }
        
        return jsonify(response)
        
    except Exception as e:
        logger.error(f"Generate prediction error: {e}")
        return jsonify({'error': 'Prediction generation temporarily unavailable'}), 500

@bp.route('/prediction-history')
@require_admin
def get_prediction_history():
    """Get historical AI predictions with accuracy data"""
    try:
        import psycopg2
        import os
        
        # Get query parameters
        game_type = request.args.get('game_type', 'all')
        limit = int(request.args.get('limit', 10))
        
        logger.info(f"Getting prediction history for: {game_type}, limit: {limit}")
        
        with psycopg2.connect(os.environ.get('DATABASE_URL')) as conn:
            with conn.cursor() as cur:
                if game_type != 'all':
                    db_game_type = map_frontend_to_db_lottery_type(game_type)
                    cur.execute("""
                        SELECT id, game_type, predicted_numbers, bonus_numbers, 
                               confidence_score, prediction_method, reasoning, 
                               target_draw_date, created_at, is_verified, accuracy_score
                        FROM lottery_predictions 
                        WHERE game_type = %s 
                        ORDER BY created_at DESC 
                        LIMIT %s
                    """, (db_game_type, limit))
                else:
                    cur.execute("""
                        SELECT id, game_type, predicted_numbers, bonus_numbers, 
                               confidence_score, prediction_method, reasoning, 
                               target_draw_date, created_at, is_verified, accuracy_score
                        FROM lottery_predictions 
                        ORDER BY created_at DESC 
                        LIMIT %s
                    """, (limit,))
                
                results = cur.fetchall()
                predictions = []
                
                for row in results:
                    predictions.append({
                        'id': row[0],
                        'game_type': row[1],
                        'predicted_numbers': row[2],
                        'bonus_numbers': row[3] or [],
                        'confidence_score': float(row[4]) if row[4] else 0.0,
                        'prediction_method': row[5],
                        'reasoning': row[6],
                        'target_draw_date': row[7].isoformat() if row[7] else None,
                        'created_at': row[8].isoformat() if row[8] else None,
                        'is_verified': row[9] if row[9] is not None else False,
                        'accuracy_score': float(row[10]) if row[10] else None,
                        'status': 'Verified' if row[9] else 'Pending'
                    })
        
        response = {
            'success': True,
            'game_type': game_type,
            'total_predictions': len(predictions),
            'predictions': predictions
        }
        
        return jsonify(response)
        
    except Exception as e:
        logger.error(f"Prediction history error: {e}")
        return jsonify({'error': 'Unable to load prediction history'}), 500

@bp.route('/system-metrics')
@require_admin
def get_system_metrics():
    """Get AI prediction system performance metrics"""
    try:
        import psycopg2
        import os
        from datetime import datetime, timedelta
        
        logger.info("Getting AI prediction system metrics")
        
        with psycopg2.connect(os.environ.get('DATABASE_URL')) as conn:
            with conn.cursor() as cur:
                # Get total predictions count
                cur.execute("SELECT COUNT(*) FROM lottery_predictions")
                total_predictions = cur.fetchone()[0]
                
                # Get predictions from last 30 days
                thirty_days_ago = datetime.now() - timedelta(days=30)
                cur.execute("""
                    SELECT COUNT(*) FROM lottery_predictions 
                    WHERE created_at >= %s
                """, (thirty_days_ago,))
                recent_predictions = cur.fetchone()[0]
                
                # Get verified predictions count
                cur.execute("SELECT COUNT(*) FROM lottery_predictions WHERE is_verified = true")
                verified_predictions = cur.fetchone()[0]
                
                # Get average confidence score
                cur.execute("SELECT AVG(confidence_score) FROM lottery_predictions WHERE confidence_score IS NOT NULL")
                avg_confidence = cur.fetchone()[0] or 0.0
                
                # Get predictions by game type
                cur.execute("""
                    SELECT game_type, COUNT(*) as count 
                    FROM lottery_predictions 
                    GROUP BY game_type 
                    ORDER BY count DESC
                """)
                predictions_by_game = [{'game_type': row[0], 'count': row[1]} for row in cur.fetchall()]
                
                # Get accuracy metrics for verified predictions
                cur.execute("""
                    SELECT AVG(accuracy_score) as avg_accuracy,
                           MIN(accuracy_score) as min_accuracy,
                           MAX(accuracy_score) as max_accuracy
                    FROM lottery_predictions 
                    WHERE is_verified = true AND accuracy_score IS NOT NULL
                """)
                accuracy_data = cur.fetchone()
                
                accuracy_metrics = {
                    'average': float(accuracy_data[0]) if accuracy_data[0] else 0.0,
                    'minimum': float(accuracy_data[1]) if accuracy_data[1] else 0.0,
                    'maximum': float(accuracy_data[2]) if accuracy_data[2] else 0.0
                } if accuracy_data else {'average': 0.0, 'minimum': 0.0, 'maximum': 0.0}
                
        response = {
            'success': True,
            'system_status': 'Active',
            'total_predictions': total_predictions,
            'recent_predictions_30d': recent_predictions,
            'verified_predictions': verified_predictions,
            'verification_rate': (verified_predictions / total_predictions * 100) if total_predictions > 0 else 0.0,
            'average_confidence': round(float(avg_confidence), 2),
            'accuracy_metrics': accuracy_metrics,
            'predictions_by_game': predictions_by_game,
            'last_updated': datetime.now().isoformat()
        }
        
        return jsonify(response)
        
    except Exception as e:
        logger.error(f"System metrics error: {e}")
        return jsonify({'error': 'Unable to load system metrics'}), 500

@bp.route('/validate-prediction', methods=['POST'])
@require_admin
def validate_prediction():
    """Validate a specific prediction against actual results"""
    try:
        data = request.get_json()
        prediction_id = data.get('prediction_id')
        actual_numbers = data.get('actual_numbers', [])
        actual_bonus = data.get('actual_bonus', [])
        
        if not prediction_id:
            return jsonify({'error': 'Prediction ID required'}), 400
        
        validation_result = predictor.validate_prediction_against_draw(
            prediction_id, actual_numbers, actual_bonus
        )
        
        return jsonify({
            'success': True,
            'validation': validation_result
        })
        
    except Exception as e:
        logger.error(f"Error validating prediction: {e}")
        return jsonify({'error': 'Validation failed'}), 500

@bp.route('/accuracy-insights')
@require_admin 
def get_accuracy_insights():
    """Get prediction accuracy insights and improvement recommendations"""
    try:
        game_type = request.args.get('game_type')
        days = int(request.args.get('days', 30))
        
        insights = predictor.get_prediction_accuracy_insights(game_type, days)
        
        return jsonify({
            'success': True,
            'insights': insights
        })
        
    except Exception as e:
        logger.error(f"Error getting accuracy insights: {e}")
        return jsonify({'error': 'Failed to get insights'}), 500

@bp.route('/auto-validate', methods=['POST'])
@require_admin
def auto_validate_predictions():
    """Automatically validate all pending predictions against available results"""
    try:
        from prediction_validation_system import PredictionValidationSystem
        
        validator = PredictionValidationSystem()
        results = validator.auto_validate_pending_predictions()
        
        return jsonify({
            'success': True,
            'validation_results': results
        })
        
    except Exception as e:
        logger.error(f"Error in auto-validation: {e}")
        return jsonify({'error': 'Auto-validation failed'}), 500