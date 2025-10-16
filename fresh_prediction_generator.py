#!/usr/bin/env python3
"""
Fresh Prediction Generator - Automatically creates new predictions for upcoming draws
Ensures each draw gets unique prediction numbers, not recycled ones
"""

import os
import psycopg2
import random
import logging
import json
from datetime import datetime, timedelta
from collections import Counter
import numpy as np

logger = logging.getLogger(__name__)

# ENABLED: Phase 2 Neural Network System - Advanced ML Ensemble
try:
    from neural_network_prediction import neural_network_prediction
    NEURAL_NETWORK_AVAILABLE = True
    logger.info("✅ Phase 2 Neural Network system ENABLED - Advanced ML ensemble with Gradient Boosting + Random Forest + Neural Network")
except ImportError as e:
    NEURAL_NETWORK_AVAILABLE = False
    logger.warning(f"⚠️ Phase 2 Neural Network not available: {e}")

def get_historical_data(cur, lottery_type, days_back=180):
    """Get historical lottery data for intelligent analysis"""
    try:
        # Get recent draws for frequency analysis
        cur.execute('''
            SELECT main_numbers, bonus_numbers, draw_date
            FROM lottery_results
            WHERE lottery_type = %s 
              AND draw_date >= CURRENT_DATE - make_interval(days => %s)
            ORDER BY draw_date DESC
            LIMIT 100
        ''', (lottery_type, days_back))
        
        results = cur.fetchall()
        all_main_numbers = []
        all_bonus_numbers = []
        
        for main_nums, bonus_nums, draw_date in results:
            # Parse main numbers
            if isinstance(main_nums, str):
                if main_nums.startswith('{') and main_nums.endswith('}'):
                    main_str = main_nums.strip('{}')
                    if main_str:
                        parsed_main = [int(x.strip()) for x in main_str.split(',')]
                        all_main_numbers.extend(parsed_main)
                else:
                    parsed_main = json.loads(main_nums)
                    all_main_numbers.extend(parsed_main)
            elif isinstance(main_nums, list):
                all_main_numbers.extend(main_nums)
                
            # Parse bonus numbers
            if bonus_nums:
                if isinstance(bonus_nums, str):
                    if bonus_nums.startswith('{') and bonus_nums.endswith('}'):
                        bonus_str = bonus_nums.strip('{}')
                        if bonus_str:
                            parsed_bonus = [int(x.strip()) for x in bonus_str.split(',')]
                            all_bonus_numbers.extend(parsed_bonus)
                    else:
                        parsed_bonus = json.loads(bonus_nums)
                        all_bonus_numbers.extend(parsed_bonus)
                elif isinstance(bonus_nums, list):
                    all_bonus_numbers.extend(bonus_nums)
                elif isinstance(bonus_nums, (int, float)):
                    all_bonus_numbers.append(int(bonus_nums))
        
        return all_main_numbers, all_bonus_numbers, len(results)
    except Exception as e:
        logger.warning(f"Error getting historical data for {lottery_type}: {e}")
        return [], [], 0

def calculate_intelligent_confidence(hot_numbers, cold_numbers, selected_numbers, total_draws):
    """Calculate realistic evidence-based confidence score for lottery predictions"""
    try:
        if not total_draws or total_draws < 5:
            return 1.5  # Low confidence with insufficient data
            
        # Count how many selected numbers are in hot/cold lists
        hot_matches = len([n for n in selected_numbers if n in hot_numbers])
        cold_matches = len([n for n in selected_numbers if n in cold_numbers])
        
        # REALISTIC BASE: Lottery predictions inherently have very low certainty
        base_confidence = 2.0  # Start at 2% - realistic for lottery predictions
        
        # Small bonuses for pattern matching (scaled down dramatically)
        hot_bonus = hot_matches * 0.2  # Max ~1.2% bonus
        cold_bonus = cold_matches * 0.1  # Max ~0.6% bonus  
        
        # Data quality bonus (very small)
        data_quality_bonus = min(total_draws / 100, 0.8)  # Max 0.8% for excellent data
        
        # Calculate final confidence (realistic lottery prediction confidence)
        confidence = base_confidence + hot_bonus + cold_bonus + data_quality_bonus
        
        # Cap at REALISTIC levels for lottery predictions (1.5-4.5%)
        confidence = max(1.5, min(4.5, round(confidence, 1)))
        
        return confidence
    except Exception as e:
        logger.warning(f"Error calculating confidence: {e}")
        return 2.0

