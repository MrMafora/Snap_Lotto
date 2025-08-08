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
    
    def get_historical_data_for_prediction(self, game_type: str, days: int = 365) -> Dict[str, Any]:
        """Get focused historical data for specific game type"""
        try:
            with psycopg2.connect(self.connection_string) as conn:
                with conn.cursor() as cur:
                    # Get recent draws with essential data
                    cur.execute("""
                        SELECT draw_number, draw_date, main_numbers, bonus_numbers,
                               prize_divisions, rollover_amount, estimated_jackpot,
                               EXTRACT(DOW FROM draw_date) as day_of_week,
                               EXTRACT(MONTH FROM draw_date) as month
                        FROM lottery_results 
                        WHERE game_type = %s 
                        AND draw_date >= %s
                        ORDER BY draw_date DESC 
                        LIMIT 15
                    """, (game_type, datetime.now().date() - timedelta(days=days)))
                    
                    results = cur.fetchall()
                    
                    if not results:
                        return {}
                    
                    # Build focused dataset
                    focused_data = {
                        'game_type': game_type,
                        'total_draws': len(results),
                        'draws': [],
                        'all_numbers': [],
                        'frequency_analysis': {},
                        'temporal_patterns': defaultdict(int),
                        'prize_patterns': {
                            'jackpot_progression': [],
                            'rollover_count': 0
                        }
                    }
                    
                    for row in results:
                        draw_num, draw_date, main_nums, bonus_nums, prizes, rollover, jackpot, dow, month = row
                        
                        # Parse numbers
                        parsed_main = self.parse_numbers(main_nums)
                        parsed_bonus = self.parse_numbers(bonus_nums)
                        
                        if parsed_main:
                            # Store draw data
                            draw_record = {
                                'draw_number': draw_num,
                                'draw_date': draw_date.isoformat() if draw_date else None,
                                'main': parsed_main,
                                'bonus': parsed_bonus,
                                'day_of_week': int(dow) if dow else None,
                                'month': int(month) if month else None
                            }
                            
                            focused_data['draws'].append(draw_record)
                            focused_data['all_numbers'].extend(parsed_main)
                            
                            # Track temporal patterns
                            if dow is not None:
                                focused_data['temporal_patterns'][f'day_{int(dow)}'] += 1
                            
                            # Track financial patterns
                            if jackpot:
                                try:
                                    jackpot_val = float(str(jackpot).replace(',', '').replace('R', '').strip())
                                    focused_data['prize_patterns']['jackpot_progression'].append(jackpot_val)
                                except:
                                    pass
                            
                            if rollover and str(rollover).strip() and rollover != '0':
                                focused_data['prize_patterns']['rollover_count'] += 1
                    
                    # Calculate frequency analysis
                    focused_data['frequency_analysis'] = dict(Counter(focused_data['all_numbers']).most_common(30))
                    
                    logger.info(f"Retrieved FOCUSED data for {game_type}: {len(focused_data['draws'])} draws with essential analysis")
                    return focused_data
                    
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
    
    def generate_ai_prediction(self, game_type: str, historical_data: Dict[str, Any], variation_seed: int = 1) -> Optional[LotteryPrediction]:
        """Generate prediction with focused AI analysis"""
        try:
            # Get game configuration
            game_config = self.get_game_configuration(game_type)
            
            # Extract focused data
            recent_draws = historical_data.get('draws', [])[:10]
            frequency_top20 = dict(list(historical_data.get('frequency_analysis', {}).items())[:20])
            
            # Create focused prompt
            prediction_prompt = f"""
            FOCUSED LOTTERY ANALYSIS FOR {game_type}
            
            GAME RULES:
            - Pick {game_config['main_count']} main numbers from 1-{game_config['main_range']}
            {"- Pick " + str(game_config['bonus_count']) + " bonus numbers from 1-" + str(game_config['bonus_range']) if game_config['bonus_count'] > 0 else ""}
            
            RECENT DRAWS (Last 10):
            {json.dumps(recent_draws, indent=2)}
            
            TOP FREQUENT NUMBERS:
            {frequency_top20}
            
            JACKPOT PATTERN:
            {historical_data.get('prize_patterns', {}).get('jackpot_progression', [])[-5:]}
            
            ANALYSIS GOALS:
            1. Find number patterns in recent draws
            2. Identify mathematical relationships
            3. Consider frequency biases
            4. Look for exploitable trends
            
            VARIATION SEED: {variation_seed}
            
            Return ONLY this JSON format:
            {{
                "main_numbers": [list of {game_config['main_count']} numbers],
                {"bonus_numbers: [list of " + str(game_config['bonus_count']) + " numbers]," if game_config['bonus_count'] > 0 else ""}
                "confidence_percentage": 50,
                "reasoning": "Brief explanation of patterns found"
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
                        prediction_method="AI_Gemini_Pattern_Analysis",
                        reasoning=f"Focused analysis: " + prediction_data.get('reasoning', 'Pattern-based prediction'),
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