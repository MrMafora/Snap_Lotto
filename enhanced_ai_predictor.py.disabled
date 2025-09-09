#!/usr/bin/env python3
"""
Enhanced AI Lottery Predictor with Near-Miss Learning Integration
Combines traditional frequency analysis with near-miss pattern learning
"""

import os
import json
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any, Tuple
import psycopg2
from google import genai
from google.genai import types
from near_miss_learning_system import NearMissLearningSystem

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize Gemini client
client = genai.Client(api_key=os.environ.get("GOOGLE_API_KEY_SNAP_LOTTERY"))

class EnhancedAIPredictor:
    """Enhanced lottery predictor that learns from near-miss patterns"""
    
    def __init__(self):
        self.connection_string = os.environ.get('DATABASE_URL')
        self.near_miss_system = NearMissLearningSystem()
        
        # Game configurations
        self.game_configs = {
            'DAILY LOTTO': {'main_count': 5, 'range': (1, 36), 'bonus_count': 0},
            'LOTTO': {'main_count': 6, 'range': (1, 52), 'bonus_count': 0},
            'LOTTO PLUS 1': {'main_count': 6, 'range': (1, 52), 'bonus_count': 0},
            'LOTTO PLUS 2': {'main_count': 6, 'range': (1, 52), 'bonus_count': 0},
            'POWERBALL': {'main_count': 5, 'range': (1, 50), 'bonus_count': 1, 'bonus_range': (1, 20)},
            'POWERBALL PLUS': {'main_count': 5, 'range': (1, 50), 'bonus_count': 1, 'bonus_range': (1, 20)}
        }
    
    def get_historical_data(self, game_type: str, days_back: int = 100) -> List[Dict]:
        """Get historical lottery results for analysis"""
        try:
            with psycopg2.connect(self.connection_string) as conn:
                with conn.cursor() as cur:
                    cutoff_date = (datetime.now() - timedelta(days=days_back)).date()
                    
                    cur.execute("""
                        SELECT main_numbers, bonus_numbers, draw_date, draw_number
                        FROM lottery_results 
                        WHERE lottery_type = %s 
                            AND draw_date >= %s 
                            AND main_numbers IS NOT NULL
                        ORDER BY draw_date DESC
                    """, (game_type, cutoff_date))
                    
                    results = []
                    for main_nums, bonus_nums, draw_date, draw_num in cur.fetchall():
                        results.append({
                            'main_numbers': main_nums,
                            'bonus_numbers': bonus_nums or [],
                            'draw_date': draw_date,
                            'draw_number': draw_num
                        })
                    
                    return results
        except Exception as e:
            logger.error(f"Error getting historical data: {e}")
            return []
    
    def analyze_frequency_patterns(self, historical_data: List[Dict]) -> Dict[str, Any]:
        """Analyze number frequency patterns from historical data"""
        main_frequency = {}
        bonus_frequency = {}
        recent_trends = {}
        
        # Analyze main numbers
        for result in historical_data:
            for num in result['main_numbers']:
                main_frequency[num] = main_frequency.get(num, 0) + 1
        
        # Analyze bonus numbers
        for result in historical_data:
            for num in result.get('bonus_numbers', []):
                bonus_frequency[num] = bonus_frequency.get(num, 0) + 1
        
        # Recent trend analysis (last 20 draws)
        recent_results = historical_data[:20]
        for result in recent_results:
            for num in result['main_numbers']:
                recent_trends[num] = recent_trends.get(num, 0) + 1
        
        return {
            'main_frequency': main_frequency,
            'bonus_frequency': bonus_frequency,
            'recent_trends': recent_trends,
            'total_draws': len(historical_data)
        }
    
    def generate_base_prediction(self, game_type: str, frequency_data: Dict) -> Tuple[List[int], List[int]]:
        """Generate base prediction using frequency analysis"""
        config = self.game_configs[game_type]
        main_count = config['main_count']
        min_num, max_num = config['range']
        
        # Balance hot and cold numbers
        hot_numbers = sorted(frequency_data['main_frequency'].items(), 
                           key=lambda x: x[1], reverse=True)[:15]
        cold_numbers = sorted(frequency_data['main_frequency'].items(), 
                            key=lambda x: x[1])[:10]
        
        # Recent trending numbers
        trending = sorted(frequency_data['recent_trends'].items(), 
                         key=lambda x: x[1], reverse=True)[:8]
        
        # Create candidate pool
        candidates = []
        
        # Add hot numbers (40% weight)
        for num, freq in hot_numbers[:6]:
            candidates.extend([num] * 4)
        
        # Add trending numbers (30% weight)  
        for num, freq in trending[:4]:
            candidates.extend([num] * 3)
        
        # Add cold numbers for balance (20% weight)
        for num, freq in cold_numbers[:3]:
            candidates.extend([num] * 2)
        
        # Add some random numbers for diversity (10% weight)
        import random
        for _ in range(5):
            candidates.append(random.randint(min_num, max_num))
        
        # Select main numbers (avoiding duplicates)
        main_numbers = []
        available = list(set(candidates))
        
        while len(main_numbers) < main_count and available:
            # Weighted random selection
            num = random.choices(available, 
                               weights=[candidates.count(x) for x in available])[0]
            main_numbers.append(num)
            available.remove(num)
        
        # Fill any remaining spots
        all_numbers = list(range(min_num, max_num + 1))
        while len(main_numbers) < main_count:
            remaining = [n for n in all_numbers if n not in main_numbers]
            if remaining:
                main_numbers.append(random.choice(remaining))
        
        main_numbers.sort()
        
        # Generate bonus numbers if needed
        bonus_numbers = []
        if config['bonus_count'] > 0:
            bonus_min, bonus_max = config['bonus_range']
            bonus_pool = list(frequency_data['bonus_frequency'].keys()) or list(range(bonus_min, bonus_max + 1))
            bonus_numbers = random.sample(bonus_pool, min(config['bonus_count'], len(bonus_pool)))
        
        return main_numbers, bonus_numbers
    
    def enhance_with_near_miss_learning(self, base_prediction: List[int], 
                                       game_type: str) -> List[int]:
        """Enhance base prediction using near-miss learning"""
        try:
            # Get near-miss patterns for this game type
            patterns = self.near_miss_system.extract_near_miss_patterns(game_type, days_back=30)
            
            if not patterns:
                logger.info("No near-miss patterns found, using base prediction")
                return base_prediction
            
            # Generate adjustment factors
            adjustments = self.near_miss_system.generate_adjustment_vector(patterns)
            
            if not adjustments:
                logger.info("No adjustments calculated, using base prediction")
                return base_prediction
            
            # Apply near-miss learning
            config = self.game_configs[game_type]
            enhanced_prediction = self.near_miss_system.apply_near_miss_learning(
                base_prediction, adjustments, config['range']
            )
            
            logger.info(f"Applied near-miss learning: {base_prediction} → {enhanced_prediction}")
            return enhanced_prediction
            
        except Exception as e:
            logger.error(f"Near-miss learning failed: {e}")
            return base_prediction
    
    def generate_enhanced_prediction(self, game_type: str) -> Dict[str, Any]:
        """Generate enhanced prediction with near-miss learning"""
        try:
            # Get historical data
            historical_data = self.get_historical_data(game_type, days_back=100)
            if not historical_data:
                raise Exception("No historical data available")
            
            # Analyze frequency patterns
            frequency_data = self.analyze_frequency_patterns(historical_data)
            
            # Generate base prediction
            main_numbers, bonus_numbers = self.generate_base_prediction(game_type, frequency_data)
            
            # Enhance with near-miss learning
            enhanced_main = self.enhance_with_near_miss_learning(main_numbers, game_type)
            
            # Calculate confidence score
            confidence = self.calculate_enhanced_confidence(
                enhanced_main, frequency_data, game_type
            )
            
            # Generate AI reasoning
            reasoning = self.generate_ai_reasoning(
                enhanced_main, bonus_numbers, frequency_data, game_type
            )
            
            return {
                'main_numbers': enhanced_main,
                'bonus_numbers': bonus_numbers,
                'confidence': confidence,
                'method': 'Hybrid Frequency-Gap Analysis with Near-Miss Learning',
                'reasoning': reasoning
            }
            
        except Exception as e:
            logger.error(f"Enhanced prediction failed: {e}")
            raise e
    
    def calculate_enhanced_confidence(self, numbers: List[int], 
                                     frequency_data: Dict, game_type: str) -> float:
        """Calculate confidence score including near-miss factors"""
        base_confidence = 45.0  # Base confidence
        
        # Frequency alignment bonus
        main_freq = frequency_data['main_frequency']
        avg_frequency = sum(main_freq.values()) / len(main_freq) if main_freq else 0
        
        frequency_bonus = 0
        for num in numbers:
            num_freq = main_freq.get(num, 0)
            if num_freq > avg_frequency:
                frequency_bonus += 2
            elif num_freq > avg_frequency * 0.8:
                frequency_bonus += 1
        
        # Near-miss learning bonus
        patterns = self.near_miss_system.extract_near_miss_patterns(game_type, days_back=30)
        near_miss_bonus = min(len(patterns) * 2, 10)  # Up to 10 points for learning data
        
        # Balance bonus
        num_range = max(numbers) - min(numbers)
        config = self.game_configs[game_type]
        optimal_range = (config['range'][1] - config['range'][0]) * 0.6
        balance_bonus = 5 if abs(num_range - optimal_range) < optimal_range * 0.3 else 0
        
        total_confidence = base_confidence + frequency_bonus + near_miss_bonus + balance_bonus
        return min(total_confidence, 85.0)  # Cap at 85%
    
    def generate_ai_reasoning(self, main_numbers: List[int], bonus_numbers: List[int],
                             frequency_data: Dict, game_type: str) -> str:
        """Generate AI reasoning for the prediction"""
        try:
            # Get near-miss insights
            patterns = self.near_miss_system.extract_near_miss_patterns(game_type)
            insights = self.near_miss_system.generate_ai_insights_on_near_misses(patterns)
            
            prompt = f"""Provide reasoning for this enhanced lottery prediction:

Game: {game_type}
Predicted Numbers: {main_numbers}
Bonus Numbers: {bonus_numbers if bonus_numbers else 'None'}

Frequency Data Summary:
- Total historical draws analyzed: {frequency_data.get('total_draws', 0)}
- Hot numbers in prediction: {[n for n in main_numbers if frequency_data['main_frequency'].get(n, 0) > (sum(frequency_data['main_frequency'].values()) / len(frequency_data['main_frequency']) if frequency_data['main_frequency'] else 0)]}
- Recent trending numbers included: {[n for n in main_numbers if frequency_data['recent_trends'].get(n, 0) > 0]}

Near-Miss Learning Insights:
{insights}

Provide a concise reasoning (2-3 sentences) explaining why these numbers were selected based on:
1. Frequency analysis patterns
2. Near-miss learning adjustments  
3. Balance and distribution factors"""

            response = client.models.generate_content(
                model="gemini-2.5-pro",
                contents=prompt
            )
            
            return response.text or "Prediction based on hybrid frequency-gap analysis with near-miss learning enhancement."
            
        except Exception as e:
            logger.error(f"AI reasoning failed: {e}")
            return "Prediction generated using enhanced frequency analysis with near-miss pattern learning."

def test_enhanced_predictor():
    """Test the enhanced predictor"""
    predictor = EnhancedAIPredictor()
    
    print("🧠 Testing Enhanced AI Predictor with Near-Miss Learning")
    print("=" * 60)
    
    # Test Daily Lotto prediction
    try:
        result = predictor.generate_enhanced_prediction('DAILY LOTTO')
        
        print(f"Game Type: DAILY LOTTO")
        print(f"Predicted Numbers: {result['main_numbers']}")
        print(f"Confidence: {result['confidence']:.1f}%")
        print(f"Method: {result['method']}")
        print(f"Reasoning: {result['reasoning'][:200]}...")
        
        return True
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False

if __name__ == "__main__":
    test_enhanced_predictor()