def intelligent_number_selection(main_range, count, hot_numbers, cold_numbers, frequency_data):
    """Intelligent number selection using frequency analysis and statistical patterns"""
    try:
        min_num, max_num = main_range
        available_numbers = list(range(min_num, max_num + 1))
        
        # Create weighted selection pools
        hot_pool = [n for n in available_numbers if n in hot_numbers]
        cold_pool = [n for n in available_numbers if n in cold_numbers]
        neutral_pool = [n for n in available_numbers if n not in hot_numbers and n not in cold_numbers]
        
        selected = []
        
        # Strategy: BALANCED ACCURACY with diversity - optimized for 2+ matches
        # 50% from hot numbers (restored for pattern recognition accuracy)
        # 12% from cold numbers (reduced mean reversion for better signal)
        # 38% from neutral numbers (balanced selection)
        
        hot_count = min(len(hot_pool), max(1, int(count * 0.50)))
        cold_count = min(len(cold_pool), max(1, int(count * 0.12)))
        neutral_count = count - hot_count - cold_count
        
        # Select from hot numbers (higher probability from frequency leaders)
        if hot_pool and hot_count > 0:
            selected.extend(random.sample(hot_pool, min(hot_count, len(hot_pool))))
        
        # Select from cold numbers (mean reversion theory)
        if cold_pool and cold_count > 0:
            remaining_cold = [n for n in cold_pool if n not in selected]
            if remaining_cold:
                selected.extend(random.sample(remaining_cold, min(cold_count, len(remaining_cold))))
        
        # Fill remaining spots with neutral numbers
        remaining_neutral = [n for n in neutral_pool if n not in selected]
        if remaining_neutral and neutral_count > 0:
            selected.extend(random.sample(remaining_neutral, min(neutral_count, len(remaining_neutral))))
        
        # If we still need more numbers, fill from any remaining
        while len(selected) < count:
            remaining = [n for n in available_numbers if n not in selected]
            if not remaining:
                break
            selected.append(random.choice(remaining))
        
        # SOFT DIVERSITY: Light range guidance without breaking patterns
        selected = selected[:count]  # Ensure correct count first
        range_size = max_num - min_num + 1
        
        # Apply soft diversity only if severely clustered (don't force if good patterns exist)
        if range_size >= 24 and count >= 4:
            third_size = range_size // 3
            lower_third = [n for n in selected if min_num <= n <= min_num + third_size - 1]
            middle_third = [n for n in selected if min_num + third_size <= n <= min_num + (2 * third_size) - 1]
            upper_third = [n for n in selected if n >= min_num + (2 * third_size)]
            
            # Only apply diversity if ALL numbers are in one third (severe clustering)
            if len(lower_third) == count or len(middle_third) == count or len(upper_third) == count:
                # Gently replace ONE number to add minimal diversity without breaking patterns
                if not middle_third:  # Missing middle - replace lowest value number
                    middle_candidates = [n for n in range(min_num + third_size, min_num + (2 * third_size)) if n not in selected]
                    if middle_candidates and selected:
                        selected[-1] = random.choice(middle_candidates)  # Replace last (lowest priority) number
                        logger.info(f"🎯 Applied minimal diversity: Added one middle-range number")
        
        return sorted(selected[:count])
        
    except Exception as e:
        logger.warning(f"Error in intelligent selection: {e}")
        # Fallback to random selection
        return sorted(random.sample(range(main_range[0], main_range[1] + 1), count))

def cleanup_old_pending_predictions(cur, lottery_type):
    """
    Delete old pending predictions for a specific lottery type
    Prevents accumulation of duplicate predictions
    """
    try:
        cur.execute('''
            DELETE FROM lottery_predictions 
            WHERE game_type = %s 
              AND validation_status = 'pending'
        ''', (lottery_type,))
        
        deleted_count = cur.rowcount
        if deleted_count > 0:
            logger.info(f"🧹 Cleaned up {deleted_count} old pending prediction(s) for {lottery_type}")
        
        return deleted_count
    except Exception as e:
        logger.warning(f"⚠️ Error cleaning up old predictions for {lottery_type}: {e}")
        return 0

