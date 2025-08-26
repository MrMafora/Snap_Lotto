#!/usr/bin/env python3
"""
Generate new predictions for all lottery games after August 26, 2025 results.
"""

import os
import sys
import logging

# Add current directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from ai_lottery_predictor import AILotteryPredictor

def setup_logging():
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )

def main():
    setup_logging()
    logger = logging.getLogger(__name__)
    
    logger.info("=== GENERATING NEW PREDICTIONS FOR ALL GAMES ===")
    
    # Games to generate predictions for
    games = ['DAILY LOTTO', 'LOTTO', 'LOTTO PLUS 1', 'LOTTO PLUS 2', 'POWERBALL', 'POWERBALL PLUS']
    
    try:
        predictor = AILotteryPredictor()
        
        successful_predictions = 0
        
        for game_type in games:
            logger.info(f"Generating {game_type} prediction...")
            
            try:
                # Use the correct method name
                prediction = predictor.generate_prediction(game_type)
                
                if prediction:
                    # Store prediction in database
                    stored = predictor.store_prediction_in_database(prediction)
                    
                    if stored:
                        logger.info(f"✅ {game_type}: {prediction.predicted_numbers} + {prediction.bonus_numbers}")
                        logger.info(f"   Confidence: {prediction.confidence_score}%")
                        logger.info(f"   Method: {prediction.prediction_method}")
                        successful_predictions += 1
                    else:
                        logger.warning(f"❌ Failed to store {game_type} prediction")
                else:
                    logger.warning(f"❌ Failed to generate {game_type} prediction")
                    
            except Exception as e:
                logger.error(f"Error with {game_type}: {e}")
        
        logger.info(f"=== PREDICTION GENERATION COMPLETE ===")
        logger.info(f"Successfully generated {successful_predictions}/{len(games)} predictions")
        
        return successful_predictions > 0
        
    except Exception as e:
        logger.error(f"Prediction generation failed: {e}")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)