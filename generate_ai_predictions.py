#!/usr/bin/env python3
"""
Generate AI-powered lottery predictions using Gemini 2.5 Pro
Analyzes historical data for each game type individually
"""

import os
import json
import logging
import psycopg2
from datetime import datetime, timedelta
from typing import Dict, List, Any
from collections import defaultdict, Counter

# Import Google Gemini
from google import genai
from google.genai import types

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class GeminiLotteryPredictor:
    """AI-powered lottery predictor using Gemini 2.5 Pro"""
    
    def __init__(self):
        self.client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))
        self.connection_string = os.environ.get("DATABASE_URL")
    
    def get_game_data(self, game_type: str, limit: int = 50) -> Dict[str, Any]:
        """Get historical data for specific game type"""
        with psycopg2.connect(self.connection_string) as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT draw_number, draw_date, main_numbers, bonus_numbers, divisions
                    FROM lottery_results 
                    WHERE lottery_type = %s 
                    ORDER BY draw_date DESC 
                    LIMIT %s
                """, (game_type, limit))
                
                results = cur.fetchall()
                
                # Process data for AI analysis
                draws = []
                for draw_num, date, main_nums, bonus_nums, divisions in results:
                    try:
                        # Parse numbers
                        if isinstance(main_nums, str):
                            main_numbers = json.loads(main_nums)
                        else:
                            main_numbers = main_nums
                        
                        if bonus_nums and isinstance(bonus_nums, str):
                            bonus_numbers = json.loads(bonus_nums)
                        else:
                            bonus_numbers = bonus_nums or []
                        
                        draws.append({
                            'draw': draw_num,
                            'date': date.strftime('%Y-%m-%d'),
                            'main': sorted(main_numbers) if main_numbers else [],
                            'bonus': sorted(bonus_numbers) if bonus_numbers else [],
                            'divisions': divisions
                        })
                    except Exception as e:
                        logger.warning(f"Error processing draw {draw_num}: {e}")
                        continue
                
                return {
                    'game_type': game_type,
                    'total_draws': len(draws),
                    'draws': draws
                }
    
    def analyze_with_gemini(self, game_data: Dict[str, Any]) -> Dict[str, Any]:
        """Use Gemini to analyze game data and generate predictions"""
        
        game_type = game_data['game_type']
        draws = game_data['draws']
        
        # Prepare data summary for AI
        analysis_prompt = f"""
You are an expert lottery analyst using advanced statistical methods. Analyze the following {game_type} lottery data and generate intelligent number predictions.

GAME: {game_type}
RECENT DRAWS ({len(draws)} draws):

"""
        
        for i, draw in enumerate(draws[:20]):  # Show recent 20 draws
            analysis_prompt += f"Draw {draw['draw']} ({draw['date']}): Main {draw['main']}"
            if draw['bonus']:
                analysis_prompt += f", Bonus {draw['bonus']}"
            analysis_prompt += "\n"
        
        # Add statistical analysis request
        analysis_prompt += f"""

ANALYSIS REQUIREMENTS:
1. Identify number frequency patterns and hot/cold numbers
2. Analyze number gap patterns and consecutive occurrences
3. Examine bonus number patterns (if applicable)
4. Look for mathematical sequences or relationships
5. Consider date-based patterns and cyclical behaviors
6. Generate 1 set of predicted numbers with confidence score

GAME RULES:
- {game_type}: Generate appropriate number of main numbers and bonus numbers based on game type
- LOTTO: 6 main numbers (1-52)
- LOTTO PLUS 1/2: 6 main numbers (1-52) 
- POWERBALL: 5 main numbers (1-50) + 1 bonus (1-20)
- POWERBALL PLUS: 5 main numbers (1-50) + 1 bonus (1-20)
- DAILY LOTTO: 5 main numbers (1-36)

RESPONSE FORMAT (JSON only):
{{
    "predicted_numbers": [list of main numbers],
    "bonus_numbers": [list of bonus numbers if applicable],
    "confidence_score": float between 0.1 and 0.9,
    "reasoning": "detailed analysis explanation",
    "method": "statistical analysis method used"
}}
"""
        
        try:
            response = self.client.models.generate_content(
                model="gemini-2.5-pro",
                contents=analysis_prompt,
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    temperature=0.7
                )
            )
            
            if response.text:
                result = json.loads(response.text)
                logger.info(f"Generated prediction for {game_type}: {result['predicted_numbers']}")
                return result
            else:
                raise ValueError("Empty response from Gemini")
                
        except Exception as e:
            logger.error(f"Error generating prediction for {game_type}: {e}")
            return None
    
    def save_prediction(self, game_type: str, prediction: Dict[str, Any]):
        """Save prediction to database"""
        with psycopg2.connect(self.connection_string) as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO lottery_predictions 
                    (game_type, predicted_numbers, bonus_numbers, confidence_score, 
                     reasoning, prediction_method, target_draw_date, created_at, validation_status)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                """, (
                    game_type,
                    prediction['predicted_numbers'],
                    prediction.get('bonus_numbers', []),
                    prediction['confidence_score'],
                    prediction['reasoning'],
                    prediction.get('method', 'Gemini AI Analysis'),
                    datetime.now().date() + timedelta(days=7),  # Next week's draw
                    datetime.now(),
                    'pending'
                ))
                conn.commit()
                logger.info(f"Saved prediction for {game_type}")
    
    def generate_all_predictions(self):
        """Generate predictions for all game types"""
        game_types = [
            'LOTTO',
            'LOTTO PLUS 1', 
            'LOTTO PLUS 2',
            'POWERBALL',
            'POWERBALL PLUS',
            'DAILY LOTTO'
        ]
        
        successful_predictions = 0
        
        for game_type in game_types:
            logger.info(f"Generating prediction for {game_type}...")
            
            try:
                # Get historical data
                game_data = self.get_game_data(game_type)
                
                if not game_data['draws']:
                    logger.warning(f"No data available for {game_type}")
                    continue
                
                # Generate AI prediction
                prediction = self.analyze_with_gemini(game_data)
                
                if prediction:
                    # Save to database
                    self.save_prediction(game_type, prediction)
                    successful_predictions += 1
                    
                    # Brief pause between API calls
                    import time
                    time.sleep(2)
                else:
                    logger.error(f"Failed to generate prediction for {game_type}")
                    
            except Exception as e:
                logger.error(f"Error processing {game_type}: {e}")
                continue
        
        logger.info(f"Successfully generated {successful_predictions} predictions")
        return successful_predictions

def main():
    predictor = GeminiLotteryPredictor()
    return predictor.generate_all_predictions()

if __name__ == "__main__":
    main()