"""
AI Lottery Number Predictor
Advanced ML-powered prediction system with self-learning capabilities
"""

import json
import logging
import os
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Tuple
import psycopg2
from collections import Counter, defaultdict
import numpy as np
from google import genai
from google.genai import types
from pydantic import BaseModel

# Configure logging
logger = logging.getLogger(__name__)

# Initialize Gemini client
client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))

class LotteryPrediction(BaseModel):
    """Structure for lottery number predictions"""
    game_type: str
    predicted_numbers: List[int]
    bonus_numbers: List[int]
    confidence_score: float
    prediction_method: str
    reasoning: str
    draw_date: str
    created_at: str

class PredictionAccuracy(BaseModel):
    """Structure for tracking prediction accuracy"""
    prediction_id: str
    game_type: str
    predicted_numbers: List[int]
    actual_numbers: List[int]
    matches: int
    bonus_matches: int
    accuracy_score: float
    date_predicted: str
    date_verified: str

class AILotteryPredictor:
    def __init__(self):
        self.connection_string = os.environ.get('DATABASE_URL')
        self.initialize_prediction_tables()
        
    def initialize_prediction_tables(self):
        """Create tables for storing predictions and accuracy tracking"""
        try:
            with psycopg2.connect(self.connection_string) as conn:
                with conn.cursor() as cur:
                    # Create predictions table
                    cur.execute("""
                        CREATE TABLE IF NOT EXISTS lottery_predictions (
                            id SERIAL PRIMARY KEY,
                            game_type VARCHAR(50) NOT NULL,
                            predicted_numbers INTEGER[] NOT NULL,
                            bonus_numbers INTEGER[],
                            confidence_score REAL NOT NULL,
                            prediction_method VARCHAR(100) NOT NULL,
                            reasoning TEXT,
                            target_draw_date DATE NOT NULL,
                            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                            is_verified BOOLEAN DEFAULT FALSE,
                            accuracy_score REAL
                        );
                    """)
                    
                    # Create accuracy tracking table
                    cur.execute("""
                        CREATE TABLE IF NOT EXISTS prediction_accuracy (
                            id SERIAL PRIMARY KEY,
                            prediction_id INTEGER REFERENCES lottery_predictions(id),
                            game_type VARCHAR(50) NOT NULL,
                            predicted_numbers INTEGER[] NOT NULL,
                            actual_numbers INTEGER[] NOT NULL,
                            bonus_predicted INTEGER[],
                            bonus_actual INTEGER[],
                            main_matches INTEGER NOT NULL,
                            bonus_matches INTEGER DEFAULT 0,
                            accuracy_score REAL NOT NULL,
                            date_predicted DATE NOT NULL,
                            date_verified DATE NOT NULL,
                            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                        );
                    """)
                    
                    # Create indexes for performance
                    cur.execute("CREATE INDEX IF NOT EXISTS idx_predictions_game_date ON lottery_predictions(game_type, target_draw_date);")
                    cur.execute("CREATE INDEX IF NOT EXISTS idx_accuracy_game ON prediction_accuracy(game_type);")
                    
                    conn.commit()
                    logger.info("Prediction tables initialized successfully")
                    
        except Exception as e:
            logger.error(f"Error initializing prediction tables: {e}")

    def get_historical_data_for_prediction(self, game_type: str, days: int = 365) -> Dict[str, Any]:
        """Get historical lottery data for AI analysis and prediction"""
        try:
            with psycopg2.connect(self.connection_string) as conn:
                with conn.cursor() as cur:
                    cutoff_date = (datetime.now() - timedelta(days=days)).date()
                    
                    cur.execute("""
                        SELECT main_numbers, bonus_numbers, draw_date, draw_number
                        FROM lottery_results 
                        WHERE lottery_type = %s AND draw_date >= %s 
                        AND main_numbers IS NOT NULL
                        ORDER BY draw_date DESC
                        LIMIT 200
                    """, (game_type, cutoff_date))
                    
                    results = cur.fetchall()
                    
                    historical_data = {
                        'draws': [],
                        'all_numbers': [],
                        'all_bonus': [],
                        'recent_patterns': [],
                        'frequency_analysis': {},
                        'sequential_analysis': {}
                    }
                    
                    for row in results:
                        main_numbers, bonus_numbers, draw_date, draw_number = row
                        
                        # Parse main numbers
                        parsed_main = self.parse_numbers(main_numbers)
                        parsed_bonus = self.parse_numbers(bonus_numbers)
                        
                        if parsed_main:
                            historical_data['draws'].append({
                                'main': sorted(parsed_main),
                                'bonus': sorted(parsed_bonus) if parsed_bonus else [],
                                'date': draw_date.isoformat() if draw_date else None,
                                'draw_number': draw_number
                            })
                            
                            historical_data['all_numbers'].extend(parsed_main)
                            if parsed_bonus:
                                historical_data['all_bonus'].extend(parsed_bonus)
                    
                    # Calculate frequency analysis
                    historical_data['frequency_analysis'] = dict(Counter(historical_data['all_numbers']).most_common())
                    
                    # Analyze sequential patterns
                    historical_data['sequential_analysis'] = self.analyze_sequential_patterns(historical_data['draws'])
                    
                    return historical_data
                    
        except Exception as e:
            logger.error(f"Error getting historical data: {e}")
            return {}

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

    def analyze_sequential_patterns(self, draws: List[Dict]) -> Dict[str, Any]:
        """Analyze sequential patterns in historical draws"""
        patterns = {
            'consecutive_pairs': [],
            'number_gaps': defaultdict(list),
            'position_analysis': defaultdict(list),
            'draw_intervals': []
        }
        
        try:
            for i, draw in enumerate(draws):
                main_numbers = draw.get('main', [])
                
                # Find consecutive pairs
                for j in range(len(main_numbers) - 1):
                    if main_numbers[j+1] - main_numbers[j] == 1:
                        patterns['consecutive_pairs'].append((main_numbers[j], main_numbers[j+1]))
                
                # Analyze number positions
                for pos, number in enumerate(sorted(main_numbers)):
                    patterns['position_analysis'][pos].append(number)
                
                # Calculate gaps between draws
                if i < len(draws) - 1:
                    current_draw = draw.get('draw_number', 0)
                    next_draw = draws[i+1].get('draw_number', 0)
                    if current_draw and next_draw:
                        patterns['draw_intervals'].append(current_draw - next_draw)
        
        except Exception as e:
            logger.error(f"Error in sequential analysis: {e}")
        
        return patterns

    def generate_ai_prediction(self, game_type: str, historical_data: Dict[str, Any]) -> LotteryPrediction:
        """Use AI to generate lottery number predictions based on historical data"""
        try:
            # Get game configuration
            game_config = self.get_game_configuration(game_type)
            
            # Prepare data for AI analysis
            prediction_prompt = f"""
            Based on the following historical lottery data for {game_type}, generate a prediction for the next draw.
            
            Game Configuration:
            - Main numbers to pick: {game_config['main_count']} from 1-{game_config['main_range']}
            - Bonus numbers to pick: {game_config['bonus_count']} from 1-{game_config['bonus_range']}
            
            Historical Data Summary:
            - Total draws analyzed: {len(historical_data.get('draws', []))}
            - Recent draws (last 10): {historical_data.get('draws', [])[:10]}
            - Number frequency (top 15): {dict(list(historical_data.get('frequency_analysis', {}).items())[:15])}
            - Sequential patterns: {historical_data.get('sequential_analysis', {})}
            
            Analysis Requirements:
            1. Consider statistical frequency of numbers
            2. Analyze recent trends and patterns
            3. Look for sequential relationships
            4. Account for randomness and avoid overfitting
            5. Provide confidence score (0.0-1.0)
            6. Explain reasoning behind selections
            
            Generate prediction with:
            - Main numbers: {game_config['main_count']} unique numbers
            - Bonus numbers: {game_config['bonus_count']} unique numbers (if applicable)
            - Confidence score based on pattern strength
            - Clear reasoning for number selection
            """
            
            response = client.models.generate_content(
                model="gemini-2.5-pro",
                contents=prediction_prompt,
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    temperature=0.4
                )
            )
            
            if response.text:
                ai_response = json.loads(response.text)
                
                # Validate and clean the prediction
                main_numbers = self.validate_numbers(
                    ai_response.get('main_numbers', []),
                    game_config['main_count'],
                    game_config['main_range']
                )
                
                bonus_numbers = self.validate_numbers(
                    ai_response.get('bonus_numbers', []),
                    game_config['bonus_count'],
                    game_config['bonus_range']
                ) if game_config['bonus_count'] > 0 else []
                
                return LotteryPrediction(
                    game_type=game_type,
                    predicted_numbers=sorted(main_numbers),
                    bonus_numbers=sorted(bonus_numbers),
                    confidence_score=min(max(ai_response.get('confidence_score', 0.5), 0.0), 1.0),
                    prediction_method="AI_Gemini_Pattern_Analysis",
                    reasoning=ai_response.get('reasoning', 'AI analysis of historical patterns'),
                    draw_date=self.get_next_draw_date(game_type),
                    created_at=datetime.now().isoformat()
                )
            
        except Exception as e:
            logger.error(f"Error generating AI prediction: {e}")
            # Fall back to statistical prediction
            return self.generate_statistical_fallback(game_type, historical_data)

    def validate_numbers(self, numbers: List[int], required_count: int, max_range: int) -> List[int]:
        """Validate and ensure prediction numbers meet game requirements"""
        try:
            # Remove duplicates and filter valid range
            valid_numbers = list(set([n for n in numbers if 1 <= n <= max_range]))
            
            # If we don't have enough numbers, fill with statistical picks
            if len(valid_numbers) < required_count:
                # Add most frequent numbers not already selected
                remaining_needed = required_count - len(valid_numbers)
                available_numbers = [n for n in range(1, max_range + 1) if n not in valid_numbers]
                
                # Add random selections from available numbers
                import random
                additional_numbers = random.sample(available_numbers, min(remaining_needed, len(available_numbers)))
                valid_numbers.extend(additional_numbers)
            
            # Return exactly the required count
            return valid_numbers[:required_count]
            
        except Exception as e:
            logger.error(f"Error validating numbers: {e}")
            # Return random selection as absolute fallback
            import random
            return random.sample(range(1, max_range + 1), required_count)

    def get_game_configuration(self, game_type: str) -> Dict[str, int]:
        """Get game configuration for number generation"""
        configs = {
            'LOTTO': {'main_count': 6, 'main_range': 52, 'bonus_count': 0, 'bonus_range': 0},
            'LOTTO PLUS 1': {'main_count': 6, 'main_range': 52, 'bonus_count': 0, 'bonus_range': 0},
            'LOTTO PLUS 2': {'main_count': 6, 'main_range': 52, 'bonus_count': 0, 'bonus_range': 0},
            'POWERBALL': {'main_count': 5, 'main_range': 50, 'bonus_count': 1, 'bonus_range': 20},
            'POWERBALL PLUS': {'main_count': 5, 'main_range': 50, 'bonus_count': 1, 'bonus_range': 20},
            'DAILY LOTTO': {'main_count': 5, 'main_range': 36, 'bonus_count': 0, 'bonus_range': 0}
        }
        return configs.get(game_type, {'main_count': 6, 'main_range': 49, 'bonus_count': 1, 'bonus_range': 10})

    def get_next_draw_date(self, game_type: str) -> str:
        """Estimate next draw date for the game type"""
        # This would be more sophisticated in production, accounting for actual draw schedules
        tomorrow = datetime.now() + timedelta(days=1)
        return tomorrow.strftime('%Y-%m-%d')

    def generate_statistical_fallback(self, game_type: str, historical_data: Dict[str, Any]) -> LotteryPrediction:
        """Generate prediction using statistical methods as fallback"""
        try:
            game_config = self.get_game_configuration(game_type)
            frequency_data = historical_data.get('frequency_analysis', {})
            
            # Select most frequent numbers with some randomization
            if frequency_data:
                frequent_numbers = list(frequency_data.keys())[:game_config['main_range'] // 2]
                remaining_numbers = [n for n in range(1, game_config['main_range'] + 1) if n not in frequent_numbers]
                
                # Mix frequent and less frequent numbers
                import random
                main_prediction = random.sample(frequent_numbers, min(game_config['main_count'] // 2, len(frequent_numbers)))
                main_prediction.extend(random.sample(remaining_numbers, game_config['main_count'] - len(main_prediction)))
            else:
                # Pure random selection
                import random
                main_prediction = random.sample(range(1, game_config['main_range'] + 1), game_config['main_count'])
            
            bonus_prediction = []
            if game_config['bonus_count'] > 0:
                import random
                bonus_prediction = random.sample(range(1, game_config['bonus_range'] + 1), game_config['bonus_count'])
            
            return LotteryPrediction(
                game_type=game_type,
                predicted_numbers=sorted(main_prediction),
                bonus_numbers=sorted(bonus_prediction),
                confidence_score=0.3,  # Lower confidence for statistical fallback
                prediction_method="Statistical_Fallback",
                reasoning="Statistical analysis of number frequency patterns",
                draw_date=self.get_next_draw_date(game_type),
                created_at=datetime.now().isoformat()
            )
            
        except Exception as e:
            logger.error(f"Error in statistical fallback: {e}")
            # Return minimal prediction
            return LotteryPrediction(
                game_type=game_type,
                predicted_numbers=[1, 2, 3, 4, 5, 6][:game_config.get('main_count', 6)],
                bonus_numbers=[1] if game_config.get('bonus_count', 0) > 0 else [],
                confidence_score=0.1,
                prediction_method="Minimal_Fallback",
                reasoning="Minimal prediction due to system error",
                draw_date=self.get_next_draw_date(game_type),
                created_at=datetime.now().isoformat()
            )

    def save_prediction(self, prediction: LotteryPrediction) -> int:
        """Save prediction to database and return prediction ID"""
        try:
            with psycopg2.connect(self.connection_string) as conn:
                with conn.cursor() as cur:
                    cur.execute("""
                        INSERT INTO lottery_predictions 
                        (game_type, predicted_numbers, bonus_numbers, confidence_score, 
                         prediction_method, reasoning, target_draw_date)
                        VALUES (%s, %s, %s, %s, %s, %s, %s)
                        RETURNING id
                    """, (
                        prediction.game_type,
                        prediction.predicted_numbers,
                        prediction.bonus_numbers,
                        prediction.confidence_score,
                        prediction.prediction_method,
                        prediction.reasoning,
                        prediction.draw_date
                    ))
                    
                    prediction_id = cur.fetchone()[0]
                    conn.commit()
                    logger.info(f"Prediction saved with ID: {prediction_id}")
                    return prediction_id
                    
        except Exception as e:
            logger.error(f"Error saving prediction: {e}")
            return -1

    def verify_predictions(self) -> List[PredictionAccuracy]:
        """Check recent predictions against actual results and calculate accuracy"""
        accuracy_results = []
        
        try:
            with psycopg2.connect(self.connection_string) as conn:
                with conn.cursor() as cur:
                    # Get unverified predictions from the last 30 days
                    cur.execute("""
                        SELECT p.id, p.game_type, p.predicted_numbers, p.bonus_numbers, 
                               p.target_draw_date, p.created_at
                        FROM lottery_predictions p
                        WHERE p.is_verified = FALSE 
                        AND p.target_draw_date <= CURRENT_DATE
                        AND p.created_at >= CURRENT_DATE - INTERVAL '30 days'
                        ORDER BY p.target_draw_date DESC
                    """)
                    
                    unverified_predictions = cur.fetchall()
                    
                    for prediction_row in unverified_predictions:
                        prediction_id, game_type, predicted_main, predicted_bonus, target_date, created_at = prediction_row
                        
                        # Find actual results for this game and date range
                        cur.execute("""
                            SELECT main_numbers, bonus_numbers, draw_date
                            FROM lottery_results 
                            WHERE lottery_type = %s 
                            AND draw_date >= %s 
                            AND draw_date <= %s + INTERVAL '7 days'
                            ORDER BY draw_date ASC
                            LIMIT 1
                        """, (game_type, target_date, target_date))
                        
                        actual_result = cur.fetchone()
                        
                        if actual_result:
                            actual_main, actual_bonus, actual_date = actual_result
                            
                            # Parse actual numbers
                            actual_main_parsed = self.parse_numbers(actual_main)
                            actual_bonus_parsed = self.parse_numbers(actual_bonus)
                            
                            # Calculate accuracy
                            accuracy = self.calculate_prediction_accuracy(
                                predicted_main, predicted_bonus or [],
                                actual_main_parsed, actual_bonus_parsed
                            )
                            
                            # Save accuracy result
                            cur.execute("""
                                INSERT INTO prediction_accuracy 
                                (prediction_id, game_type, predicted_numbers, actual_numbers,
                                 bonus_predicted, bonus_actual, main_matches, bonus_matches,
                                 accuracy_score, date_predicted, date_verified)
                                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                            """, (
                                prediction_id, game_type, predicted_main, actual_main_parsed,
                                predicted_bonus or [], actual_bonus_parsed,
                                accuracy['main_matches'], accuracy['bonus_matches'],
                                accuracy['overall_score'], target_date, actual_date
                            ))
                            
                            # Mark prediction as verified
                            cur.execute("""
                                UPDATE lottery_predictions 
                                SET is_verified = TRUE, accuracy_score = %s
                                WHERE id = %s
                            """, (accuracy['overall_score'], prediction_id))
                            
                            accuracy_results.append(PredictionAccuracy(
                                prediction_id=str(prediction_id),
                                game_type=game_type,
                                predicted_numbers=predicted_main,
                                actual_numbers=actual_main_parsed,
                                matches=accuracy['main_matches'],
                                bonus_matches=accuracy['bonus_matches'],
                                accuracy_score=accuracy['overall_score'],
                                date_predicted=target_date.isoformat(),
                                date_verified=actual_date.isoformat()
                            ))
                    
                    conn.commit()
                    logger.info(f"Verified {len(accuracy_results)} predictions")
                    
        except Exception as e:
            logger.error(f"Error verifying predictions: {e}")
        
        return accuracy_results

    def calculate_prediction_accuracy(self, predicted_main: List[int], predicted_bonus: List[int], 
                                    actual_main: List[int], actual_bonus: List[int]) -> Dict[str, float]:
        """Calculate accuracy score for a prediction"""
        try:
            main_matches = len(set(predicted_main) & set(actual_main))
            bonus_matches = len(set(predicted_bonus) & set(actual_bonus)) if predicted_bonus and actual_bonus else 0
            
            # Calculate overall accuracy score (0.0 to 1.0)
            total_predicted = len(predicted_main) + len(predicted_bonus)
            total_matches = main_matches + bonus_matches
            
            overall_score = total_matches / total_predicted if total_predicted > 0 else 0.0
            
            return {
                'main_matches': main_matches,
                'bonus_matches': bonus_matches,
                'overall_score': overall_score,
                'main_accuracy': main_matches / len(predicted_main) if predicted_main else 0.0,
                'bonus_accuracy': bonus_matches / len(predicted_bonus) if predicted_bonus else 0.0
            }
            
        except Exception as e:
            logger.error(f"Error calculating accuracy: {e}")
            return {'main_matches': 0, 'bonus_matches': 0, 'overall_score': 0.0, 'main_accuracy': 0.0, 'bonus_accuracy': 0.0}

    def get_prediction_performance_stats(self, game_type: str = None, days: int = 90) -> Dict[str, Any]:
        """Get performance statistics for predictions"""
        try:
            with psycopg2.connect(self.connection_string) as conn:
                with conn.cursor() as cur:
                    base_query = """
                        SELECT pa.accuracy_score, pa.main_matches, pa.bonus_matches,
                               p.prediction_method, p.confidence_score
                        FROM prediction_accuracy pa
                        JOIN lottery_predictions p ON pa.prediction_id = p.id
                        WHERE pa.date_verified >= CURRENT_DATE - INTERVAL '%s days'
                    """
                    
                    params = [days]
                    if game_type:
                        base_query += " AND pa.game_type = %s"
                        params.append(game_type)
                    
                    cur.execute(base_query, params)
                    results = cur.fetchall()
                    
                    if not results:
                        return {
                            'total_predictions': 0,
                            'average_accuracy': 0.0,
                            'best_accuracy': 0.0,
                            'method_performance': {},
                            'match_distribution': {}
                        }
                    
                    accuracies = [r[0] for r in results]
                    main_matches = [r[1] for r in results]
                    methods = [r[3] for r in results]
                    
                    # Calculate statistics
                    stats = {
                        'total_predictions': len(results),
                        'average_accuracy': sum(accuracies) / len(accuracies),
                        'best_accuracy': max(accuracies),
                        'worst_accuracy': min(accuracies),
                        'method_performance': {},
                        'match_distribution': dict(Counter(main_matches)),
                        'accuracy_trend': accuracies[-10:]  # Last 10 predictions
                    }
                    
                    # Performance by method
                    method_stats = defaultdict(list)
                    for i, method in enumerate(methods):
                        method_stats[method].append(accuracies[i])
                    
                    for method, scores in method_stats.items():
                        stats['method_performance'][method] = {
                            'count': len(scores),
                            'average': sum(scores) / len(scores),
                            'best': max(scores)
                        }
                    
                    return stats
                    
        except Exception as e:
            logger.error(f"Error getting performance stats: {e}")
            return {}

# Create global predictor instance
predictor = AILotteryPredictor()