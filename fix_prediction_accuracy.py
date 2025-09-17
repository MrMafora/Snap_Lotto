#!/usr/bin/env python3
"""
Comprehensive Prediction Accuracy Fix
Re-validates all predictions against actual results to fix accuracy issues
"""

import os
import json
import logging
import psycopg2
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def calculate_matches(predicted_numbers, actual_numbers, predicted_bonus=None, actual_bonus=None):
    """Calculate matches between predicted and actual numbers"""
    try:
        # Ensure both are lists of integers
        if isinstance(predicted_numbers, str):
            predicted_numbers = json.loads(predicted_numbers)
        if isinstance(actual_numbers, str):
            actual_numbers = json.loads(actual_numbers)
            
        # Convert to sets of integers for comparison
        pred_set = set(int(x) for x in predicted_numbers)
        actual_set = set(int(x) for x in actual_numbers)
        
        # Calculate main matches
        main_matches = len(pred_set & actual_set)
        matched_main = list(pred_set & actual_set)
        
        # Calculate bonus matches
        bonus_matches = 0
        matched_bonus = []
        
        if predicted_bonus and actual_bonus:
            if isinstance(predicted_bonus, str):
                predicted_bonus = json.loads(predicted_bonus)
            if isinstance(actual_bonus, str):
                actual_bonus = json.loads(actual_bonus)
                
            pred_bonus_set = set(int(x) for x in predicted_bonus)
            actual_bonus_set = set(int(x) for x in actual_bonus)
            
            bonus_matches = len(pred_bonus_set & actual_bonus_set)
            matched_bonus = list(pred_bonus_set & actual_bonus_set)
        
        # Calculate accuracy percentage
        total_predicted = len(predicted_numbers)
        accuracy_percentage = (main_matches / total_predicted) * 100 if total_predicted > 0 else 0
        
        # Determine prize tier (simplified)
        if main_matches >= 3:
            if bonus_matches > 0:
                prize_tier = f"{main_matches}+{bonus_matches} Match"
            else:
                prize_tier = f"{main_matches} Match"
        elif main_matches >= 2:
            prize_tier = f"{main_matches} Match"
        elif main_matches == 1:
            prize_tier = "1 Match"
        else:
            prize_tier = "No Prize"
        
        return {
            'main_matches': main_matches,
            'bonus_matches': bonus_matches,
            'accuracy_percentage': accuracy_percentage,
            'prize_tier': prize_tier,
            'matched_main': matched_main,
            'matched_bonus': matched_bonus
        }
        
    except Exception as e:
        logger.error(f"Error calculating matches: {e}")
        return {
            'main_matches': 0,
            'bonus_matches': 0,
            'accuracy_percentage': 0,
            'prize_tier': 'Error',
            'matched_main': [],
            'matched_bonus': []
        }

def fix_all_prediction_accuracy():
    """Fix accuracy for all validated predictions"""
    try:
        conn = psycopg2.connect(os.environ.get('DATABASE_URL'))
        cur = conn.cursor()
        
        # Find all predictions that have matching results
        cur.execute("""
            SELECT lp.id, lp.game_type, lp.predicted_numbers, lp.bonus_numbers, lp.linked_draw_id,
                   lr.main_numbers, lr.bonus_numbers
            FROM lottery_predictions lp
            JOIN lottery_results lr ON (lr.lottery_type = lp.game_type AND lr.draw_number = lp.linked_draw_id)
            WHERE lp.created_at >= CURRENT_DATE - INTERVAL '30 days'
            ORDER BY lp.created_at DESC
        """)
        
        predictions_to_fix = cur.fetchall()
        logger.info(f"Found {len(predictions_to_fix)} predictions to re-validate")
        
        fixed_count = 0
        
        for pred_data in predictions_to_fix:
            try:
                prediction_id, game_type, predicted_nums, predicted_bonus, linked_draw, actual_nums, actual_bonus = pred_data
                
                # Calculate correct matches
                result = calculate_matches(predicted_nums, actual_nums, predicted_bonus, actual_bonus)
                
                # Update the database with correct values
                cur.execute("""
                    UPDATE lottery_predictions 
                    SET main_number_matches = %s,
                        bonus_number_matches = %s,
                        accuracy_percentage = %s,
                        prize_tier = %s,
                        matched_main_numbers = %s,
                        matched_bonus_numbers = %s,
                        validation_status = 'corrected',
                        verified_at = NOW()
                    WHERE id = %s
                """, (
                    result['main_matches'],
                    result['bonus_matches'], 
                    result['accuracy_percentage'],
                    result['prize_tier'],
                    result['matched_main'],
                    result['matched_bonus'],
                    prediction_id
                ))
                
                fixed_count += 1
                
                if result['main_matches'] > 0:
                    logger.info(f"✅ Fixed prediction {prediction_id} ({game_type} {linked_draw}): {result['main_matches']} main matches, {result['accuracy_percentage']:.1f}% accuracy")
                
            except Exception as pred_error:
                logger.warning(f"Failed to fix prediction {prediction_id}: {pred_error}")
                continue
        
        conn.commit()
        cur.close()
        conn.close()
        
        logger.info(f"🎯 Successfully fixed {fixed_count} predictions!")
        return fixed_count
        
    except Exception as e:
        logger.error(f"Error fixing predictions: {e}")
        return 0

if __name__ == "__main__":
    print("🔧 Running Comprehensive Prediction Accuracy Fix...")
    fixed = fix_all_prediction_accuracy()
    print(f"✅ Complete! Fixed {fixed} predictions with correct accuracy calculations.")