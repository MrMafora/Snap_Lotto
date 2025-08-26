#!/usr/bin/env python3
"""
Generate fresh predictions for all lottery games after August 26, 2025 results.
"""

import os
import sys
import logging
from datetime import date, timedelta

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
    
    logger.info("=== GENERATING FRESH PREDICTIONS AFTER AUG 26 RESULTS ===")
    
    # Calculate next target dates based on August 26, 2025 (Monday)
    predictions_to_generate = [
        # Daily Lotto draws every day
        ('DAILY LOTTO', date(2025, 8, 27)),  # Tuesday
        
        # PowerBall draws Tuesday and Friday - next is Friday
        ('POWERBALL', date(2025, 8, 29)),    # Friday
        ('POWERBALL PLUS', date(2025, 8, 29)),  # Friday
        
        # Lotto draws Wednesday and Saturday - next is Wednesday
        ('LOTTO', date(2025, 8, 27)),        # Wednesday
        ('LOTTO PLUS 1', date(2025, 8, 27)), # Wednesday
        ('LOTTO PLUS 2', date(2025, 8, 27)), # Wednesday
    ]
    
    try:
        predictor = AILotteryPredictor()
        
        successful_predictions = 0
        
        for game_type, target_date in predictions_to_generate:
            logger.info(f"Generating {game_type} prediction for {target_date}...")
            
            try:
                # Generate prediction using the AI predictor
                prediction = predictor.generate_single_prediction(game_type, target_date.strftime('%Y-%m-%d'))
                
                if prediction:
                    logger.info(f"✅ {game_type}: {prediction.predicted_numbers} + {prediction.bonus_numbers}")
                    logger.info(f"   Confidence: {prediction.confidence_score}%")
                    logger.info(f"   Method: {prediction.prediction_method}")
                    successful_predictions += 1
                else:
                    logger.warning(f"❌ Failed to generate {game_type} prediction")
                    
            except Exception as e:
                logger.error(f"Error generating {game_type} prediction: {e}")
        
        logger.info(f"=== GENERATION COMPLETE ===")
        logger.info(f"Successfully generated {successful_predictions}/{len(predictions_to_generate)} predictions")
        
        return successful_predictions > 0
        
    except Exception as e:
        logger.error(f"Prediction generation failed: {e}")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)