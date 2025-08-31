#!/usr/bin/env python3
"""
Simple AI Lottery Predictor using only "Hybrid Frequency-Gap Analysis with Learning"
Fixed for empty response issues with optimized prompts and token limits.
"""

import os
import json
import logging
import psycopg2
from datetime import datetime, timedelta
from google import genai
from google.genai import types
from typing import Dict, List, Optional, Any

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SimpleLotteryPredictor:
    def __init__(self):
        self.connection_string = os.environ.get('DATABASE_URL')
        # Force use of GEMINI_API_KEY by temporarily removing GOOGLE_API_KEY
        gemini_key = os.environ.get('GEMINI_API_KEY')
        self.client = genai.Client(api_key=gemini_key)
        
        # Game configurations
        self.game_configs = {
            'DAILY LOTTO': {'main_count': 5, 'main_range': 36, 'bonus_count': 0, 'bonus_range': 0},
            'LOTTO': {'main_count': 6, 'main_range': 52, 'bonus_count': 1, 'bonus_range': 52},
            'LOTTO PLUS 1': {'main_count': 6, 'main_range': 52, 'bonus_count': 1, 'bonus_range': 52},
            'LOTTO PLUS 2': {'main_count': 6, 'main_range': 52, 'bonus_count': 1, 'bonus_range': 52},
            'POWERBALL': {'main_count': 5, 'main_range': 50, 'bonus_count': 1, 'bonus_range': 20},
            'POWERBALL PLUS': {'main_count': 5, 'main_range': 50, 'bonus_count': 1, 'bonus_range': 20}
        }

    def generate_prediction(self, game_type: str) -> Optional[Dict]:
        """Generate a single prediction using Hybrid Frequency-Gap Analysis with Learning"""
        try:
            # Get historical data
            historical_data = self._get_historical_data(game_type)
            if not historical_data:
                logger.error(f"No historical data for {game_type}")
                return None
            
            # Get game config
            config = self.game_configs.get(game_type)
            if not config:
                logger.error(f"Unknown game type: {game_type}")
                return None
            
            # Create simplified prompt
            prompt = f"""Generate lottery prediction for {game_type}:
            - Pick {config['main_count']} numbers from 1-{config['main_range']}
            {"- Pick 1 bonus from 1-" + str(config['bonus_range']) if config['bonus_count'] > 0 else ""}
            
            Recent results: {historical_data['recent'][:2]}
            Hot numbers: {historical_data['hot'][:6]}
            Cold numbers: {historical_data['cold'][:4]}
            
            Method: Hybrid Frequency-Gap Analysis with Learning
            
            Return JSON: {{"main_numbers": [1,2,3], "bonus_numbers": [1], "confidence": 50, "reasoning": "analysis"}}"""
            
            # Call Gemini API with optimized settings
            response = self.client.models.generate_content(
                model="gemini-2.5-pro",
                contents=prompt,
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    temperature=0.5,
                    max_output_tokens=80
                )
            )
            
            # Parse response
            if not response.text:
                logger.error("Empty response from Gemini API")
                return None
                
            data = json.loads(response.text)
            
            # Validate and format numbers
            main_numbers = self._validate_numbers(
                data.get('main_numbers', []), 
                config['main_count'], 
                config['main_range']
            )
            
            bonus_numbers = []
            if config['bonus_count'] > 0:
                bonus_numbers = self._validate_numbers(
                    data.get('bonus_numbers', []),
                    config['bonus_count'],
                    config['bonus_range']
                )
            
            if len(main_numbers) != config['main_count']:
                logger.error(f"Invalid main numbers count: {len(main_numbers)} vs {config['main_count']}")
                return None
            
            # Get next draw info
            next_draw_info = self._get_next_draw_info(game_type)
            
            return {
                'game_type': game_type,
                'predicted_numbers': sorted(main_numbers),
                'bonus_numbers': sorted(bonus_numbers) if bonus_numbers else None,
                'confidence_score': min(data.get('confidence', 50), 65),  # Cap at 65%
                'prediction_method': 'Hybrid Frequency-Gap Analysis with Learning',
                'reasoning': data.get('reasoning', 'AI-generated prediction based on historical analysis'),
                'target_draw_date': next_draw_info['date'],
                'linked_draw_id': next_draw_info['draw_id'],
                'created_at': datetime.now()
            }
            
        except Exception as e:
            logger.error(f"Error generating prediction for {game_type}: {e}")
            return None

    def _get_historical_data(self, game_type: str) -> Optional[Dict]:
        """Get historical data for analysis"""
        try:
            with psycopg2.connect(self.connection_string) as conn:
                with conn.cursor() as cur:
                    # Get recent draws
                    cur.execute("""
                        SELECT draw_date, main_numbers, bonus_numbers 
                        FROM lottery_results 
                        WHERE lottery_type = %s 
                        ORDER BY draw_date DESC 
                        LIMIT 20
                    """, (game_type,))
                    
                    recent_draws = []
                    all_main_numbers = []
                    all_bonus_numbers = []
                    
                    for row in cur.fetchall():
                        main_nums = json.loads(row[1]) if isinstance(row[1], str) else row[1]
                        bonus_nums = json.loads(row[2]) if row[2] and isinstance(row[2], str) else (row[2] or [])
                        
                        recent_draws.append({
                            'date': str(row[0]),
                            'main': main_nums,
                            'bonus': bonus_nums
                        })
                        
                        all_main_numbers.extend(main_nums)
                        if bonus_nums:
                            all_bonus_numbers.extend(bonus_nums)
                    
                    # Calculate frequency
                    from collections import Counter
                    main_freq = Counter(all_main_numbers)
                    
                    # Get hot and cold numbers
                    config = self.game_configs[game_type]
                    all_possible = list(range(1, config['main_range'] + 1))
                    
                    sorted_by_freq = sorted(main_freq.items(), key=lambda x: x[1], reverse=True)
                    hot_numbers = [num for num, freq in sorted_by_freq[:8]]
                    cold_numbers = [num for num in all_possible if num not in [n for n, f in sorted_by_freq[:15]]][:6]
                    
                    return {
                        'recent': recent_draws,
                        'hot': hot_numbers,
                        'cold': cold_numbers,
                        'total_draws': len(recent_draws)
                    }
                    
        except Exception as e:
            logger.error(f"Error getting historical data: {e}")
            return None

    def _get_next_draw_info(self, game_type: str) -> Dict:
        """Get next draw date and ID from extracted image data"""
        try:
            with psycopg2.connect(self.connection_string) as conn:
                with conn.cursor() as cur:
                    # First, try to get next draw info from the most recent extraction
                    cur.execute("""
                        SELECT draw_number, next_draw_date 
                        FROM lottery_results 
                        WHERE lottery_type = %s 
                          AND next_draw_date IS NOT NULL
                          AND next_draw_date != ''
                        ORDER BY draw_date DESC, created_at DESC
                        LIMIT 1
                    """, (game_type,))
                    
                    result = cur.fetchone()
                    if result and result[1]:
                        last_draw_num = result[0]
                        extracted_next_date = result[1]
                        
                        # Parse the extracted next draw date
                        try:
                            if isinstance(extracted_next_date, str):
                                next_date = datetime.strptime(extracted_next_date, '%Y-%m-%d').date()
                            else:
                                next_date = extracted_next_date
                            
                            # Ensure the extracted date is in the future
                            today = datetime.now().date()
                            if next_date > today:
                                return {
                                    'draw_id': last_draw_num + 1,
                                    'date': next_date
                                }
                        except Exception as date_e:
                            logger.warning(f"Could not parse extracted next draw date '{extracted_next_date}': {date_e}")
                    
                    # Fallback: Calculate next draw if no extracted data available
                    cur.execute("""
                        SELECT MAX(draw_number), MAX(draw_date) 
                        FROM lottery_results 
                        WHERE lottery_type = %s
                    """, (game_type,))
                    
                    fallback_result = cur.fetchone()
                    if fallback_result and fallback_result[0]:
                        last_draw_num = fallback_result[0]
                        last_draw_date = fallback_result[1]
                        
                        # Calculate next draw - always ensure it's in the future
                        today = datetime.now().date()
                        
                        if game_type == 'DAILY LOTTO':
                            next_date = max(last_draw_date + timedelta(days=1), today + timedelta(days=1))
                        elif game_type in ['POWERBALL', 'POWERBALL PLUS']:
                            next_date = last_draw_date + timedelta(days=3)
                            while next_date <= today:
                                next_date += timedelta(days=3)
                        else:  # LOTTO games
                            next_date = last_draw_date + timedelta(days=3)
                            while next_date <= today:
                                next_date += timedelta(days=3)
                        
                        return {
                            'draw_id': last_draw_num + 1,
                            'date': next_date
                        }
                    
                    return {'draw_id': 1, 'date': datetime.now().date() + timedelta(days=1)}
                    
        except Exception as e:
            logger.error(f"Error getting next draw info: {e}")
            return {'draw_id': 1, 'date': datetime.now().date() + timedelta(days=1)}

    def _validate_numbers(self, numbers: List[int], count: int, max_range: int) -> List[int]:
        """Validate and fix number selection"""
        if not numbers:
            return []
        
        # Filter valid numbers
        valid_numbers = [n for n in numbers if isinstance(n, int) and 1 <= n <= max_range]
        
        # Remove duplicates while preserving order
        seen = set()
        unique_numbers = []
        for n in valid_numbers:
            if n not in seen:
                seen.add(n)
                unique_numbers.append(n)
        
        # Fill missing numbers if needed
        while len(unique_numbers) < count:
            for candidate in range(1, max_range + 1):
                if candidate not in unique_numbers:
                    unique_numbers.append(candidate)
                    break
                if len(unique_numbers) >= count:
                    break
        
        return unique_numbers[:count]

    def save_prediction(self, prediction: Dict) -> bool:
        """Save prediction to database"""
        try:
            with psycopg2.connect(self.connection_string) as conn:
                with conn.cursor() as cur:
                    # Check for existing prediction for this draw
                    cur.execute("""
                        SELECT id FROM lottery_predictions 
                        WHERE game_type = %s AND linked_draw_id = %s AND validation_status = 'pending'
                    """, (prediction['game_type'], prediction['linked_draw_id']))
                    
                    existing = cur.fetchone()
                    
                    if existing:
                        # Update existing
                        cur.execute("""
                            UPDATE lottery_predictions 
                            SET predicted_numbers = %s, bonus_numbers = %s, confidence_score = %s,
                                prediction_method = %s, reasoning = %s, created_at = %s
                            WHERE id = %s
                        """, (
                            prediction['predicted_numbers'],
                            prediction['bonus_numbers'],
                            prediction['confidence_score'],
                            prediction['prediction_method'],
                            prediction['reasoning'],
                            prediction['created_at'],
                            existing[0]
                        ))
                        logger.info(f"Updated existing prediction for {prediction['game_type']} draw {prediction['linked_draw_id']}")
                    else:
                        # Insert new
                        cur.execute("""
                            INSERT INTO lottery_predictions 
                            (game_type, predicted_numbers, bonus_numbers, confidence_score, 
                             prediction_method, reasoning, target_draw_date, created_at, 
                             linked_draw_id, validation_status)
                            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, 'pending')
                        """, (
                            prediction['game_type'],
                            prediction['predicted_numbers'],
                            prediction['bonus_numbers'],
                            prediction['confidence_score'],
                            prediction['prediction_method'],
                            prediction['reasoning'],
                            prediction['target_draw_date'],
                            prediction['created_at'],
                            prediction['linked_draw_id']
                        ))
                        logger.info(f"Created new prediction for {prediction['game_type']} draw {prediction['linked_draw_id']}")
                    
                    conn.commit()
                    return True
                    
        except Exception as e:
            logger.error(f"Error saving prediction: {e}")
            return False

def main():
    """Test the simple predictor"""
    predictor = SimpleLotteryPredictor()
    
    # Test with Daily Lotto
    print("Testing Daily Lotto prediction...")
    prediction = predictor.generate_prediction('DAILY LOTTO')
    
    if prediction:
        print(f"✅ Generated prediction: {prediction['predicted_numbers']}")
        print(f"   Confidence: {prediction['confidence_score']}%")
        print(f"   Method: {prediction['prediction_method']}")
        print(f"   Target draw: {prediction['linked_draw_id']}")
        
        # Save it
        if predictor.save_prediction(prediction):
            print("✅ Prediction saved successfully")
        else:
            print("❌ Failed to save prediction")
    else:
        print("❌ Failed to generate prediction")

if __name__ == "__main__":
    main()