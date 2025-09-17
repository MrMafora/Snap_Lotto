#!/usr/bin/env python3
"""
Prediction Validation System - Validates existing predictions against actual draw results
This module provides the validation interface expected by the automation workflow
"""

import os
import logging
from typing import Dict, List, Any
from ai_lottery_predictor import AILotteryPredictor

logger = logging.getLogger(__name__)

class PredictionValidationSystem:
    """Main validation system for lottery predictions"""
    
    def __init__(self):
        """Initialize the validation system"""
        self.predictor = AILotteryPredictor()
        logger.info("PredictionValidationSystem initialized")
    
    def validate_all_pending_predictions(self) -> Dict[str, Any]:
        """
        Validate all pending predictions against actual draw results
        Returns a dictionary with validation results
        """
        try:
            logger.info("Starting validation of all pending predictions")
            
            # Use the existing validation functionality from AILotteryPredictor
            # This will check predictions against actual results and update their status
            validated_predictions = []
            
            # Get all pending predictions from the database
            import psycopg2
            conn = psycopg2.connect(os.environ.get('DATABASE_URL'))
            cur = conn.cursor()
            
            try:
                # Find predictions that need validation (have matching draw results)
                cur.execute("""
                    SELECT lp.id, lp.game_type, lp.predicted_numbers, lp.bonus_numbers, lp.linked_draw_id,
                           lr.main_numbers, lr.bonus_numbers
                    FROM lottery_predictions lp
                    JOIN lottery_results lr ON (lr.lottery_type = lp.game_type AND lr.draw_number = lp.linked_draw_id)
                    WHERE lp.validation_status != 'validated'
                       OR lp.validation_status IS NULL
                    ORDER BY lp.created_at DESC
                    LIMIT 100
                """)
                
                pending_validations = cur.fetchall()
                logger.info(f"Found {len(pending_validations)} predictions needing validation")
                
                for prediction_data in pending_validations:
                    try:
                        prediction_id, game_type, predicted_nums, predicted_bonus, linked_draw, actual_nums, actual_bonus = prediction_data
                        
                        # Parse the actual numbers
                        import json
                        if isinstance(actual_nums, str):
                            actual_numbers = json.loads(actual_nums)
                        elif isinstance(actual_nums, list):
                            actual_numbers = actual_nums
                        else:
                            continue
                            
                        # Parse actual bonus numbers
                        actual_bonus_list = []
                        if actual_bonus:
                            if isinstance(actual_bonus, str):
                                actual_bonus_list = json.loads(actual_bonus)
                            elif isinstance(actual_bonus, list):
                                actual_bonus_list = actual_bonus
                        
                        # Use the existing validation method
                        validation_result = self.predictor.validate_prediction_against_draw(
                            prediction_id, actual_numbers, actual_bonus_list
                        )
                        
                        if validation_result.get('success', False):
                            validated_predictions.append({
                                'prediction_id': prediction_id,
                                'game_type': game_type,
                                'matches': validation_result.get('total_matches', 0),
                                'accuracy': validation_result.get('accuracy_percentage', 0),
                                'prize_tier': validation_result.get('prize_tier', 'No Win')
                            })
                            logger.info(f"✅ Validated prediction {prediction_id} for {game_type}: {validation_result.get('total_matches', 0)} matches")
                        
                    except Exception as pred_error:
                        logger.warning(f"Failed to validate prediction {prediction_id}: {pred_error}")
                        continue
                
            finally:
                cur.close()
                conn.close()
            
            result = {
                'success': True,
                'validated_predictions': validated_predictions,
                'total_validated': len(validated_predictions),
                'message': f'Successfully validated {len(validated_predictions)} predictions'
            }
            
            logger.info(f"Validation complete: {len(validated_predictions)} predictions validated")
            return result
            
        except Exception as e:
            logger.error(f"Error in validate_all_pending_predictions: {e}")
            return {
                'success': False,
                'validated_predictions': [],
                'total_validated': 0,
                'error': str(e),
                'message': f'Validation failed: {str(e)}'
            }

class PredictionValidator:
    """Legacy validator class for backward compatibility"""
    
    def __init__(self):
        self.validation_system = PredictionValidationSystem()
    
    def validate_all_pending_predictions(self):
        """Legacy method that wraps the new validation system"""
        return self.validation_system.validate_all_pending_predictions()

# Export both classes for compatibility
__all__ = ['PredictionValidationSystem', 'PredictionValidator']