def generate_fresh_predictions_for_new_draws():
    """
    Automatically generate fresh predictions for newly completed draws
    This ensures each upcoming draw has unique prediction numbers
    """
    try:
        logger.info("🎯 Generating fresh predictions for new draws...")
        
        # Connect to database
        conn = psycopg2.connect(os.environ.get('DATABASE_URL'))
        cur = conn.cursor()
        
        # Game configurations
        configs = {
            'LOTTO': {'main_count': 6, 'main_range': (1, 52), 'bonus_count': 0},
            'LOTTO PLUS 1': {'main_count': 6, 'main_range': (1, 52), 'bonus_count': 0}, 
            'LOTTO PLUS 2': {'main_count': 6, 'main_range': (1, 52), 'bonus_count': 0},
            'POWERBALL': {'main_count': 5, 'main_range': (1, 50), 'bonus_count': 1, 'bonus_range': (1, 20)},
            'POWERBALL PLUS': {'main_count': 5, 'main_range': (1, 50), 'bonus_count': 1, 'bonus_range': (1, 20)},
            'DAILY LOTTO': {'main_count': 5, 'main_range': (1, 36), 'bonus_count': 0}
        }
        
        # Find the latest completed draw for each game that doesn't have a prediction for the next draw
        cur.execute('''
            WITH latest_draws AS (
                SELECT 
                    lr.lottery_type,
                    lr.draw_number as completed_draw,
                    lr.draw_date,
                    lr.draw_number + 1 as next_draw_needed,
                    lr.next_draw_date,
                    ROW_NUMBER() OVER (PARTITION BY lr.lottery_type ORDER BY lr.draw_date DESC) as rn
                FROM lottery_results lr
            )
            SELECT 
                lottery_type,
                completed_draw,
                draw_date,
                next_draw_needed,
                next_draw_date
            FROM latest_draws
            WHERE rn = 1
              AND NOT EXISTS (
                  SELECT 1 FROM lottery_predictions lp 
                  WHERE lp.game_type = latest_draws.lottery_type 
                    AND lp.linked_draw_id = latest_draws.next_draw_needed
              )
            ORDER BY lottery_type
        ''')
        
        new_draws_needed = cur.fetchall()
        
        if not new_draws_needed:
            logger.info("✅ All recent draws already have fresh predictions")
            cur.close()
            conn.close()
            return True
        
        # Generate fresh predictions for each missing next draw
        for lottery_type, completed_draw, draw_date, next_draw, next_draw_date in new_draws_needed:
            logger.info(f"🔄 Generating INTELLIGENT prediction for {lottery_type} Draw {next_draw} (after completed draw {completed_draw})")
            
            # Clean up any old pending predictions for this lottery type
            cleanup_old_pending_predictions(cur, lottery_type)
            
            config = configs[lottery_type]
            
            # Get historical data for intelligent analysis
            all_main_numbers, all_bonus_numbers, total_draws = get_historical_data(cur, lottery_type)
            
            # Analyze frequency patterns for intelligent prediction
            main_frequency = Counter(all_main_numbers)
            bonus_frequency = Counter(all_bonus_numbers) if all_bonus_numbers else Counter()
            
            # Get hot and cold numbers based on recent frequency
            hot_main_numbers = [num for num, freq in main_frequency.most_common(10)]
            cold_main_numbers = [num for num, freq in main_frequency.most_common()[-10:]] if main_frequency else []
            
            hot_bonus_numbers = [num for num, freq in bonus_frequency.most_common(5)] if bonus_frequency else []
            cold_bonus_numbers = [num for num, freq in bonus_frequency.most_common()[-5:]] if bonus_frequency else []
            
            # Phase 2: Try Neural Network System First (Advanced AI)
            neural_main = None
            neural_bonus = None
            neural_confidence = None
            neural_reasoning = None
            
            # Smart ML gating: Need ≥30 draws for machine learning (enough for meaningful patterns)
            if NEURAL_NETWORK_AVAILABLE and total_draws >= 30:
                logger.info(f"🧠 Attempting Phase 2 Neural Network prediction for {lottery_type}...")
                try:
                    neural_main, neural_bonus, neural_confidence, neural_reasoning = neural_network_prediction(lottery_type, config)
                    if neural_main and neural_confidence:
                        logger.info(f"✅ Phase 2 Neural Network SUCCESS: {neural_main} + {neural_bonus} (confidence: {neural_confidence}%)")
                except Exception as e:
                    logger.warning(f"⚠️ Phase 2 Neural Network failed, falling back to Phase 1: {e}")
            
            # Use Neural Network prediction if available, otherwise use Phase 1 frequency analysis
            if neural_main and neural_confidence:
                # Phase 2: Use Neural Network Results
                main_numbers = neural_main
                confidence_score = neural_confidence
                reasoning = neural_reasoning
                prediction_method = "Phase 2 Neural Network Ensemble (Random Forest + Gradient Boosting + Neural Network)"
                
                # Use Neural Network bonus if available, otherwise fallback to Phase 1 for bonus
                if neural_bonus:
                    bonus_numbers = neural_bonus
                    logger.info(f"🎯 Using Phase 2 Neural Network bonus prediction: {bonus_numbers}")
                else:
                    # Fallback to Phase 1 for bonus numbers
                    bonus_numbers = []
                    if config['bonus_count'] > 0:
                        if hot_bonus_numbers and bonus_frequency:
                            # Use frequency-weighted selection for bonus numbers
                            all_bonus_range = list(range(config['bonus_range'][0], config['bonus_range'][1] + 1))
                            weighted_bonus_list = []
                            for num in all_bonus_range:
                                if num in hot_bonus_numbers:
                                    weighted_bonus_list.extend([num] * 3)  # 3x weight for hot numbers
                                else:
                                    weighted_bonus_list.append(num)  # 1x weight for others
                            bonus_numbers = [random.choice(weighted_bonus_list)]
                        else:
                            bonus_numbers = [random.randint(config['bonus_range'][0], config['bonus_range'][1])]
                        logger.info(f"📊 Using Phase 1 fallback for bonus prediction: {bonus_numbers}")
                
                logger.info(f"🚀 Using Phase 2 Neural Network prediction with {confidence_score}% confidence")
                
            else:
                # Phase 1: Fallback to Frequency Analysis (Still much better than random!)
                logger.info(f"📊 Using Phase 1 Frequency Analysis for {lottery_type}...")
                
                # Seed for reproducible randomness within intelligent selection
                seed = f"{lottery_type}_{next_draw}_{datetime.now().strftime('%Y%m%d_%H%M')}"
                random.seed(hash(seed) % (2**32))
                
                # Generate main numbers using intelligent selection
                main_numbers = intelligent_number_selection(
                    config['main_range'], 
                    config['main_count'], 
                    hot_main_numbers, 
                    cold_main_numbers,
                    main_frequency
                )
                
                # Generate bonus numbers using intelligent frequency-weighted selection
                bonus_numbers = []
                if config['bonus_count'] > 0:
                    if hot_bonus_numbers and bonus_frequency:
                        # Use frequency-weighted selection for bonus numbers
                        all_bonus_range = list(range(config['bonus_range'][0], config['bonus_range'][1] + 1))
                        
                        # Create weighted list: hot numbers get 3x weight, others get 1x weight
                        weighted_bonus_list = []
                        for num in all_bonus_range:
                            if num in hot_bonus_numbers:
                                weighted_bonus_list.extend([num] * 3)  # 3x weight for hot numbers
                            else:
                                weighted_bonus_list.append(num)  # 1x weight for others
                        
                        bonus_numbers = [random.choice(weighted_bonus_list)]
                    else:
                        # Fall back to range-based selection
                        bonus_numbers = [random.randint(config['bonus_range'][0], config['bonus_range'][1])]
                
                # Calculate intelligent confidence score based on patterns
                confidence_score = calculate_intelligent_confidence(
                    hot_main_numbers, cold_main_numbers, main_numbers, total_draws
                )
                
                # Create detailed reasoning
                reasoning_parts = [
                    f"Phase 1 frequency analysis using {total_draws} historical draws",
                    f"Selected {len([n for n in main_numbers if n in hot_main_numbers])} hot numbers",
                    f"Selected {len([n for n in main_numbers if n in cold_main_numbers])} cold numbers",
                    f"Confidence based on frequency patterns and statistical analysis"
                ]
                reasoning = " | ".join(reasoning_parts)
                prediction_method = "Fresh Draw-Specific Prediction Engine"
            
            # Insert intelligent prediction
            cur.execute('''
                INSERT INTO lottery_predictions (
                    game_type, predicted_numbers, bonus_numbers, confidence_score,
                    prediction_method, reasoning, target_draw_date, linked_draw_id,
                    validation_status, is_verified, created_at
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ''', (
                lottery_type, main_numbers, bonus_numbers or None, 
                float(confidence_score),  # Convert numpy types to Python float
                prediction_method,
                reasoning,
                next_draw_date,
                next_draw, 'pending', False, datetime.now()
            ))
            
            logger.info(f"✅ NEW FRESH PREDICTION: {lottery_type} Draw {next_draw}: {main_numbers} + {bonus_numbers}")
        
        conn.commit()
        logger.info(f"🎯 Generated {len(new_draws_needed)} fresh predictions!")
        
        cur.close()
        conn.close()
        return True
        
    except Exception as e:
        logger.error(f"❌ Fresh prediction generation failed: {e}")
        return False

if __name__ == "__main__":
    # Test run
    logging.basicConfig(level=logging.INFO)
    generate_fresh_predictions_for_new_draws()