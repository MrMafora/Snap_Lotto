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
        """Get COMPREHENSIVE lottery data for deep AI analysis - ALL available information per draw"""
        try:
            with psycopg2.connect(self.connection_string) as conn:
                with conn.cursor() as cur:
                    cutoff_date = (datetime.now() - timedelta(days=days)).date()
                    
                    # Get ALL available data columns for comprehensive analysis
                    cur.execute("""
                        SELECT 
                            main_numbers, bonus_numbers, draw_date, draw_number,
                            division_1_winners, division_1_payout,
                            division_2_winners, division_2_payout,
                            division_3_winners, division_3_payout,
                            division_4_winners, division_4_payout,
                            division_5_winners, division_5_payout,
                            division_6_winners, division_6_payout,
                            division_7_winners, division_7_payout,
                            division_8_winners, division_8_payout,
                            rollover_amount, estimated_jackpot, total_sales,
                            EXTRACT(DOW FROM draw_date) as day_of_week,
                            EXTRACT(MONTH FROM draw_date) as month,
                            EXTRACT(YEAR FROM draw_date) as year,
                            created_at
                        FROM lottery_results 
                        WHERE lottery_type = %s AND draw_date >= %s 
                        AND main_numbers IS NOT NULL
                        ORDER BY draw_date DESC
                        LIMIT 200
                    """, (game_type, cutoff_date))
                    
                    results = cur.fetchall()
                    
                    comprehensive_data = {
                        'game_type': game_type,
                        'total_draws': len(results),
                        'date_range': {'start': None, 'end': None},
                        'draws': [],
                        'all_numbers': [],
                        'all_bonus': [],
                        'prize_patterns': {
                            'division_winners': defaultdict(list),
                            'division_payouts': defaultdict(list),
                            'jackpot_progression': [],
                            'rollover_frequency': 0,
                            'total_sales_trend': []
                        },
                        'temporal_patterns': {
                            'day_of_week_frequency': defaultdict(int),
                            'monthly_patterns': defaultdict(list),
                            'yearly_trends': defaultdict(list)
                        },
                        'frequency_analysis': {},
                        'sequential_analysis': {},
                        'advanced_patterns': {
                            'number_sum_analysis': [],
                            'even_odd_ratios': [],
                            'high_low_ratios': [],
                            'consecutive_sequences': []
                        }
                    }
                    
                    for i, row in enumerate(results):
                        # Extract all data fields
                        (main_nums, bonus_nums, draw_date, draw_num,
                         d1_win, d1_pay, d2_win, d2_pay, d3_win, d3_pay, d4_win, d4_pay,
                         d5_win, d5_pay, d6_win, d6_pay, d7_win, d7_pay, d8_win, d8_pay,
                         rollover, jackpot, sales, dow, month, year, created) = row
                        
                        # Parse numbers
                        parsed_main = self.parse_numbers(main_nums)
                        parsed_bonus = self.parse_numbers(bonus_nums)
                        
                        if parsed_main:
                            # Core draw data
                            draw_record = {
                                'draw_number': draw_num,
                                'date': draw_date.isoformat() if draw_date else None,
                                'main_numbers': sorted(parsed_main),
                                'bonus_numbers': sorted(parsed_bonus) if parsed_bonus else [],
                                
                                # Complete prize structure
                                'prize_divisions': {
                                    'division_1': {'winners': d1_win, 'payout': d1_pay},
                                    'division_2': {'winners': d2_win, 'payout': d2_pay},
                                    'division_3': {'winners': d3_win, 'payout': d3_pay},
                                    'division_4': {'winners': d4_win, 'payout': d4_pay},
                                    'division_5': {'winners': d5_win, 'payout': d5_pay},
                                    'division_6': {'winners': d6_win, 'payout': d6_pay},
                                    'division_7': {'winners': d7_win, 'payout': d7_pay},
                                    'division_8': {'winners': d8_win, 'payout': d8_pay}
                                },
                                
                                # Financial indicators
                                'financial_data': {
                                    'rollover_amount': rollover,
                                    'estimated_jackpot': jackpot,
                                    'total_sales': sales,
                                    'had_rollover': rollover is not None and rollover > 0
                                },
                                
                                # Temporal data
                                'temporal_data': {
                                    'day_of_week': dow,  # 0=Sunday, 6=Saturday
                                    'month': month,
                                    'year': year,
                                    'processing_date': created.isoformat() if created else None
                                },
                                
                                # Mathematical properties
                                'mathematical_properties': {
                                    'sum_of_numbers': sum(parsed_main),
                                    'even_count': sum(1 for n in parsed_main if n % 2 == 0),
                                    'odd_count': sum(1 for n in parsed_main if n % 2 == 1),
                                    'high_count': sum(1 for n in parsed_main if n > 25),  # Assuming 1-49 range
                                    'low_count': sum(1 for n in parsed_main if n <= 25),
                                    'consecutive_pairs': self.count_consecutive_pairs(parsed_main)
                                }
                            }
                            
                            comprehensive_data['draws'].append(draw_record)
                            comprehensive_data['all_numbers'].extend(parsed_main)
                            if parsed_bonus:
                                comprehensive_data['all_bonus'].extend(parsed_bonus)
                            
                            # Track date range
                            if i == 0:
                                comprehensive_data['date_range']['end'] = draw_date.isoformat() if draw_date else None
                            if i == len(results) - 1:
                                comprehensive_data['date_range']['start'] = draw_date.isoformat() if draw_date else None
                            
                            # Collect prize patterns
                            for div in range(1, 9):
                                winners = locals()[f'd{div}_win']
                                payout = locals()[f'd{div}_pay']
                                if winners is not None:
                                    comprehensive_data['prize_patterns']['division_winners'][f'division_{div}'].append(winners)
                                if payout is not None:
                                    comprehensive_data['prize_patterns']['division_payouts'][f'division_{div}'].append(float(payout))
                            
                            # Track financial trends
                            if jackpot:
                                comprehensive_data['prize_patterns']['jackpot_progression'].append(float(jackpot))
                            if rollover and rollover > 0:
                                comprehensive_data['prize_patterns']['rollover_frequency'] += 1
                            if sales:
                                comprehensive_data['prize_patterns']['total_sales_trend'].append(float(sales))
                            
                            # Track temporal patterns
                            if dow is not None:
                                comprehensive_data['temporal_patterns']['day_of_week_frequency'][int(dow)] += 1
                            if month:
                                comprehensive_data['temporal_patterns']['monthly_patterns'][int(month)].append(parsed_main)
                            if year:
                                comprehensive_data['temporal_patterns']['yearly_trends'][int(year)].append(parsed_main)
                            
                            # Advanced mathematical analysis
                            comprehensive_data['advanced_patterns']['number_sum_analysis'].append(sum(parsed_main))
                            comprehensive_data['advanced_patterns']['even_odd_ratios'].append(
                                (sum(1 for n in parsed_main if n % 2 == 0), sum(1 for n in parsed_main if n % 2 == 1))
                            )
                            comprehensive_data['advanced_patterns']['high_low_ratios'].append(
                                (sum(1 for n in parsed_main if n > 25), sum(1 for n in parsed_main if n <= 25))
                            )
                            comprehensive_data['advanced_patterns']['consecutive_sequences'].append(
                                self.count_consecutive_pairs(parsed_main)
                            )
                    
                    # Calculate comprehensive frequency analysis
                    comprehensive_data['frequency_analysis'] = dict(Counter(comprehensive_data['all_numbers']).most_common())
                    
                    # Analyze sequential patterns with enhanced data
                    comprehensive_data['sequential_analysis'] = self.analyze_sequential_patterns(comprehensive_data['draws'])
                    
                    logger.info(f"Retrieved COMPREHENSIVE data for {game_type}: {len(comprehensive_data['draws'])} draws with full prize/financial/temporal analysis")
                    return comprehensive_data
                    
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
    
    def count_consecutive_pairs(self, numbers: List[int]) -> int:
        """Count consecutive number pairs in a draw"""
        if len(numbers) < 2:
            return 0
        
        sorted_nums = sorted(numbers)
        consecutive_count = 0
        
        for i in range(len(sorted_nums) - 1):
            if sorted_nums[i+1] - sorted_nums[i] == 1:
                consecutive_count += 1
        
        return consecutive_count

    def generate_ai_prediction(self, game_type: str, historical_data: Dict[str, Any], variation_seed: int = 1) -> LotteryPrediction:
        """Use AI to generate lottery number predictions based on historical data"""
        try:
            # Get game configuration
            game_config = self.get_game_configuration(game_type)
            
            # Prepare comprehensive data for deep AI analysis
            prediction_prompt = f"""
            COMPREHENSIVE LOTTERY ALGORITHM ANALYSIS FOR {game_type}
            
            You are an advanced AI tasked with finding hidden patterns in lottery data that might indicate algorithmic behavior or exploitable trends.
            Analyze ALL the provided data - not just winning numbers, but prize distributions, financial patterns, temporal relationships, and mathematical properties.
            
            FULL DATASET FOR ANALYSIS:
            ============================
            
            Game Configuration:
            - Main numbers to pick: {game_config['main_count']} from 1-{game_config['main_range']}
            - Bonus numbers to pick: {game_config['bonus_count']} from 1-{game_config['bonus_range']}
            
            COMPREHENSIVE HISTORICAL DATA:
            =============================
            
            Basic Statistics:
            - Total draws analyzed: {historical_data.get('total_draws', 0)}
            - Date range: {historical_data.get('date_range', {})}
            - Game type: {historical_data.get('game_type', game_type)}
            
            PRIZE DISTRIBUTION PATTERNS (Look for algorithmic anomalies):
            - Division winner counts by level: {historical_data.get('prize_patterns', {}).get('division_winners', {})}
            - Division payout amounts by level: {historical_data.get('prize_patterns', {}).get('division_payouts', {})}
            - Jackpot progression over time: {historical_data.get('prize_patterns', {}).get('jackpot_progression', [])}
            - Rollover frequency: {historical_data.get('prize_patterns', {}).get('rollover_frequency', 0)}
            - Total sales trends: {historical_data.get('prize_patterns', {}).get('total_sales_trend', [])}
            
            TEMPORAL PATTERNS (Check for day/time correlations):
            - Day of week frequency: {historical_data.get('temporal_patterns', {}).get('day_of_week_frequency', {})}
            - Monthly distribution: {dict(list(historical_data.get('temporal_patterns', {}).get('monthly_patterns', {}).items())[:6])}
            - Yearly trends: {dict(list(historical_data.get('temporal_patterns', {}).get('yearly_trends', {}).items())[:3])}
            
            MATHEMATICAL PROPERTIES (Search for algorithmic signatures):
            - Number sum analysis: {historical_data.get('advanced_patterns', {}).get('number_sum_analysis', [])[:20]}
            - Even/odd ratios: {historical_data.get('advanced_patterns', {}).get('even_odd_ratios', [])[:20]}
            - High/low number ratios: {historical_data.get('advanced_patterns', {}).get('high_low_ratios', [])[:20]}
            - Consecutive sequence patterns: {historical_data.get('advanced_patterns', {}).get('consecutive_sequences', [])[:20]}
            
            RECENT DRAW ANALYSIS (Last 15 draws with full context):
            {json.dumps(historical_data.get('draws', [])[:15], indent=2)}
            
            NUMBER FREQUENCY ANALYSIS:
            - Overall frequency (top 20): {dict(list(historical_data.get('frequency_analysis', {}).items())[:20])}
            - All numbers frequency: {historical_data.get('frequency_analysis', {})}
            
            SEQUENTIAL PATTERN ANALYSIS:
            {json.dumps(historical_data.get('sequential_analysis', {}), indent=2)}
            
            CRITICAL ANALYSIS TASKS:
            ========================
            
            1. ALGORITHMIC DETECTION: Look for patterns that suggest non-random generation:
               - Unusual clustering in prize distributions
               - Temporal correlations that shouldn't exist in true randomness
               - Mathematical properties that repeat with suspicious frequency
               - Prize payout patterns that correlate with number selections
            
            2. FINANCIAL CORRELATION ANALYSIS:
               - Do jackpot amounts correlate with specific number patterns?
               - Are there relationships between sales volumes and winning numbers?
               - Do rollover events coincide with certain mathematical properties?
            
            3. TEMPORAL EXPLOITATION:
               - Are certain numbers more likely on specific days/months?
               - Do processing dates reveal any systematic biases?
               - Are there seasonal trends that indicate algorithmic behavior?
            
            4. MATHEMATICAL SIGNATURE DETECTION:
               - Look for sum ranges that appear more frequently than statistical probability suggests
               - Analyze even/odd ratios for non-random distributions
               - Check high/low ratios for algorithmic biases
               - Examine consecutive number patterns for systematic generation
            
            5. PRIZE STRUCTURE ANALYSIS:
               - Do winner counts in different divisions show correlations with number patterns?
               - Are there payout amounts that correlate with specific mathematical properties?
               - Does the frequency of multiple winners suggest predictable patterns?
            
            PREDICTION GENERATION REQUIREMENTS:
            ==================================
            
            Based on your comprehensive analysis, generate a prediction that:
            - Exploits any discovered algorithmic patterns
            - Considers financial and temporal correlations
            - Incorporates mathematical property analysis
            - Accounts for prize distribution anomalies
            - Uses variation seed {variation_seed} for diverse predictions
            
            OUTPUT FORMAT:
            {{
                "main_numbers": [array of {game_config['main_count']} unique integers from 1-{game_config['main_range']}],
                "bonus_numbers": [array of {game_config['bonus_count']} unique integers from 1-{game_config['bonus_range']}],
                "confidence_score": float between 0.0-1.0,
                "reasoning": "Detailed explanation of patterns found and exploitation strategy",
                "algorithmic_indicators": "Specific algorithmic behaviors detected",
                "pattern_strength": "Assessment of pattern reliability",
                "exploitation_strategy": "How the prediction exploits discovered patterns"
            }}
            
            Focus on finding exploitable patterns rather than just statistical analysis. Look for evidence of algorithmic generation that can be predicted.
            """
            
            response = client.models.generate_content(
                model="gemini-2.5-pro",
                contents=prediction_prompt,
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    temperature=min(0.7 + (variation_seed * 0.1), 2.0)  # Fixed temperature range for comprehensive analysis
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
                        'actual_numbers': actual_numbers,
                        'main_matches': main_matches,
                        'bonus_matches': bonus_matches,
                        'accuracy_percentage': accuracy_percentage,
                        'prize_tier': prize_tier,
                        'confidence_score': confidence,
                        'matched_main_numbers': list(set(predicted_numbers) & set(actual_numbers)),
                        'matched_bonus_numbers': list(set(predicted_bonus) & set(actual_bonus)) if predicted_bonus and actual_bonus else []
                    }
                    
                    logger.info(f"Prediction {prediction_id} validated: {main_matches} matches ({accuracy_percentage:.1f}%)")
                    return validation_result
                    
        except Exception as e:
            logger.error(f"Error validating prediction: {e}")
            return {'error': str(e)}

    def calculate_prize_tier(self, game_type: str, main_matches: int, bonus_matches: int) -> str:
        """Calculate the prize tier based on matches"""
        if game_type in ['LOTTO', 'LOTTO PLUS 1', 'LOTTO PLUS 2']:
            if main_matches >= 6: return 'Division 1'
            elif main_matches >= 5: return 'Division 2'
            elif main_matches >= 4: return 'Division 3'
            elif main_matches >= 3: return 'Division 4'
            else: return 'No Prize'
        elif game_type in ['POWERBALL', 'POWERBALL PLUS']:
            if main_matches >= 5 and bonus_matches >= 1: return 'Division 1'
            elif main_matches >= 5: return 'Division 2'
            elif main_matches >= 4 and bonus_matches >= 1: return 'Division 3'
            elif main_matches >= 4: return 'Division 4'
            elif main_matches >= 3 and bonus_matches >= 1: return 'Division 5'
            elif main_matches >= 3: return 'Division 6'
            elif main_matches >= 2 and bonus_matches >= 1: return 'Division 7'
            elif main_matches >= 1 and bonus_matches >= 1: return 'Division 8'
            elif bonus_matches >= 1: return 'Division 9'
            else: return 'No Prize'
        elif game_type == 'DAILY LOTTO':
            if main_matches >= 5: return 'Division 1'
            elif main_matches >= 4: return 'Division 2'
            elif main_matches >= 3: return 'Division 3'
            elif main_matches >= 2: return 'Division 4'
            else: return 'No Prize'
        return 'No Prize'

    def get_prediction_accuracy_insights(self, game_type: str = None, days: int = 30) -> Dict[str, Any]:
        """Analyze prediction accuracy to improve future predictions"""
        try:
            with psycopg2.connect(self.connection_string) as conn:
                with conn.cursor() as cur:
                    # Base query for verified predictions
                    where_clause = "WHERE is_verified = true"
                    params = []
                    
                    if game_type:
                        where_clause += " AND game_type = %s"
                        params.append(game_type)
                    
                    if days:
                        where_clause += " AND verified_at >= NOW() - INTERVAL '%s days'"
                        params.append(days)
                    
                    # Get overall accuracy stats
                    cur.execute(f"""
                        SELECT 
                            game_type,
                            COUNT(*) as total_predictions,
                            AVG(accuracy_percentage) as avg_accuracy,
                            AVG(main_number_matches) as avg_main_matches,
                            AVG(confidence_score) as avg_confidence,
                            COUNT(CASE WHEN main_number_matches >= 3 THEN 1 END) as winning_predictions
                        FROM lottery_predictions 
                        {where_clause}
                        GROUP BY game_type
                        ORDER BY avg_accuracy DESC
                    """, params)
                    
                    accuracy_stats = []
                    for row in cur.fetchall():
                        accuracy_stats.append({
                            'game_type': row[0],
                            'total_predictions': row[1],
                            'avg_accuracy': float(row[2]) if row[2] else 0,
                            'avg_main_matches': float(row[3]) if row[3] else 0,
                            'avg_confidence': float(row[4]) if row[4] else 0,
                            'winning_predictions': row[5],
                            'win_rate': (row[5] / row[1] * 100) if row[1] > 0 else 0
                        })
                    
                    # Get number patterns that performed well
                    cur.execute(f"""
                        SELECT 
                            unnest(predicted_numbers) as number,
                            COUNT(*) as times_predicted,
                            AVG(main_number_matches) as avg_matches_when_predicted
                        FROM lottery_predictions 
                        {where_clause}
                        GROUP BY unnest(predicted_numbers)
                        HAVING COUNT(*) >= 3
                        ORDER BY avg_matches_when_predicted DESC, times_predicted DESC
                        LIMIT 20
                    """, params)
                    
                    successful_numbers = []
                    for row in cur.fetchall():
                        successful_numbers.append({
                            'number': row[0],
                            'times_predicted': row[1],
                            'avg_matches_when_predicted': float(row[2]) if row[2] else 0
                        })
                    
                    return {
                        'accuracy_stats': accuracy_stats,
                        'successful_numbers': successful_numbers,
                        'analysis_period': f"{days} days" if days else "all time",
                        'total_verified_predictions': sum(stat['total_predictions'] for stat in accuracy_stats)
                    }
                    
        except Exception as e:
            logger.error(f"Error getting accuracy insights: {e}")
            return {'error': str(e)}

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