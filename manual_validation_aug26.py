#!/usr/bin/env python3
"""
Manual validation and prediction generation for August 26, 2025 results.
"""

import os
import sys
import logging
from datetime import datetime, date, timedelta
import psycopg2
from psycopg2.extras import RealDictCursor

# Add the current directory to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from ai_lottery_predictor import SmartLotteryPredictor

def setup_logging():
    """Setup logging for the validation process."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('manual_validation_aug26.log'),
            logging.StreamHandler()
        ]
    )

def connect_database():
    """Connect to the database."""
    return psycopg2.connect(
        os.environ.get("DATABASE_URL"),
        cursor_factory=RealDictCursor
    )

def validate_and_generate_predictions():
    """Validate existing predictions and generate new ones for the August 26 results."""
    logger = logging.getLogger(__name__)
    
    # August 26, 2025 new results
    new_results = [
        {
            'game_type': 'POWERBALL',
            'draw_number': 1645,
            'draw_date': date(2025, 8, 26),
            'main_numbers': [13, 19, 24, 44, 50],
            'bonus_numbers': [15]
        },
        {
            'game_type': 'POWERBALL PLUS', 
            'draw_number': 1645,
            'draw_date': date(2025, 8, 26),
            'main_numbers': [3, 5, 24, 32, 47],
            'bonus_numbers': [17]
        },
        {
            'game_type': 'DAILY LOTTO',
            'draw_number': 2356,
            'draw_date': date(2025, 8, 26),
            'main_numbers': [7, 10, 15, 27, 36],
            'bonus_numbers': []
        }
    ]
    
    conn = connect_database()
    cur = conn.cursor()
    
    predictions_validated = 0
    new_predictions_generated = 0
    
    try:
        # Check for predictions to validate against these new results
        for result in new_results:
            logger.info(f"Processing {result['game_type']} Draw {result['draw_number']} ({result['draw_date']})")
            
            # Look for predictions targeting this date
            cur.execute("""
                SELECT * FROM lottery_predictions 
                WHERE game_type = %s 
                AND target_draw_date = %s 
                AND validation_status = 'pending'
            """, (result['game_type'], result['draw_date']))
            
            predictions = cur.fetchall()
            logger.info(f"Found {len(predictions)} pending predictions for {result['game_type']}")
            
            for prediction in predictions:
                logger.info(f"Validating prediction {prediction['id']} for {result['game_type']}")
                
                # Calculate accuracy
                predicted_main = list(prediction['predicted_numbers'])
                actual_main = result['main_numbers']
                predicted_bonus = list(prediction['bonus_numbers']) if prediction['bonus_numbers'] else []
                actual_bonus = result['bonus_numbers']
                
                # Count matches
                main_matches = len(set(predicted_main) & set(actual_main))
                bonus_matches = len(set(predicted_bonus) & set(actual_bonus)) if actual_bonus else 0
                
                # Calculate accuracy percentage
                total_predicted = len(predicted_main) + len(predicted_bonus)
                total_matches = main_matches + bonus_matches
                accuracy = (total_matches / total_predicted * 100) if total_predicted > 0 else 0
                
                # Determine prize tier
                prize_tier = "No Prize"
                if result['game_type'] in ['POWERBALL', 'POWERBALL PLUS']:
                    if main_matches == 5 and bonus_matches == 1:
                        prize_tier = "Division 1"
                    elif main_matches == 5:
                        prize_tier = "Division 2"
                    elif main_matches == 4 and bonus_matches == 1:
                        prize_tier = "Division 3"
                    elif main_matches == 4:
                        prize_tier = "Division 4"
                    elif main_matches == 3 and bonus_matches == 1:
                        prize_tier = "Division 5"
                    elif main_matches == 3:
                        prize_tier = "Division 6"
                    elif main_matches == 2 and bonus_matches == 1:
                        prize_tier = "Division 7"
                    elif bonus_matches == 1:
                        prize_tier = "Division 8"
                elif result['game_type'] == 'DAILY LOTTO':
                    if main_matches == 5:
                        prize_tier = "Division 1"
                    elif main_matches == 4:
                        prize_tier = "Division 2"
                    elif main_matches == 3:
                        prize_tier = "Division 3"
                else:  # LOTTO games
                    if main_matches == 6 and bonus_matches == 1:
                        prize_tier = "Division 1"
                    elif main_matches == 6:
                        prize_tier = "Division 2"
                    elif main_matches == 5 and bonus_matches == 1:
                        prize_tier = "Division 3"
                    elif main_matches == 5:
                        prize_tier = "Division 4"
                    elif main_matches == 4 and bonus_matches == 1:
                        prize_tier = "Division 5"
                    elif main_matches == 4:
                        prize_tier = "Division 6"
                    elif main_matches == 3 and bonus_matches == 1:
                        prize_tier = "Division 7"
                    elif main_matches == 3:
                        prize_tier = "Division 8"
                
                # Update prediction with validation results
                cur.execute("""
                    UPDATE lottery_predictions SET
                        validation_status = 'validated',
                        is_verified = true,
                        verified_at = %s,
                        verified_draw_number = %s,
                        main_number_matches = %s,
                        bonus_number_matches = %s,
                        accuracy_percentage = %s,
                        prize_tier = %s,
                        matched_main_numbers = %s,
                        matched_bonus_numbers = %s
                    WHERE id = %s
                """, (
                    datetime.now(), result['draw_number'], main_matches, bonus_matches,
                    round(accuracy, 2), prize_tier, 
                    list(set(predicted_main) & set(actual_main)),
                    list(set(predicted_bonus) & set(actual_bonus)),
                    prediction['id']
                ))
                
                logger.info(f"✅ Validated prediction {prediction['id']}: {accuracy:.1f}% accuracy, {prize_tier}")
                predictions_validated += 1
            
            # Generate new prediction for next draw
            logger.info(f"Generating new prediction for next {result['game_type']} draw...")
            
            try:
                predictor = SmartLotteryPredictor()
                
                # Calculate next target date
                if result['game_type'] == 'DAILY LOTTO':
                    next_target = result['draw_date'] + timedelta(days=1)
                elif result['game_type'] in ['POWERBALL', 'POWERBALL PLUS']:
                    # PowerBall draws on Tuesday and Friday
                    days_ahead = 2 if result['draw_date'].weekday() == 1 else 4  # Tuesday=1, Friday=4
                    next_target = result['draw_date'] + timedelta(days=days_ahead)
                else:  # LOTTO games
                    # LOTTO draws on Wednesday and Saturday
                    days_ahead = 3 if result['draw_date'].weekday() == 2 else 4  # Wednesday=2, Saturday=5
                    next_target = result['draw_date'] + timedelta(days=days_ahead)
                
                prediction_data = predictor.generate_prediction(result['game_type'], str(next_target))
                
                if prediction_data:
                    logger.info(f"✅ Generated new {result['game_type']} prediction for {next_target}")
                    logger.info(f"Numbers: {prediction_data['predicted_numbers']}")
                    logger.info(f"Confidence: {prediction_data['confidence_score']}%")
                    new_predictions_generated += 1
                else:
                    logger.warning(f"❌ Failed to generate prediction for {result['game_type']}")
                    
            except Exception as e:
                logger.error(f"Error generating prediction for {result['game_type']}: {e}")
        
        conn.commit()
        
    except Exception as e:
        logger.error(f"Database error: {e}")
        conn.rollback()
        raise
    finally:
        cur.close()
        conn.close()
    
    return predictions_validated, new_predictions_generated

def main():
    """Main function."""
    setup_logging()
    logger = logging.getLogger(__name__)
    
    logger.info("=== MANUAL VALIDATION FOR AUGUST 26, 2025 ===")
    
    try:
        validated, generated = validate_and_generate_predictions()
        logger.info(f"=== VALIDATION COMPLETE ===")
        logger.info(f"Predictions validated: {validated}")
        logger.info(f"New predictions generated: {generated}")
        return True
    except Exception as e:
        logger.error(f"Validation failed: {e}")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)