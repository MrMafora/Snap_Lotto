#!/usr/bin/env python3
"""
Validate all predictions against actual results to ensure accuracy
"""

import os
import logging
import psycopg2
from psycopg2.extras import RealDictCursor
import json

def setup_logging():
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )

def connect_database():
    return psycopg2.connect(
        os.environ.get("DATABASE_URL"),
        cursor_factory=RealDictCursor
    )

def calculate_matches(predicted_main, predicted_bonus, actual_main, actual_bonus):
    """Calculate exact matches between predicted and actual numbers"""
    
    # Convert string arrays to Python lists if needed
    if isinstance(predicted_main, str):
        predicted_main = json.loads(predicted_main.replace('{', '[').replace('}', ']'))
    if isinstance(actual_main, str):
        actual_main = json.loads(actual_main)
    
    # Calculate main number matches
    main_matches = [num for num in predicted_main if num in actual_main]
    main_count = len(main_matches)
    
    # Calculate bonus number matches
    bonus_matches = []
    bonus_count = 0
    
    if predicted_bonus and actual_bonus:
        if isinstance(predicted_bonus, str):
            predicted_bonus = json.loads(predicted_bonus.replace('{', '[').replace('}', ']'))
        if isinstance(actual_bonus, str):
            actual_bonus = json.loads(actual_bonus)
        
        bonus_matches = [num for num in predicted_bonus if num in actual_bonus]
        bonus_count = len(bonus_matches)
    
    return main_matches, bonus_matches, main_count, bonus_count

def calculate_accuracy(game_type, main_count, bonus_count):
    """Calculate accuracy percentage based on game type"""
    
    if game_type == 'DAILY LOTTO':
        # 5 main numbers total
        return (main_count / 5.0) * 100
    elif game_type in ['LOTTO', 'LOTTO PLUS 1', 'LOTTO PLUS 2']:
        # 6 main numbers total
        return (main_count / 6.0) * 100
    elif game_type in ['POWERBALL', 'POWERBALL PLUS']:
        # 5 main + 1 bonus = 6 total numbers
        total_matches = main_count + bonus_count
        return (total_matches / 6.0) * 100
    
    return 0.0

def main():
    setup_logging()
    logger = logging.getLogger(__name__)
    
    logger.info("=== VALIDATING ALL PREDICTIONS ===")
    
    conn = connect_database()
    cur = conn.cursor()
    
    try:
        # Get all validated predictions with their corresponding results
        cur.execute("""
            SELECT 
                p.id,
                p.game_type,
                p.predicted_numbers,
                p.bonus_numbers,
                p.target_draw_date,
                p.verified_draw_number,
                p.matched_main_numbers,
                p.matched_bonus_numbers,
                p.main_number_matches,
                p.bonus_number_matches,
                p.accuracy_percentage,
                r.main_numbers as actual_main_numbers,
                r.bonus_numbers as actual_bonus_numbers
            FROM lottery_predictions p
            JOIN lottery_results r ON (
                (p.verified_draw_number = r.draw_number AND p.game_type = r.lottery_type)
                OR 
                (p.target_draw_date = r.draw_date AND p.game_type = r.lottery_type)
            )
            WHERE p.validation_status = 'validated'
            ORDER BY p.game_type, p.target_draw_date
        """)
        
        predictions = cur.fetchall()
        logger.info(f"Found {len(predictions)} validated predictions to verify")
        
        corrections_needed = 0
        
        for pred in predictions:
            logger.info(f"\n--- {pred['game_type']} (ID: {pred['id']}) ---")
            logger.info(f"Draw: {pred['verified_draw_number']} | Date: {pred['target_draw_date']}")
            logger.info(f"Predicted Main: {pred['predicted_numbers']}")
            logger.info(f"Predicted Bonus: {pred['bonus_numbers']}")
            logger.info(f"Actual Main: {pred['actual_main_numbers']}")
            logger.info(f"Actual Bonus: {pred['actual_bonus_numbers']}")
            
            # Calculate correct matches
            main_matches, bonus_matches, main_count, bonus_count = calculate_matches(
                pred['predicted_numbers'], 
                pred['bonus_numbers'],
                pred['actual_main_numbers'],
                pred['actual_bonus_numbers']
            )
            
            # Calculate correct accuracy
            correct_accuracy = calculate_accuracy(pred['game_type'], main_count, bonus_count)
            
            logger.info(f"CALCULATED - Main Matches: {main_matches} ({main_count})")
            logger.info(f"CALCULATED - Bonus Matches: {bonus_matches} ({bonus_count})")
            logger.info(f"CALCULATED - Accuracy: {correct_accuracy:.2f}%")
            
            logger.info(f"STORED - Main Matches: {pred['matched_main_numbers']} ({pred['main_number_matches']})")
            logger.info(f"STORED - Bonus Matches: {pred['matched_bonus_numbers']} ({pred['bonus_number_matches']})")
            logger.info(f"STORED - Accuracy: {pred['accuracy_percentage']}%")
            
            # Check if correction is needed
            needs_correction = (
                main_count != pred['main_number_matches'] or
                bonus_count != (pred['bonus_number_matches'] or 0) or
                abs(correct_accuracy - float(pred['accuracy_percentage'])) > 0.01
            )
            
            if needs_correction:
                logger.warning("❌ CORRECTION NEEDED!")
                corrections_needed += 1
                
                # Update the prediction with correct values
                cur.execute("""
                    UPDATE lottery_predictions
                    SET 
                        matched_main_numbers = %s,
                        matched_bonus_numbers = %s,
                        main_number_matches = %s,
                        bonus_number_matches = %s,
                        accuracy_percentage = %s
                    WHERE id = %s
                """, (
                    main_matches,
                    bonus_matches if bonus_matches else None,
                    main_count,
                    bonus_count if bonus_count > 0 else None,
                    correct_accuracy,
                    pred['id']
                ))
                
                logger.info("✅ Correction applied to database")
            else:
                logger.info("✅ Validation data is correct")
        
        if corrections_needed > 0:
            conn.commit()
            logger.info(f"\n=== VALIDATION COMPLETE ===")
            logger.info(f"Applied corrections to {corrections_needed} predictions")
        else:
            logger.info(f"\n=== VALIDATION COMPLETE ===")
            logger.info("All predictions have accurate validation data")
        
    except Exception as e:
        logger.error(f"Error: {e}")
        conn.rollback()
        import traceback
        traceback.print_exc()
    finally:
        cur.close()
        conn.close()

if __name__ == "__main__":
    main()