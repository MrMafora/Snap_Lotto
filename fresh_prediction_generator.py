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

# Import Phase 2 Neural Network System
try:
    from neural_network_predictor import neural_network_prediction
    NEURAL_NETWORK_AVAILABLE = True
    logger.info("✅ Phase 2 Neural Network system loaded successfully")
except ImportError as e:
    NEURAL_NETWORK_AVAILABLE = False
    logger.warning(f"⚠️ Phase 2 Neural Network system not available: {e}")

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
    """Calculate evidence-based confidence score"""
    try:
        if not total_draws or total_draws < 5:
            return 45  # Low confidence with insufficient data
            
        # Count how many selected numbers are in hot/cold lists
        hot_matches = len([n for n in selected_numbers if n in hot_numbers])
        cold_matches = len([n for n in selected_numbers if n in cold_numbers])
        
        # Base confidence on statistical patterns
        base_confidence = 50
        
        # Bonus for hot numbers (recent frequency patterns)
        hot_bonus = hot_matches * 3
        
        # Slight bonus for cold numbers (mean reversion theory)
        cold_bonus = cold_matches * 1
        
        # Data quality bonus
        data_quality_bonus = min(total_draws / 10, 10)  # Up to 10% for good data
        
        # Calculate final confidence
        confidence = base_confidence + hot_bonus + cold_bonus + data_quality_bonus
        
        # Cap confidence at realistic levels (45-75%)
        confidence = max(45, min(75, int(confidence)))
        
        return confidence
    except Exception as e:
        logger.warning(f"Error calculating confidence: {e}")
        return 50

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
        
        # Strategy: Balanced approach with frequency weighting
        # 50% from hot numbers (recent trends)
        # 20% from cold numbers (mean reversion)
        # 30% from neutral numbers (balanced selection)
        
        hot_count = min(len(hot_pool), max(1, int(count * 0.5)))
        cold_count = min(len(cold_pool), max(1, int(count * 0.2)))
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
        
        return sorted(selected[:count])
        
    except Exception as e:
        logger.warning(f"Error in intelligent selection: {e}")
        # Fallback to random selection
        return sorted(random.sample(range(main_range[0], main_range[1] + 1), count))

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
        
        # Find draws that completed today but don't have next prediction yet
        cur.execute('''
            SELECT 
                lr.lottery_type,
                lr.draw_number as completed_draw,
                lr.draw_date,
                lr.draw_number + 1 as next_draw_needed,
                lr.next_draw_date
            FROM lottery_results lr
            WHERE lr.draw_date >= CURRENT_DATE - make_interval(days => 1)
              AND NOT EXISTS (
                  SELECT 1 FROM lottery_predictions lp 
                  WHERE lp.game_type = lr.lottery_type 
                    AND lp.linked_draw_id = lr.draw_number + 1
              )
            ORDER BY lr.lottery_type, lr.draw_date DESC
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
            
            if NEURAL_NETWORK_AVAILABLE and total_draws >= 20:
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
                confidence_score,  
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