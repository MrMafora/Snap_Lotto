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
import statistics
import random
from concurrent.futures import ThreadPoolExecutor, as_completed

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
    ensemble_composition: Optional[Dict[str, Any]] = None
    model_weights: Optional[Dict[str, float]] = None

@dataclass 
class ModelPrediction:
    model_name: str
    predicted_numbers: List[int]
    bonus_numbers: List[int]
    confidence_score: float
    reasoning: str

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
                            validation_status VARCHAR(20) DEFAULT 'pending',
                            ensemble_composition JSONB,
                            model_weights JSONB
                        );
                        
                        CREATE TABLE IF NOT EXISTS model_performance_tracking (
                            id SERIAL PRIMARY KEY,
                            model_name VARCHAR(100) NOT NULL,
                            game_type VARCHAR(50) NOT NULL,
                            prediction_date DATE NOT NULL,
                            predicted_numbers INTEGER[] NOT NULL,
                            bonus_numbers INTEGER[],
                            confidence_score DECIMAL(5,4),
                            accuracy_percentage DECIMAL(5,2),
                            main_number_matches INTEGER DEFAULT 0,
                            bonus_number_matches INTEGER DEFAULT 0,
                            prize_tier VARCHAR(50),
                            weight_used DECIMAL(5,4),
                            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                            UNIQUE(model_name, game_type, prediction_date)
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
                        WHERE lottery_type = %s 
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
    
    # ========== MULTI-MODEL ENSEMBLE SYSTEM ==========
    
    def generate_ensemble_prediction(self, game_type: str, historical_data: Dict[str, Any]) -> Optional[LotteryPrediction]:
        """Generate prediction using Multi-Model Ensemble - runs 5 AI models and combines results"""
        try:
            logger.info(f"🎯 Starting Multi-Model Ensemble prediction for {game_type}")
            
            # Get current model weights based on historical performance
            model_weights = self._get_model_weights(game_type)
            
            # Run all 5 AI models in parallel
            model_predictions = self._run_all_models_parallel(game_type, historical_data)
            
            if not model_predictions:
                logger.error("No model predictions generated")
                return None
            
            # Combine predictions using weighted voting
            ensemble_result = self._combine_predictions_weighted_voting(model_predictions, model_weights, game_type)
            
            if ensemble_result:
                # Store individual model performance for future weight adjustments
                self._store_model_performances(model_predictions, game_type)
                logger.info(f"✅ Ensemble prediction generated successfully for {game_type}")
                
            return ensemble_result
            
        except Exception as e:
            logger.error(f"Error generating ensemble prediction: {e}")
            return None
    
    def _get_model_weights(self, game_type: str) -> Dict[str, float]:
        """Get model weights based on historical performance"""
        try:
            with psycopg2.connect(self.connection_string) as conn:
                with conn.cursor() as cur:
                    # Get recent performance for each model
                    cur.execute("""
                        SELECT model_name, 
                               AVG(accuracy_percentage) as avg_accuracy,
                               COUNT(*) as prediction_count
                        FROM model_performance_tracking 
                        WHERE game_type = %s 
                        AND prediction_date >= CURRENT_DATE - INTERVAL '30 days'
                        GROUP BY model_name
                    """, (game_type,))
                    
                    performance_data = cur.fetchall()
                    
                    if not performance_data:
                        # Default equal weights for new games
                        return {
                            'pattern_analysis': 0.20,
                            'frequency_analysis': 0.20,
                            'statistical_regression': 0.20,
                            'anomaly_detection': 0.20,
                            'hybrid_mathematical': 0.20
                        }
                    
                    # Calculate dynamic weights based on performance
                    total_accuracy = sum(row[1] for row in performance_data if row[1])
                    
                    weights = {}
                    for model_name, avg_accuracy, count in performance_data:
                        if avg_accuracy and total_accuracy > 0:
                            # Higher accuracy gets higher weight
                            weight = (avg_accuracy / total_accuracy) * 0.8  # Base weight on accuracy
                            weight += 0.04  # Minimum weight of 4% for each model
                            weights[model_name] = weight
                        else:
                            weights[model_name] = 0.20
                    
                    # Ensure all 5 models have weights
                    all_models = ['pattern_analysis', 'frequency_analysis', 'statistical_regression', 'anomaly_detection', 'hybrid_mathematical']
                    for model in all_models:
                        if model not in weights:
                            weights[model] = 0.20
                    
                    # Normalize weights to sum to 1.0
                    total_weight = sum(weights.values())
                    if total_weight > 0:
                        weights = {k: v/total_weight for k, v in weights.items()}
                    
                    logger.info(f"Model weights for {game_type}: {weights}")
                    return weights
                    
        except Exception as e:
            logger.error(f"Error getting model weights: {e}")
            # Return default equal weights
            return {
                'pattern_analysis': 0.20,
                'frequency_analysis': 0.20,
                'statistical_regression': 0.20,
                'anomaly_detection': 0.20,
                'hybrid_mathematical': 0.20
            }
    
    def _run_all_models_parallel(self, game_type: str, historical_data: Dict[str, Any]) -> List[ModelPrediction]:
        """Run all 5 AI models in parallel for faster processing"""
        predictions = []
        
        # Define all model functions
        model_functions = [
            ('pattern_analysis', self._generate_pattern_analysis_prediction),
            ('frequency_analysis', self._generate_frequency_analysis_prediction),
            ('statistical_regression', self._generate_statistical_regression_prediction),
            ('anomaly_detection', self._generate_anomaly_detection_prediction),
            ('hybrid_mathematical', self._generate_hybrid_mathematical_prediction)
        ]
        
        # Run models in parallel using ThreadPoolExecutor
        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = {
                executor.submit(func, game_type, historical_data): model_name 
                for model_name, func in model_functions
            }
            
            for future in as_completed(futures):
                model_name = futures[future]
                try:
                    prediction = future.result(timeout=60)  # 60 second timeout per model
                    if prediction:
                        predictions.append(prediction)
                        logger.info(f"✅ {model_name} model completed")
                    else:
                        logger.warning(f"⚠️ {model_name} model returned no prediction")
                except Exception as e:
                    logger.error(f"❌ {model_name} model failed: {e}")
        
        logger.info(f"Completed {len(predictions)}/5 model predictions")
        return predictions
    
    def _combine_predictions_weighted_voting(self, model_predictions: List[ModelPrediction], 
                                            model_weights: Dict[str, float], game_type: str) -> Optional[LotteryPrediction]:
        """Combine multiple model predictions using weighted voting"""
        try:
            if not model_predictions:
                return None
                
            game_config = self.get_game_configuration(game_type)
            
            # Collect all number votes with weights
            number_votes = defaultdict(float)
            bonus_votes = defaultdict(float)
            total_confidence = 0
            ensemble_reasoning = []
            
            for prediction in model_predictions:
                model_weight = model_weights.get(prediction.model_name, 0.20)
                
                # Weight main numbers
                for number in prediction.predicted_numbers:
                    number_votes[number] += model_weight * prediction.confidence_score
                
                # Weight bonus numbers
                if prediction.bonus_numbers:
                    for bonus in prediction.bonus_numbers:
                        bonus_votes[bonus] += model_weight * prediction.confidence_score
                
                total_confidence += model_weight * prediction.confidence_score
                ensemble_reasoning.append(f"{prediction.model_name}({model_weight:.2f}): {prediction.reasoning[:50]}...")
            
            # Select top-voted numbers
            sorted_main_numbers = sorted(number_votes.items(), key=lambda x: x[1], reverse=True)
            final_main_numbers = [num for num, vote in sorted_main_numbers[:game_config['main_count']]]
            
            final_bonus_numbers = []
            if game_config['bonus_count'] > 0 and bonus_votes:
                sorted_bonus_numbers = sorted(bonus_votes.items(), key=lambda x: x[1], reverse=True)
                final_bonus_numbers = [num for num, vote in sorted_bonus_numbers[:game_config['bonus_count']]]
            
            # Create ensemble composition details
            ensemble_composition = {
                'models_used': [p.model_name for p in model_predictions],
                'model_weights': model_weights,
                'number_votes': dict(sorted_main_numbers[:10]),  # Top 10 voted numbers
                'total_models': len(model_predictions)
            }
            
            # Create final prediction
            ensemble_prediction = LotteryPrediction(
                game_type=game_type,
                predicted_numbers=sorted(final_main_numbers),
                bonus_numbers=sorted(final_bonus_numbers),
                confidence_score=min(total_confidence / len(model_predictions), 1.0),
                prediction_method="Multi_Model_Ensemble",
                reasoning=f"Ensemble of {len(model_predictions)} models: " + "; ".join(ensemble_reasoning[:3]),
                created_at=datetime.now(),
                ensemble_composition=ensemble_composition,
                model_weights=model_weights
            )
            
            return ensemble_prediction
            
        except Exception as e:
            logger.error(f"Error combining predictions: {e}")
            return None
    
    def _store_model_performances(self, model_predictions: List[ModelPrediction], game_type: str):
        """Store individual model predictions for future performance tracking"""
        try:
            with psycopg2.connect(self.connection_string) as conn:
                with conn.cursor() as cur:
                    prediction_date = datetime.now().date()
                    
                    for prediction in model_predictions:
                        cur.execute("""
                            INSERT INTO model_performance_tracking 
                            (model_name, game_type, prediction_date, predicted_numbers, 
                             bonus_numbers, confidence_score, created_at)
                            VALUES (%s, %s, %s, %s, %s, %s, %s)
                            ON CONFLICT (model_name, game_type, prediction_date) 
                            DO UPDATE SET 
                                predicted_numbers = EXCLUDED.predicted_numbers,
                                bonus_numbers = EXCLUDED.bonus_numbers,
                                confidence_score = EXCLUDED.confidence_score,
                                created_at = EXCLUDED.created_at
                        """, (
                            prediction.model_name,
                            game_type,
                            prediction_date,
                            prediction.predicted_numbers,
                            prediction.bonus_numbers,
                            prediction.confidence_score,
                            datetime.now()
                        ))
                    
                    conn.commit()
                    logger.info(f"Stored {len(model_predictions)} model performances for {game_type}")
                    
        except Exception as e:
            logger.error(f"Error storing model performances: {e}")
    
    # ========== INDIVIDUAL AI MODELS ==========
    
    def _generate_pattern_analysis_prediction(self, game_type: str, historical_data: Dict[str, Any]) -> Optional[ModelPrediction]:
        """Model 1: Pattern Analysis - Extended historical analysis approach"""
        try:
            game_config = self.get_game_configuration(game_type)
            total_draws = len(historical_data.get('draws', []))
            recent_draws = historical_data.get('draws', [])[:20]
            
            prompt = f"""
            PATTERN ANALYSIS MODEL for {game_type} - {total_draws} draws analyzed
            
            GAME RULES: Pick {game_config['main_count']} main numbers from 1-{game_config['main_range']}
            {"Pick " + str(game_config['bonus_count']) + " bonus from 1-" + str(game_config['bonus_range']) if game_config['bonus_count'] > 0 else ""}
            
            FOCUS: Pattern recognition, sequence analysis, cyclical trends
            
            RECENT PATTERNS: {json.dumps(recent_draws[:8], indent=1)}
            CYCLICAL: {historical_data.get('cyclical_patterns', {}).get('monthly_trends', {})}
            
            Return JSON: {{"main_numbers": [1,2,3,4,5,6], "confidence_percentage": 60, "reasoning": "pattern analysis"}}
            """
            
            response = self.client.models.generate_content(
                model="gemini-2.5-pro",
                contents=prompt,
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    temperature=0.6,
                    max_output_tokens=512
                )
            )
            
            if response.text:
                data = json.loads(response.text)
                main_numbers = self.validate_numbers(data.get('main_numbers', []), game_config['main_count'], game_config['main_range'])
                bonus_numbers = self.validate_numbers(data.get('bonus_numbers', []), game_config['bonus_count'], game_config['bonus_range']) if game_config['bonus_count'] > 0 else []
                
                return ModelPrediction(
                    model_name='pattern_analysis',
                    predicted_numbers=sorted(main_numbers),
                    bonus_numbers=sorted(bonus_numbers),
                    confidence_score=data.get('confidence_percentage', 60) / 100.0,
                    reasoning=data.get('reasoning', 'Pattern analysis based prediction')
                )
                
        except Exception as e:
            logger.error(f"Pattern analysis model error: {e}")
            return None
    
    def _generate_frequency_analysis_prediction(self, game_type: str, historical_data: Dict[str, Any]) -> Optional[ModelPrediction]:
        """Model 2: Pure Frequency Analysis - Focus on hot/cold numbers"""
        try:
            game_config = self.get_game_configuration(game_type)
            frequency_analysis = historical_data.get('frequency_analysis', {})
            
            # Get hot and cold numbers
            sorted_freq = sorted(frequency_analysis.items(), key=lambda x: x[1], reverse=True)
            hot_numbers = [num for num, freq in sorted_freq[:15]]
            cold_numbers = [num for num, freq in sorted_freq[-10:]]
            
            prompt = f"""
            FREQUENCY ANALYSIS MODEL for {game_type}
            
            GAME RULES: Pick {game_config['main_count']} main numbers from 1-{game_config['main_range']}
            {"Pick " + str(game_config['bonus_count']) + " bonus from 1-" + str(game_config['bonus_range']) if game_config['bonus_count'] > 0 else ""}
            
            FOCUS: Statistical frequency, hot/cold number theory, reversion analysis
            
            HOT NUMBERS (most frequent): {hot_numbers}
            COLD NUMBERS (least frequent): {cold_numbers}
            FREQUENCY DATA: {dict(sorted_freq[:20])}
            
            STRATEGY: Balance hot numbers (continuing trends) with cold numbers (due for reversion)
            
            Return JSON: {{"main_numbers": [1,2,3,4,5,6], "confidence_percentage": 55, "reasoning": "frequency analysis"}}
            """
            
            response = self.client.models.generate_content(
                model="gemini-2.5-pro",
                contents=prompt,
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    temperature=0.7,
                    max_output_tokens=512
                )
            )
            
            if response.text:
                data = json.loads(response.text)
                main_numbers = self.validate_numbers(data.get('main_numbers', []), game_config['main_count'], game_config['main_range'])
                bonus_numbers = self.validate_numbers(data.get('bonus_numbers', []), game_config['bonus_count'], game_config['bonus_range']) if game_config['bonus_count'] > 0 else []
                
                return ModelPrediction(
                    model_name='frequency_analysis',
                    predicted_numbers=sorted(main_numbers),
                    bonus_numbers=sorted(bonus_numbers),
                    confidence_score=data.get('confidence_percentage', 55) / 100.0,
                    reasoning=data.get('reasoning', 'Frequency-based statistical analysis')
                )
                
        except Exception as e:
            logger.error(f"Frequency analysis model error: {e}")
            return None
    
    def _generate_statistical_regression_prediction(self, game_type: str, historical_data: Dict[str, Any]) -> Optional[ModelPrediction]:
        """Model 3: Statistical/Mathematical Regression - Pure probability approach"""
        try:
            game_config = self.get_game_configuration(game_type)
            all_numbers = historical_data.get('all_numbers', [])
            total_draws = len(historical_data.get('draws', []))
            
            # Calculate statistical metrics
            if all_numbers:
                avg_number = statistics.mean(all_numbers)
                median_number = statistics.median(all_numbers)
                
                # Calculate expected frequencies
                expected_freq = len(all_numbers) / game_config['main_range']
                
                prompt = f"""
                STATISTICAL REGRESSION MODEL for {game_type}
                
                GAME RULES: Pick {game_config['main_count']} main numbers from 1-{game_config['main_range']}
                {"Pick " + str(game_config['bonus_count']) + " bonus from 1-" + str(game_config['bonus_range']) if game_config['bonus_count'] > 0 else ""}
                
                FOCUS: Mathematical probability, statistical regression, uniform distribution theory
                
                STATISTICAL METRICS:
                - Total draws analyzed: {total_draws}
                - Average number: {avg_number:.2f}
                - Median number: {median_number}
                - Expected frequency per number: {expected_freq:.2f}
                - Total number range: 1-{game_config['main_range']}
                
                APPROACH: Use statistical principles, normal distribution, and mathematical probability
                
                Return JSON: {{"main_numbers": [1,2,3,4,5,6], "confidence_percentage": 50, "reasoning": "statistical regression"}}
                """
                
                response = self.client.models.generate_content(
                    model="gemini-2.5-pro",
                    contents=prompt,
                    config=types.GenerateContentConfig(
                        response_mime_type="application/json",
                        temperature=0.4,  # Lower temperature for mathematical approach
                        max_output_tokens=512
                    )
                )
                
                if response.text:
                    data = json.loads(response.text)
                    main_numbers = self.validate_numbers(data.get('main_numbers', []), game_config['main_count'], game_config['main_range'])
                    bonus_numbers = self.validate_numbers(data.get('bonus_numbers', []), game_config['bonus_count'], game_config['bonus_range']) if game_config['bonus_count'] > 0 else []
                    
                    return ModelPrediction(
                        model_name='statistical_regression',
                        predicted_numbers=sorted(main_numbers),
                        bonus_numbers=sorted(bonus_numbers),
                        confidence_score=data.get('confidence_percentage', 50) / 100.0,
                        reasoning=data.get('reasoning', 'Mathematical regression analysis')
                    )
            
        except Exception as e:
            logger.error(f"Statistical regression model error: {e}")
            return None
    
    def _generate_anomaly_detection_prediction(self, game_type: str, historical_data: Dict[str, Any]) -> Optional[ModelPrediction]:
        """Model 4: Anomaly Detection - Focus on avoiding unusual patterns"""
        try:
            game_config = self.get_game_configuration(game_type)
            anomaly_data = historical_data.get('anomaly_detection', {})
            recent_draws = historical_data.get('draws', [])[:10]
            
            # Extract anomaly information
            unusual_combinations = anomaly_data.get('unusual_combinations', [])
            pattern_breaks = anomaly_data.get('pattern_breaks', [])
            
            prompt = f"""
            ANOMALY DETECTION MODEL for {game_type}
            
            GAME RULES: Pick {game_config['main_count']} main numbers from 1-{game_config['main_range']}
            {"Pick " + str(game_config['bonus_count']) + " bonus from 1-" + str(game_config['bonus_range']) if game_config['bonus_count'] > 0 else ""}
            
            FOCUS: Avoid anomalous patterns, predict statistically normal combinations
            
            RECENT DRAWS: {json.dumps(recent_draws[:5], indent=1)}
            UNUSUAL COMBINATIONS DETECTED: {len(unusual_combinations)} anomalies
            PATTERN BREAKS: {len(pattern_breaks)} breaks detected
            
            STRATEGY: Generate numbers that avoid consecutive patterns, same-digit clusters, and statistical outliers
            Favor balanced, distributed selections
            
            Return JSON: {{"main_numbers": [1,2,3,4,5,6], "confidence_percentage": 58, "reasoning": "anomaly avoidance"}}
            """
            
            response = self.client.models.generate_content(
                model="gemini-2.5-pro",
                contents=prompt,
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    temperature=0.5,
                    max_output_tokens=512
                )
            )
            
            if response.text:
                data = json.loads(response.text)
                main_numbers = self.validate_numbers(data.get('main_numbers', []), game_config['main_count'], game_config['main_range'])
                bonus_numbers = self.validate_numbers(data.get('bonus_numbers', []), game_config['bonus_count'], game_config['bonus_range']) if game_config['bonus_count'] > 0 else []
                
                return ModelPrediction(
                    model_name='anomaly_detection',
                    predicted_numbers=sorted(main_numbers),
                    bonus_numbers=sorted(bonus_numbers),
                    confidence_score=data.get('confidence_percentage', 58) / 100.0,
                    reasoning=data.get('reasoning', 'Anomaly detection and avoidance')
                )
                
        except Exception as e:
            logger.error(f"Anomaly detection model error: {e}")
            return None
    
    def _generate_hybrid_mathematical_prediction(self, game_type: str, historical_data: Dict[str, Any]) -> Optional[ModelPrediction]:
        """Model 5: Hybrid Mathematical - Combines multiple mathematical approaches"""
        try:
            game_config = self.get_game_configuration(game_type)
            total_draws = len(historical_data.get('draws', []))
            drought_cycles = historical_data.get('long_term_analysis', {}).get('number_drought_cycles', {})
            hot_cold_transitions = historical_data.get('long_term_analysis', {}).get('hot_cold_transitions', [])
            
            prompt = f"""
            HYBRID MATHEMATICAL MODEL for {game_type}
            
            GAME RULES: Pick {game_config['main_count']} main numbers from 1-{game_config['main_range']}
            {"Pick " + str(game_config['bonus_count']) + " bonus from 1-" + str(game_config['bonus_range']) if game_config['bonus_count'] > 0 else ""}
            
            FOCUS: Hybrid approach combining frequency analysis, drought cycles, transitions, and mathematical balance
            
            ANALYSIS COMPONENTS:
            - Total draws: {total_draws}
            - Drought cycles: {dict(list(drought_cycles.items())[:10])}
            - Hot/cold transitions: {len(hot_cold_transitions)} detected
            - Mathematical range optimization: 1-{game_config['main_range']}
            
            STRATEGY: Synthesize frequency data, drought patterns, mathematical distribution, and transition analysis
            Balance recent trends with statistical reversion probability
            
            Return JSON: {{"main_numbers": [1,2,3,4,5,6], "confidence_percentage": 62, "reasoning": "hybrid mathematical synthesis"}}
            """
            
            response = self.client.models.generate_content(
                model="gemini-2.5-pro",
                contents=prompt,
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    temperature=0.6,
                    max_output_tokens=512
                )
            )
            
            if response.text:
                data = json.loads(response.text)
                main_numbers = self.validate_numbers(data.get('main_numbers', []), game_config['main_count'], game_config['main_range'])
                bonus_numbers = self.validate_numbers(data.get('bonus_numbers', []), game_config['bonus_count'], game_config['bonus_range']) if game_config['bonus_count'] > 0 else []
                
                return ModelPrediction(
                    model_name='hybrid_mathematical',
                    predicted_numbers=sorted(main_numbers),
                    bonus_numbers=sorted(bonus_numbers),
                    confidence_score=data.get('confidence_percentage', 62) / 100.0,
                    reasoning=data.get('reasoning', 'Hybrid mathematical synthesis')
                )
                
        except Exception as e:
            logger.error(f"Hybrid mathematical model error: {e}")
            return None
    
    def generate_prediction(self, game_type: str) -> Optional[LotteryPrediction]:
        """Main prediction method - uses Unified Intelligent Learning System"""
        try:
            logger.info(f"🧠 Generating intelligent prediction for {game_type}")
            
            # Get historical data for prediction
            historical_data = self.get_historical_data_for_prediction(game_type)
            
            if not historical_data or not historical_data.get('draws'):
                logger.error(f"No historical data available for {game_type}")
                return None
                
            # Use unified intelligent prediction system
            logger.info("🎯 Using Hybrid Frequency-Gap Analysis with Learning...")
            prediction = self.generate_intelligent_prediction(game_type, historical_data)
            
            if prediction:
                logger.info("✅ Intelligent prediction generated successfully")
                return prediction
            
            logger.error(f"❌ Intelligent prediction failed for {game_type}")
            return None
            
        except Exception as e:
            logger.error(f"Error in intelligent prediction generation: {e}")
            return None
    
    def generate_intelligent_prediction(self, game_type: str, historical_data: Dict[str, Any]) -> Optional[LotteryPrediction]:
        """Generate prediction using Hybrid Frequency-Gap Analysis with Learning - UNIFIED INTELLIGENT SYSTEM"""
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
                    temperature=0.7,
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
                        prediction_method="Hybrid_Frequency_Gap_Analysis_with_Learning",
                        reasoning=f"Intelligent prediction using Hybrid Frequency-Gap Analysis with Learning methodology: {total_draws}+ historical draws analyzed, hot/cold number patterns, mean reversion strategies, and performance-based learning integration - " + prediction_data.get('reasoning', 'Multi-timeframe pattern analysis with cyclical detection'),
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
    
    def generate_ai_prediction(self, game_type: str, historical_data: Dict[str, Any], variation_seed: int = 1) -> LotteryPrediction:
        """Generate AI prediction using advanced analysis - MISSING METHOD RESTORED"""
        try:
            # Get game configuration
            game_config = self.get_game_configuration(game_type)
            
            # Extract key data for focused analysis
            recent_draws = historical_data.get('draws', [])[:10]  # Last 10 draws only
            frequency_analysis = dict(list(historical_data.get('frequency_analysis', {}).items())[:30])  # Top 30 numbers
            prize_patterns = historical_data.get('prize_patterns', {})
            temporal_patterns = historical_data.get('temporal_patterns', {})
            
            # Create focused, game-specific prompt
            prediction_prompt = f"""
            FOCUSED LOTTERY ANALYSIS FOR {game_type}
            
            OBJECTIVE: Analyze {game_type} lottery data to identify exploitable patterns and generate predictions.
            
            GAME RULES:
            - Pick {game_config['main_count']} main numbers from 1-{game_config['main_range']}
            {"- Pick " + str(game_config['bonus_count']) + " bonus numbers from 1-" + str(game_config['bonus_range']) if game_config['bonus_count'] > 0 else ""}
            
            RECENT WINNING PATTERNS (Last 10 draws):
            {self.serialize_data_safe(recent_draws)}
            
            NUMBER FREQUENCY ANALYSIS:
            {frequency_analysis}
            
            PRIZE DISTRIBUTION INSIGHTS:
            - Jackpot progression: {prize_patterns.get('jackpot_progression', [])[-5:]}
            - Rollover frequency: {prize_patterns.get('rollover_frequency', 0)} out of {historical_data.get('total_draws', 0)} draws
            
            TEMPORAL PATTERNS:
            - Day of week distribution: {temporal_patterns.get('day_of_week_frequency', {})}
            
            ANALYSIS TASKS:
            1. Identify number patterns that appear frequently in recent draws
            2. Look for mathematical relationships (sums, even/odd ratios, consecutive pairs)
            3. Consider temporal factors (day patterns, seasonal trends)
            4. Analyze prize distribution anomalies that might indicate algorithmic behavior
            
            PREDICTION REQUIREMENTS:
            - Generate {game_config['main_count']} main numbers (1-{game_config['main_range']})
            {"- Generate " + str(game_config['bonus_count']) + " bonus numbers (1-" + str(game_config['bonus_range']) + ") if applicable" if game_config['bonus_count'] > 0 else ""}
            - Provide confidence percentage (0-100%)
            - Explain your reasoning focusing on exploitable patterns found
            
            VARIATION SEED: {variation_seed} (use this to ensure different predictions for the same game)
            
            Return your response in this EXACT JSON format:
            {{
                "main_numbers": [num1, num2, num3, num4, num5{"num6" if game_config['main_count'] == 6 else ""}],
                {"bonus_numbers: [bonus_num]," if game_config['bonus_count'] > 0 else ""}
                "confidence_percentage": 45,
                "reasoning": "Exploitable pattern analysis based on frequency and temporal data"
            }}
            """
            
            response = self.client.models.generate_content(
                model="gemini-2.5-pro",
                contents=prediction_prompt,
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    temperature=0.6 + (variation_seed * 0.01),
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
                        prediction_method="Hybrid_Frequency_Gap_Analysis_with_Learning",
                        reasoning=f"Intelligent prediction using Hybrid Frequency-Gap Analysis with Learning methodology: Advanced analysis - " + prediction_data.get('reasoning', 'AI analysis of historical patterns'),
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

    def serialize_data_safe(self, data):
        """Safely serialize data by converting Decimal and other non-JSON types"""
        import decimal
        
        def convert_item(obj):
            if isinstance(obj, decimal.Decimal):
                return float(obj)
            elif isinstance(obj, dict):
                return {k: convert_item(v) for k, v in obj.items()}
            elif isinstance(obj, list):
                return [convert_item(item) for item in obj]
            else:
                return obj
        
        try:
            converted = convert_item(data)
            return json.dumps(converted, indent=2)
        except Exception as e:
            return f"[Data serialization error: {e}]"

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
        """Store prediction in database with duplicate prevention (1 prediction per game type per draw rule)"""
        try:
            with psycopg2.connect(self.connection_string) as conn:
                with conn.cursor() as cur:
                    # Calculate next draw date
                    if prediction.game_type == 'DAILY LOTTO':
                        next_draw = datetime.now().date() + timedelta(days=1)
                    else:
                        next_draw = datetime.now().date() + timedelta(days=7)
                    
                    # CRITICAL: Check for existing predictions for this game type and target date
                    cur.execute("""
                        SELECT id, is_locked FROM lottery_predictions 
                        WHERE game_type = %s AND target_draw_date = %s
                    """, (prediction.game_type, next_draw))
                    
                    existing_prediction = cur.fetchone()
                    
                    if existing_prediction:
                        # Check if prediction is locked (stable)
                        if existing_prediction[1]:  # is_locked = True
                            logger.info(f"🔒 Prediction for {prediction.game_type} on {next_draw} is locked - skipping update")
                            return True
                        # Update existing prediction instead of creating duplicate (1 prediction per draw rule)
                        logger.info(f"Updating existing prediction {existing_prediction[0]} for {prediction.game_type} on {next_draw}")
                        cur.execute("""
                            UPDATE lottery_predictions 
                            SET predicted_numbers = %s, bonus_numbers = %s, confidence_score = %s,
                                reasoning = %s, prediction_method = %s, created_at = %s,
                                ensemble_composition = %s, model_weights = %s
                            WHERE id = %s
                        """, (
                            prediction.predicted_numbers,
                            prediction.bonus_numbers,
                            prediction.confidence_score,
                            prediction.reasoning,
                            prediction.prediction_method,
                            prediction.created_at,
                            json.dumps(prediction.ensemble_composition) if prediction.ensemble_composition else None,
                            json.dumps(prediction.model_weights) if prediction.model_weights else None,
                            existing_prediction[0]
                        ))
                        logger.info(f"✅ Updated existing {prediction.prediction_method} prediction for {prediction.game_type}")
                    else:
                        # Insert new prediction
                        cur.execute("""
                            INSERT INTO lottery_predictions (
                                game_type, predicted_numbers, bonus_numbers, 
                                confidence_score, prediction_method, reasoning, 
                                target_draw_date, created_at, ensemble_composition, model_weights
                            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                        """, (
                            prediction.game_type,
                            prediction.predicted_numbers,
                            prediction.bonus_numbers,
                            prediction.confidence_score,
                            prediction.prediction_method,
                            prediction.reasoning,
                            next_draw,
                            prediction.created_at,
                            json.dumps(prediction.ensemble_composition) if prediction.ensemble_composition else None,
                            json.dumps(prediction.model_weights) if prediction.model_weights else None
                        ))
                        logger.info(f"✅ Stored new {prediction.prediction_method} prediction for {prediction.game_type}")
                    
                    conn.commit()
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