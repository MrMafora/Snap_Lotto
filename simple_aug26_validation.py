#!/usr/bin/env python3
"""
Simple validation for August 26, 2025 results.
"""

import os
import sys
import logging
import psycopg2
from psycopg2.extras import RealDictCursor
from datetime import datetime, date, timedelta

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
    
    logger.info("=== VALIDATING AUGUST 26 PREDICTIONS ===")
    
    # August 26, 2025 new results
    new_results = {
        'DAILY LOTTO': {
            'draw_number': 2356,
            'actual_numbers': [7, 10, 15, 27, 36]
        }
    }
    
    conn = connect_database()
    cur = conn.cursor()
    
    try:
        # Find pending prediction for Daily Lotto on Aug 26
        cur.execute("""
            SELECT * FROM lottery_predictions 
            WHERE game_type = 'DAILY LOTTO' 
            AND target_draw_date = %s 
            AND validation_status = 'pending'
        """, (date(2025, 8, 26),))
        
        prediction = cur.fetchone()
        
        if not prediction:
            logger.info("❌ No pending Daily Lotto prediction found for Aug 26")
            return
        
        logger.info(f"✅ Found prediction ID {prediction['id']} for Daily Lotto")
        logger.info(f"Predicted: {list(prediction['predicted_numbers'])}")
        logger.info(f"Actual: {new_results['DAILY LOTTO']['actual_numbers']}")
        
        # Calculate matches
        predicted = list(prediction['predicted_numbers'])
        actual = new_results['DAILY LOTTO']['actual_numbers']
        
        matches = set(predicted) & set(actual)
        match_count = len(matches)
        accuracy = (match_count / len(predicted)) * 100
        
        # Determine prize tier
        prize_tier = "No Prize"
        if match_count == 5:
            prize_tier = "Division 1"
        elif match_count == 4:
            prize_tier = "Division 2"
        elif match_count == 3:
            prize_tier = "Division 3"
        
        logger.info(f"Matches: {match_count}/5 ({list(matches)})")
        logger.info(f"Accuracy: {accuracy:.1f}%")
        logger.info(f"Prize Tier: {prize_tier}")
        
        # Update prediction
        cur.execute("""
            UPDATE lottery_predictions SET
                validation_status = 'validated',
                is_verified = true,
                verified_at = %s,
                verified_draw_number = %s,
                main_number_matches = %s,
                accuracy_percentage = %s,
                prize_tier = %s,
                matched_main_numbers = %s
            WHERE id = %s
        """, (
            datetime.now(),
            new_results['DAILY LOTTO']['draw_number'],
            match_count,
            round(accuracy, 2),
            prize_tier,
            list(matches),
            prediction['id']
        ))
        
        conn.commit()
        logger.info(f"✅ Prediction {prediction['id']} validated successfully!")
        
    except Exception as e:
        logger.error(f"Error: {e}")
        conn.rollback()
    finally:
        cur.close()
        conn.close()

if __name__ == "__main__":
    main()