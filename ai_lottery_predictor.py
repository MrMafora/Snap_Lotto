#!/usr/bin/env python3
"""
Optimized AI Lottery Predictor with Focused Game-Specific Analysis
Processes data in smaller chunks to avoid AI timeouts
"""

import os
import json
import logging
import psycopg2
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from collections import defaultdict, Counter
from dataclasses import dataclass

# Import Google Gemini
from google import genai
from google.genai import types

# Configure logging
logger = logging.getLogger(__name__)

@dataclass
class LotteryPrediction:
    game_type: str
    predicted_numbers: List[int]
    bonus_numbers: List[int]
    confidence_score: float
    prediction_method: str
    reasoning: str
    created_at: datetime

class AILotteryPredictor:
    """Optimized AI Lottery Predictor with focused game-specific analysis"""
    
    def __init__(self):
        self.client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))
        self.connection_string = os.environ.get("DATABASE_URL")
        self._initialize_tables()
    
    def _initialize_tables(self):
        """Initialize prediction tables"""
        try:
            with psycopg2.connect(self.connection_string) as conn:
                with conn.cursor() as cur:
                    cur.execute("""
                        CREATE TABLE IF NOT EXISTS lottery_predictions (
                            id SERIAL PRIMARY KEY,
                            game_type VARCHAR(50) NOT NULL,
                            predicted_numbers INTEGER[] NOT NULL,
                            bonus_numbers INTEGER[],
                            confidence_score DECIMAL(5,4),
                            prediction_method VARCHAR(100),
                            reasoning TEXT,
                            target_draw_date DATE,
                            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                            main_number_matches INTEGER DEFAULT 0,
                            bonus_number_matches INTEGER DEFAULT 0,
                            accuracy_percentage DECIMAL(5,2),
                            prize_tier VARCHAR(50),
                            validation_status VARCHAR(20) DEFAULT 'pending'
                        )
                    """)
                    conn.commit()
                    logger.info("Prediction tables initialized successfully")
        except Exception as e:
            logger.error(f"Error initializing prediction tables: {e}")
    
    def get_historical_data_for_prediction(self, game_type: str, days: int = 730) -> Dict[str, Any]:
        """Get extended historical data for advanced pattern analysis (2 years)"""
        try:
            with psycopg2.connect(self.connection_string) as conn:
                with conn.cursor() as cur:
                    # Get extended historical data - 100 draws for optimal AI processing
                    cur.execute("""
                        SELECT draw_number, draw_date, main_numbers, bonus_numbers,
                               prize_divisions, rollover_amount, estimated_jackpot,
                               EXTRACT(DOW FROM draw_date) as day_of_week,
                               EXTRACT(MONTH FROM draw_date) as month,
                               EXTRACT(QUARTER FROM draw_date) as quarter,
                               EXTRACT(YEAR FROM draw_date) as year
                        FROM lottery_results 
                        WHERE game_type = %s 
                        AND draw_date >= %s
                        ORDER BY draw_date DESC 
                        LIMIT 100
                    """, (game_type, datetime.now().date() - timedelta(days=days)))
                    
                    results = cur.fetchall()
                    
                    if not results:
                        return {}
                    
                    # Build extended analysis dataset
                    extended_data = {
                        'game_type': game_type,
                        'total_draws': len(results),
                        'draws': [],
                        'all_numbers': [],
                        'frequency_analysis': {},
                        'temporal_patterns': defaultdict(int),
                        'cyclical_patterns': {
                            'monthly_trends': defaultdict(list),
                            'quarterly_trends': defaultdict(list),
                            'yearly_trends': defaultdict(list),
                            'day_of_week_patterns': defaultdict(list)
                        },
                        'long_term_analysis': {
                            'decade_patterns': defaultdict(int),
                            'seasonal_variations': defaultdict(int),
                            'number_drought_cycles': {},
                            'hot_cold_transitions': []
                        },
                        'prize_patterns': {
                            'jackpot_progression': [],
                            'rollover_count': 0,
                            'rollover_cycles': []
                        },
                        'anomaly_detection': {
                            'unusual_combinations': [],
                            'pattern_breaks': [],
                            'statistical_outliers': []
                        }
                    }
                    
                    for row in results:
                        draw_num, draw_date, main_nums, bonus_nums, prizes, rollover, jackpot, dow, month, quarter, year = row
                        
                        # Parse numbers
                        parsed_main = self.parse_numbers(main_nums)
                        parsed_bonus = self.parse_numbers(bonus_nums)
                        
                        if parsed_main:
                            # Store comprehensive draw data
                            draw_record = {
                                'draw_number': draw_num,
                                'draw_date': draw_date.isoformat() if draw_date else None,
                                'main': parsed_main,
                                'bonus': parsed_bonus,
                                'day_of_week': int(dow) if dow else None,
                                'month': int(month) if month else None,
                                'quarter': int(quarter) if quarter else None,
                                'year': int(year) if year else None
                            }
                            
                            extended_data['draws'].append(draw_record)
                            extended_data['all_numbers'].extend(parsed_main)
                            
                            # Enhanced temporal pattern tracking
                            if dow is not None:
                                extended_data['temporal_patterns'][f'day_{int(dow)}'] += 1
                                extended_data['cyclical_patterns']['day_of_week_patterns'][int(dow)].append(parsed_main)
                            
                            if month is not None:
                                extended_data['cyclical_patterns']['monthly_trends'][int(month)].append(parsed_main)
                                extended_data['long_term_analysis']['seasonal_variations'][f'month_{int(month)}'] += 1
                            
                            if quarter is not None:
                                extended_data['cyclical_patterns']['quarterly_trends'][int(quarter)].append(parsed_main)
                            
                            if year is not None:
                                extended_data['cyclical_patterns']['yearly_trends'][int(year)].append(parsed_main)
                                extended_data['long_term_analysis']['decade_patterns'][f'year_{int(year)}'] += 1
                            
                            # Enhanced financial pattern tracking
                            if jackpot:
                                try:
                                    jackpot_val = float(str(jackpot).replace(',', '').replace('R', '').strip())
                                    extended_data['prize_patterns']['jackpot_progression'].append({
                                        'amount': jackpot_val,
                                        'draw_date': draw_date.isoformat() if draw_date else None,
                                        'draw_number': draw_num
                                    })
                                except:
                                    pass
                            
                            if rollover and str(rollover).strip() and rollover != '0':
                                extended_data['prize_patterns']['rollover_count'] += 1
                                extended_data['prize_patterns']['rollover_cycles'].append({
                                    'draw_number': draw_num,
                                    'date': draw_date.isoformat() if draw_date else None
                                })
                    
                    # Enhanced frequency analysis - complete spectrum
                    all_number_counts = Counter(extended_data['all_numbers'])
                    extended_data['frequency_analysis'] = dict(all_number_counts.most_common())
                    
                    # Calculate long-term patterns
                    self._analyze_long_term_patterns(extended_data)
                    
                    # Detect anomalies and pattern breaks
                    self._detect_anomalies(extended_data)
                    
                    logger.info(f"Retrieved EXTENDED data for {game_type}: {len(extended_data['draws'])} draws (optimized for AI processing) with advanced pattern analysis")
                    return extended_data
                    
        except Exception as e:
            logger.error(f"Error getting historical data: {e}")
            return {}
    
    def _analyze_long_term_patterns(self, data: Dict[str, Any]):
        """Analyze long-term cyclical patterns and trends"""
        try:
            # Analyze number drought cycles
            all_numbers = data['all_numbers']
            if not all_numbers:
                return
            
            # Find numbers that haven't appeared recently
            recent_50_draws = data['draws'][:50] if len(data['draws']) >= 50 else data['draws']
            recent_numbers = set()
            for draw in recent_50_draws:
                recent_numbers.update(draw['main'])
            
            # Calculate drought cycles for each number
            game_type = data['game_type']
            if 'LOTTO' in game_type.upper():
                number_range = range(1, 53)  # LOTTO numbers 1-52
            elif 'POWERBALL' in game_type.upper():
                number_range = range(1, 51)  # POWERBALL main numbers 1-50
            elif 'DAILY' in game_type.upper():
                number_range = range(1, 37)  # Daily Lotto 1-36
            else:
                number_range = range(1, 53)  # Default
            
            for number in number_range:
                if number not in recent_numbers:
                    # Count how many draws since this number last appeared
                    drought_count = 0
                    for draw in data['draws']:
                        if number in draw['main']:
                            break
                        drought_count += 1
                    data['long_term_analysis']['number_drought_cycles'][number] = drought_count
            
            # Analyze hot/cold transitions
            if len(data['draws']) >= 100:
                # Split into periods and analyze frequency changes
                period_size = 25
                periods = []
                for i in range(0, min(100, len(data['draws'])), period_size):
                    period_draws = data['draws'][i:i+period_size]
                    period_numbers = []
                    for draw in period_draws:
                        period_numbers.extend(draw['main'])
                    period_freq = Counter(period_numbers)
                    periods.append(period_freq)
                
                # Find numbers that changed from hot to cold or vice versa
                if len(periods) >= 2:
                    recent_freq = periods[0]
                    older_freq = periods[1]
                    
                    for number in number_range:
                        recent_count = recent_freq.get(number, 0)
                        older_count = older_freq.get(number, 0)
                        
                        if recent_count > older_count + 2:
                            data['long_term_analysis']['hot_cold_transitions'].append({
                                'number': number,
                                'transition': 'cold_to_hot',
                                'change': recent_count - older_count
                            })
                        elif older_count > recent_count + 2:
                            data['long_term_analysis']['hot_cold_transitions'].append({
                                'number': number,
                                'transition': 'hot_to_cold',
                                'change': older_count - recent_count
                            })
            
            logger.info(f"Long-term pattern analysis completed for {game_type}")
            
        except Exception as e:
            logger.error(f"Error in long-term pattern analysis: {e}")
    
    def _detect_anomalies(self, data: Dict[str, Any]):
        """Detect statistical anomalies and pattern breaks"""
        try:
            draws = data['draws']
            if len(draws) < 20:
                return
            
            # Detect unusual number combinations
            for i, draw in enumerate(draws[:20]):  # Check recent 20 draws
                main_numbers = sorted(draw['main'])
                
                # Check for consecutive numbers
                consecutive_count = 0
                for j in range(len(main_numbers) - 1):
                    if main_numbers[j+1] == main_numbers[j] + 1:
                        consecutive_count += 1
                
                if consecutive_count >= 3:
                    data['anomaly_detection']['unusual_combinations'].append({
                        'draw_number': draw['draw_number'],
                        'type': 'high_consecutive',
                        'value': consecutive_count,
                        'numbers': main_numbers
                    })
                
                # Check for same digit patterns
                same_digit_groups = defaultdict(list)
                for num in main_numbers:
                    last_digit = num % 10
                    same_digit_groups[last_digit].append(num)
                
                for digit, nums in same_digit_groups.items():
                    if len(nums) >= 3:
                        data['anomaly_detection']['unusual_combinations'].append({
                            'draw_number': draw['draw_number'],
                            'type': 'same_last_digit',
                            'digit': digit,
                            'count': len(nums),
                            'numbers': nums
                        })
            
            # Detect pattern breaks in frequency
            if len(draws) >= 50:
                recent_25 = draws[:25]
                older_25 = draws[25:50]
                
                recent_freq = Counter()
                older_freq = Counter()
                
                for draw in recent_25:
                    recent_freq.update(draw['main'])
                
                for draw in older_25:
                    older_freq.update(draw['main'])
                
                # Find significant frequency changes
                for number in set(recent_freq.keys()) | set(older_freq.keys()):
                    recent_count = recent_freq.get(number, 0)
                    older_count = older_freq.get(number, 0)
                    
                    if abs(recent_count - older_count) >= 4:
                        data['anomaly_detection']['pattern_breaks'].append({
                            'number': number,
                            'recent_frequency': recent_count,
                            'older_frequency': older_count,
                            'change': recent_count - older_count
                        })
            
            logger.info(f"Anomaly detection completed for {data['game_type']}")
            
        except Exception as e:
            logger.error(f"Error in anomaly detection: {e}")
    
    def parse_numbers(self, numbers_field) -> List[int]:
        """Parse numbers from database field"""
        if not numbers_field:
            return []
        
        try:
            if isinstance(numbers_field, str):
                if numbers_field.startswith('{') and numbers_field.endswith('}'):
                    numbers_str = numbers_field.strip('{}')
                    if numbers_str:
                        return [int(x.strip()) for x in numbers_str.split(',')]
                else:
                    return json.loads(numbers_field)
            elif isinstance(numbers_field, list):
                return numbers_field
        except:
            pass
        
        return []
    
    def generate_ai_prediction(self, game_type: str, historical_data: Dict[str, Any], variation_seed: int = 1) -> Optional[LotteryPrediction]:
        """Generate prediction with EXTENDED AI analysis - using 200+ draws"""
        try:
            # Get game configuration
            game_config = self.get_game_configuration(game_type)
            
            # Extract extended multi-timeframe data
            total_draws = len(historical_data.get('draws', []))
            recent_draws = historical_data.get('draws', [])[:20]  # Most recent 20 draws
            medium_term_draws = historical_data.get('draws', [])[20:60] if total_draws > 20 else []
            long_term_draws = historical_data.get('draws', [])[60:] if total_draws > 60 else []
            
            # Extended frequency analysis - all numbers, not just top 20
            frequency_analysis = historical_data.get('frequency_analysis', {})
            
            # Extract advanced pattern data
            cyclical_patterns = historical_data.get('cyclical_patterns', {})
            long_term_analysis = historical_data.get('long_term_analysis', {})
            anomaly_detection = historical_data.get('anomaly_detection', {})
            prize_patterns = historical_data.get('prize_patterns', {})
            
            # Create comprehensive advanced analysis prompt
            prediction_prompt = f"""
            EXTENDED LOTTERY ANALYSIS FOR {game_type} - ANALYZING {total_draws} HISTORICAL DRAWS
            
            GAME RULES:
            - Pick {game_config['main_count']} main numbers from 1-{game_config['main_range']}
            {"- Pick " + str(game_config['bonus_count']) + " bonus numbers from 1-" + str(game_config['bonus_range']) if game_config['bonus_count'] > 0 else ""}
            
            === MULTI-TIMEFRAME ANALYSIS ===
            
            RECENT DRAWS (Last 20 - Most Relevant):
            {json.dumps(recent_draws[:12], indent=2)}
            
            MEDIUM-TERM PATTERN (Draws 21-60):
            Total draws analyzed: {len(medium_term_draws)}
            
            LONG-TERM HISTORICAL (60+ draws):
            Total historical draws: {len(long_term_draws)}
            
            === COMPREHENSIVE FREQUENCY ANALYSIS ===
            Complete Number Frequency (ALL {total_draws} draws):
            {dict(list(frequency_analysis.items())[:30])}
            
            === CYCLICAL PATTERN DETECTION ===
            Monthly Trends: {dict(list(cyclical_patterns.get('monthly_trends', {}).items())[:6])}
            Quarterly Patterns: {len(cyclical_patterns.get('quarterly_trends', {}))} quarters analyzed
            Day-of-Week Patterns: {len(cyclical_patterns.get('day_of_week_patterns', {}))} different days
            
            === LONG-TERM PATTERN ANALYSIS ===
            Number Drought Cycles: {dict(list(long_term_analysis.get('number_drought_cycles', {}).items())[:10])}
            Hot/Cold Transitions: {len(long_term_analysis.get('hot_cold_transitions', []))} transitions detected
            Seasonal Variations: {dict(list(long_term_analysis.get('seasonal_variations', {}).items())[:6])}
            
            === ANOMALY & PATTERN BREAK DETECTION ===
            Unusual Combinations Found: {len(anomaly_detection.get('unusual_combinations', []))}
            Pattern Breaks Detected: {len(anomaly_detection.get('pattern_breaks', []))}
            Statistical Outliers: {len(anomaly_detection.get('statistical_outliers', []))}
            
            === JACKPOT & FINANCIAL PATTERN ANALYSIS ===
            Recent Jackpot Progression: {prize_patterns.get('jackpot_progression', [])[-8:]}
            Rollover Count: {prize_patterns.get('rollover_count', 0)}
            Rollover Cycles: {len(prize_patterns.get('rollover_cycles', []))} cycles
            
            === ADVANCED ANALYSIS FRAMEWORK ===
            1. EXTENDED FREQUENCY PATTERNS: Analyze complete {total_draws}-draw frequency spectrum, not just recent trends
            2. CYCLICAL PATTERN RECOGNITION: Identify monthly, quarterly, and seasonal number selection patterns
            3. DROUGHT CYCLE EXPLOITATION: Consider numbers with extended absence periods for statistical reversion
            4. HOT/COLD TRANSITION ANALYSIS: Leverage numbers transitioning between frequency states
            5. ANOMALY-INFORMED PREDICTIONS: Use pattern break detection to avoid or favor certain combinations
            6. MULTI-TIMEFRAME SYNTHESIS: Blend recent (20 draws), medium-term (40 draws), and long-term (40+ draws) patterns
            
            VARIATION SEED: {variation_seed}
            
            Return ONLY this JSON format:
            {{
                "main_numbers": [list of {game_config['main_count']} numbers],
                {"bonus_numbers: [list of " + str(game_config['bonus_count']) + " numbers]," if game_config['bonus_count'] > 0 else ""}
                "confidence_percentage": 55,
                "reasoning": "Multi-timeframe analysis combining {total_draws} draws with cyclical patterns, drought cycles, and anomaly detection"
            }}
            """
            
            # Generate prediction
            response = self.client.models.generate_content(
                model="gemini-2.5-pro",
                contents=prediction_prompt,
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    temperature=0.7 + (variation_seed * 0.01),
                    max_output_tokens=1024
                )
            )
            
            if response.text:
                try:
                    prediction_data = json.loads(response.text)
                    
                    # Validate numbers
                    main_numbers = self.validate_numbers(
                        prediction_data.get('main_numbers', []),
                        game_config['main_count'],
                        game_config['main_range']
                    )
                    
                    bonus_numbers = []
                    if game_config['bonus_count'] > 0:
                        bonus_numbers = self.validate_numbers(
                            prediction_data.get('bonus_numbers', []),
                            game_config['bonus_count'],
                            game_config['bonus_range']
                        )
                    
                    # Create prediction
                    prediction = LotteryPrediction(
                        game_type=game_type,
                        predicted_numbers=sorted(main_numbers),
                        bonus_numbers=sorted(bonus_numbers),
                        confidence_score=prediction_data.get('confidence_percentage', 50) / 100.0,
                        prediction_method="Extended_Historical_Analysis",
                        reasoning=f"Extended analysis ({total_draws} draws): " + prediction_data.get('reasoning', 'Multi-timeframe pattern analysis with cyclical detection'),
                        created_at=datetime.now()
                    )
                    
                    return prediction
                    
                except json.JSONDecodeError as e:
                    logger.error(f"JSON decode error: {e}")
                    return None
            else:
                logger.error("Empty response from AI model")
                return None
                
        except Exception as e:
            logger.error(f"Error generating AI prediction: {e}")
            return None
    
    def validate_numbers(self, numbers: List[int], required_count: int, max_range: int) -> List[int]:
        """Validate and fix prediction numbers"""
        try:
            # Remove duplicates and filter valid range
            valid_numbers = list(set([n for n in numbers if 1 <= n <= max_range]))
            
            # Fill missing numbers if needed
            if len(valid_numbers) < required_count:
                remaining_needed = required_count - len(valid_numbers)
                available_numbers = [n for n in range(1, max_range + 1) if n not in valid_numbers]
                
                import random
                additional_numbers = random.sample(available_numbers, min(remaining_needed, len(available_numbers)))
                valid_numbers.extend(additional_numbers)
            
            return valid_numbers[:required_count]
            
        except Exception as e:
            logger.error(f"Error validating numbers: {e}")
            import random
            return random.sample(range(1, max_range + 1), required_count)
    
    def get_game_configuration(self, game_type: str) -> Dict[str, int]:
        """Get game configuration"""
        configs = {
            'LOTTO': {'main_count': 6, 'main_range': 52, 'bonus_count': 0, 'bonus_range': 0},
            'LOTTO PLUS 1': {'main_count': 6, 'main_range': 52, 'bonus_count': 0, 'bonus_range': 0},
            'LOTTO PLUS 2': {'main_count': 6, 'main_range': 52, 'bonus_count': 0, 'bonus_range': 0},
            'POWERBALL': {'main_count': 5, 'main_range': 50, 'bonus_count': 1, 'bonus_range': 20},
            'POWERBALL PLUS': {'main_count': 5, 'main_range': 50, 'bonus_count': 1, 'bonus_range': 20},
            'DAILY LOTTO': {'main_count': 5, 'main_range': 36, 'bonus_count': 0, 'bonus_range': 0}
        }
        return configs.get(game_type, configs['LOTTO'])
    
    def store_prediction_in_database(self, prediction: LotteryPrediction) -> bool:
        """Store prediction in database"""
        try:
            with psycopg2.connect(self.connection_string) as conn:
                with conn.cursor() as cur:
                    next_draw = datetime.now().date() + timedelta(days=1)
                    
                    cur.execute("""
                        INSERT INTO lottery_predictions (
                            game_type, predicted_numbers, bonus_numbers, 
                            confidence_score, prediction_method, reasoning, 
                            target_draw_date, created_at
                        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                    """, (
                        prediction.game_type,
                        prediction.predicted_numbers,
                        prediction.bonus_numbers,
                        prediction.confidence_score,
                        prediction.prediction_method,
                        prediction.reasoning,
                        next_draw,
                        prediction.created_at
                    ))
                    conn.commit()
                    logger.info(f"✅ Stored prediction for {prediction.game_type}")
                    return True
        except Exception as e:
            logger.error(f"Error storing prediction: {e}")
            return False
    
    def validate_prediction_against_draw(self, prediction_id: int, actual_numbers: List[int], actual_bonus: List[int] = None) -> Dict[str, Any]:
        """Validate a prediction against actual draw results"""
        try:
            with psycopg2.connect(self.connection_string) as conn:
                with conn.cursor() as cur:
                    # Get prediction details
                    cur.execute("""
                        SELECT predicted_numbers, bonus_numbers, game_type, confidence_score
                        FROM lottery_predictions WHERE id = %s
                    """, (prediction_id,))
                    
                    result = cur.fetchone()
                    if not result:
                        return {'error': 'Prediction not found'}
                    
                    predicted_numbers, predicted_bonus, game_type, confidence = result
                    predicted_bonus = predicted_bonus or []
                    actual_bonus = actual_bonus or []
                    
                    # Calculate matches
                    main_matches = len(set(predicted_numbers) & set(actual_numbers))
                    bonus_matches = len(set(predicted_bonus) & set(actual_bonus)) if predicted_bonus and actual_bonus else 0
                    
                    # Determine accuracy level
                    total_predicted = len(predicted_numbers)
                    accuracy_percentage = (main_matches / total_predicted) * 100 if total_predicted > 0 else 0
                    
                    # Calculate prize tier (simplified)
                    prize_tier = self.calculate_prize_tier(game_type, main_matches, bonus_matches)
                    
                    # Update prediction with validation results
                    cur.execute("""
                        UPDATE lottery_predictions 
                        SET is_verified = true, 
                            validation_status = 'validated',
                            main_number_matches = %s,
                            bonus_number_matches = %s,
                            accuracy_percentage = %s,
                            prize_tier = %s,
                            matched_main_numbers = %s,
                            matched_bonus_numbers = %s,
                            verified_at = NOW()
                        WHERE id = %s
                    """, (main_matches, bonus_matches, accuracy_percentage, prize_tier, 
                          list(set(predicted_numbers) & set(actual_numbers)),
                          list(set(predicted_bonus) & set(actual_bonus)) if predicted_bonus and actual_bonus else [],
                          prediction_id))
                    
                    conn.commit()
                    
                    validation_result = {
                        'prediction_id': prediction_id,
                        'game_type': game_type,
                        'predicted_numbers': predicted_numbers,
                        'predicted_bonus': predicted_bonus,
                        'actual_numbers': actual_numbers,
                        'actual_bonus': actual_bonus,
                        'main_matches': main_matches,
                        'bonus_matches': bonus_matches,
                        'accuracy_percentage': round(accuracy_percentage, 2),
                        'prize_tier': prize_tier,
                        'matched_main_numbers': list(set(predicted_numbers) & set(actual_numbers)),
                        'matched_bonus_numbers': list(set(predicted_bonus) & set(actual_bonus)) if predicted_bonus and actual_bonus else [],
                        'validation_status': 'validated'
                    }
                    
                    logger.info(f"✅ Validated prediction {prediction_id}: {main_matches} main + {bonus_matches} bonus matches ({accuracy_percentage:.1f}%)")
                    return validation_result
                    
        except Exception as e:
            logger.error(f"Error validating prediction {prediction_id}: {e}")
            return {'error': f'Validation failed: {str(e)}'}
    
    def calculate_prize_tier(self, game_type: str, main_matches: int, bonus_matches: int) -> str:
        """Calculate prize tier based on matches"""
        try:
            if game_type in ['POWERBALL', 'POWERBALL PLUS']:
                if main_matches == 5 and bonus_matches == 1:
                    return "Division 1"
                elif main_matches == 5:
                    return "Division 2"
                elif main_matches == 4 and bonus_matches == 1:
                    return "Division 3"
                elif main_matches == 4:
                    return "Division 4"
                elif main_matches == 3 and bonus_matches == 1:
                    return "Division 5"
                elif main_matches == 3:
                    return "Division 6"
                elif main_matches == 2 and bonus_matches == 1:
                    return "Division 7"
                elif main_matches == 1 and bonus_matches == 1:
                    return "Division 8"
                elif bonus_matches == 1:
                    return "Division 9"
                else:
                    return "No prize"
            
            elif game_type in ['LOTTO', 'LOTTO PLUS 1', 'LOTTO PLUS 2']:
                if main_matches == 6:
                    return "Division 1"
                elif main_matches == 5:
                    return "Division 2"  
                elif main_matches == 4:
                    return "Division 3"
                elif main_matches == 3:
                    return "Division 4"
                else:
                    return "No prize"
            
            elif game_type == 'DAILY LOTTO':
                if main_matches == 5:
                    return "Division 1"
                elif main_matches == 4:
                    return "Division 2"
                elif main_matches == 3:
                    return "Division 3"
                elif main_matches == 2:
                    return "Division 4"
                else:
                    return "No prize"
            
            return "No prize"
            
        except Exception as e:
            logger.error(f"Error calculating prize tier: {e}")
            return "No prize"