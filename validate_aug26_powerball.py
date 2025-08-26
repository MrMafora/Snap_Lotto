#!/usr/bin/env python3
"""
Create validation data for August 26, 2025 Powerball results.
"""

import os
import sys
import logging
import psycopg2
from psycopg2.extras import RealDictCursor
from datetime import datetime, date

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

def main():
    setup_logging()
    logger = logging.getLogger(__name__)
    
    logger.info("=== CREATING VALIDATION DATA FOR AUG 26 POWERBALL RESULTS ===")
    
    # August 26, 2025 new results from our database
    new_results = {
        'POWERBALL': {
            'draw_number': 1645,
            'actual_numbers': [13, 19, 24, 44, 50],
            'actual_bonus': [15]
        },
        'POWERBALL PLUS': {
            'draw_number': 1645,
            'actual_numbers': [3, 5, 24, 32, 47],
            'actual_bonus': [17]
        }
    }
    
    conn = connect_database()
    cur = conn.cursor()
    
    try:
        # Check for existing predictions for Powerball games
        for game_type, result_data in new_results.items():
            logger.info(f"\n--- Processing {game_type} ---")
            
            # Find prediction for this game type for Aug 29 (next draw)
            cur.execute("""
                SELECT * FROM lottery_predictions 
                WHERE game_type = %s 
                AND target_draw_date = %s 
                AND validation_status = 'pending'
                ORDER BY created_at DESC
                LIMIT 1
            """, (game_type, date(2025, 8, 29)))
            
            prediction = cur.fetchone()
            
            if not prediction:
                logger.info(f"No pending prediction found for {game_type} on Aug 29")
                continue
            
            logger.info(f"✅ Found prediction ID {prediction['id']} for {game_type}")
            logger.info(f"Predicted: {list(prediction['predicted_numbers'])} + {list(prediction['bonus_numbers']) if prediction['bonus_numbers'] else []}")
            logger.info(f"Actual: {result_data['actual_numbers']} + {result_data['actual_bonus']}")
            
            # Calculate matches
            predicted_main = list(prediction['predicted_numbers'])
            predicted_bonus = list(prediction['bonus_numbers']) if prediction['bonus_numbers'] else []
            
            actual_main = result_data['actual_numbers']
            actual_bonus = result_data['actual_bonus']
            
            main_matches = set(predicted_main) & set(actual_main)
            bonus_matches = set(predicted_bonus) & set(actual_bonus)
            
            main_match_count = len(main_matches)
            bonus_match_count = len(bonus_matches)
            
            # Calculate accuracy based on main numbers only for Powerball
            accuracy = (main_match_count / len(predicted_main)) * 100 if predicted_main else 0
            
            # Determine prize tier for Powerball
            prize_tier = "No Prize"
            if main_match_count == 5 and bonus_match_count == 1:
                prize_tier = "Division 1"
            elif main_match_count == 5:
                prize_tier = "Division 2"
            elif main_match_count == 4 and bonus_match_count == 1:
                prize_tier = "Division 3"
            elif main_match_count == 4:
                prize_tier = "Division 4"
            elif main_match_count == 3 and bonus_match_count == 1:
                prize_tier = "Division 5"
            elif main_match_count == 3:
                prize_tier = "Division 6"
            elif main_match_count == 2 and bonus_match_count == 1:
                prize_tier = "Division 7"
            elif (main_match_count == 1 and bonus_match_count == 1) or bonus_match_count == 1:
                prize_tier = "Division 8"
            
            logger.info(f"Main matches: {main_match_count}/5 ({list(main_matches)})")
            logger.info(f"Bonus matches: {bonus_match_count}/1 ({list(bonus_matches)})")
            logger.info(f"Accuracy: {accuracy:.1f}%")
            logger.info(f"Prize Tier: {prize_tier}")
            
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
                datetime.now(),
                result_data['draw_number'],
                main_match_count,
                bonus_match_count,
                round(accuracy, 2),
                prize_tier,
                list(main_matches),
                list(bonus_matches),
                prediction['id']
            ))
            
            conn.commit()
            logger.info(f"✅ Prediction {prediction['id']} validated successfully!")
        
        logger.info(f"\n=== VALIDATION COMPLETE ===")
        
    except Exception as e:
        logger.error(f"Error: {e}")
        conn.rollback()
    finally:
        cur.close()
        conn.close()

if __name__ == "__main__":
    main()