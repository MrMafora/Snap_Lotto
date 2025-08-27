#!/usr/bin/env python3
"""
South African Lottery Prediction Validation System
Compares AI predictions against actual lottery results and calculates accuracy metrics.
"""

import os
import logging
import json
from datetime import datetime, timedelta
from typing import List, Dict, Tuple, Optional
import psycopg2
from psycopg2.extras import RealDictCursor

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class PredictionValidationSystem:
    def __init__(self):
        self.db_url = os.environ.get('DATABASE_URL')
        if not self.db_url:
            raise Exception("DATABASE_URL environment variable not set")
        
        self.conn = None
        self.connect_db()
        
    def connect_db(self):
        """Connect to PostgreSQL database"""
        try:
            self.conn = psycopg2.connect(self.db_url)
            logger.info("Database connection established")
        except Exception as e:
            logger.error(f"Database connection failed: {e}")
            raise
            
    def calculate_prediction_accuracy(self, predicted_numbers: List[int], actual_numbers: List[int], 
                                    predicted_bonus: List[int] = None, actual_bonus: List[int] = None) -> Dict:
        """
        Calculate detailed accuracy metrics for a prediction vs actual result
        """
        # Convert to sets for easier comparison
        pred_set = set(predicted_numbers)
        actual_set = set(actual_numbers)
        
        # Find matches
        matched_main = list(pred_set.intersection(actual_set))
        main_matches = len(matched_main)
        
        # Bonus number matches (for games like PowerBall)
        bonus_matches = 0
        matched_bonus = []
        if predicted_bonus and actual_bonus:
            pred_bonus_set = set(predicted_bonus)
            actual_bonus_set = set(actual_bonus)
            matched_bonus = list(pred_bonus_set.intersection(actual_bonus_set))
            bonus_matches = len(matched_bonus)
        
        # Calculate accuracy percentage
        total_possible_matches = len(actual_numbers)
        accuracy_percentage = (main_matches / total_possible_matches) * 100
        
        # Determine prize tier based on matches
        prize_tier = self.determine_prize_tier(main_matches, bonus_matches, len(actual_numbers))
        
        # Calculate overall accuracy score (0-100)
        if predicted_bonus and actual_bonus:
            # For bonus games, factor in bonus matches
            total_possible = len(actual_numbers) + len(actual_bonus)
            total_matches = main_matches + bonus_matches
            accuracy_score = (total_matches / total_possible) * 100
        else:
            accuracy_score = accuracy_percentage
            
        return {
            'main_number_matches': main_matches,
            'bonus_number_matches': bonus_matches,
            'matched_main_numbers': matched_main,
            'matched_bonus_numbers': matched_bonus,
            'accuracy_percentage': round(accuracy_percentage, 2),
            'accuracy_score': round(accuracy_score, 2),
            'prize_tier': prize_tier,
            'validation_status': 'validated'
        }
    
    def determine_prize_tier(self, main_matches: int, bonus_matches: int, total_main_numbers: int) -> str:
        """
        Determine prize tier based on number of matches
        """
        if total_main_numbers == 5:  # Daily Lotto
            if main_matches == 5:
                return "Division 1 (5 matches)"
            elif main_matches == 4:
                return "Division 2 (4 matches)"
            elif main_matches == 3:
                return "Division 3 (3 matches)"
            elif main_matches == 2:
                return "Division 4 (2 matches)"
            else:
                return "No Prize"
                
        elif total_main_numbers == 6:  # Lotto, Lotto Plus
            if main_matches == 6:
                return "Division 1 (6 matches)"
            elif main_matches == 5:
                return "Division 2 (5 matches)"
            elif main_matches == 4:
                return "Division 3 (4 matches)"
            elif main_matches == 3:
                return "Division 4 (3 matches)"
            else:
                return "No Prize"
                
        else:  # PowerBall (5 main + bonus)
            if main_matches == 5 and bonus_matches == 1:
                return "Division 1 (5+PB)"
            elif main_matches == 5:
                return "Division 2 (5)"
            elif main_matches == 4 and bonus_matches == 1:
                return "Division 3 (4+PB)"
            elif main_matches == 4:
                return "Division 4 (4)"
            elif main_matches == 3 and bonus_matches == 1:
                return "Division 5 (3+PB)"
            elif main_matches == 3:
                return "Division 6 (3)"
            elif main_matches == 2 and bonus_matches == 1:
                return "Division 7 (2+PB)"
            elif main_matches == 1 and bonus_matches == 1:
                return "Division 8 (1+PB)"
            elif bonus_matches == 1:
                return "Division 9 (PB only)"
            else:
                return "No Prize"
    
    def validate_prediction_against_result(self, prediction_id: int, lottery_result_id: int = None, 
                                         draw_number: int = None, game_type: str = None) -> Dict:
        """
        Validate a specific prediction against lottery result
        """
        try:
            with self.conn.cursor(cursor_factory=RealDictCursor) as cursor:
                # Get prediction details
                cursor.execute("""
                    SELECT * FROM lottery_predictions 
                    WHERE id = %s
                """, (prediction_id,))
                
                prediction = cursor.fetchone()
                if not prediction:
                    return {'error': f'Prediction {prediction_id} not found'}
                
                # Find matching lottery result
                if lottery_result_id:
                    cursor.execute("""
                        SELECT * FROM lottery_results 
                        WHERE id = %s
                    """, (lottery_result_id,))
                elif draw_number and game_type:
                    # Map game type to lottery type
                    lottery_type_map = {
                        'DAILY LOTTO': 'DAILY LOTTO',
                        'LOTTO': 'LOTTO',
                        'LOTTO PLUS 1': 'LOTTO PLUS 1',
                        'LOTTO PLUS 2': 'LOTTO PLUS 2',
                        'POWERBALL': 'POWERBALL',
                        'POWERBALL PLUS': 'POWERBALL PLUS'
                    }
                    
                    cursor.execute("""
                        SELECT * FROM lottery_results 
                        WHERE draw_number = %s AND lottery_type = %s
                        ORDER BY created_at DESC LIMIT 1
                    """, (draw_number, lottery_type_map.get(game_type, game_type)))
                else:
                    return {'error': 'Either lottery_result_id or draw_number+game_type must be provided'}
                
                result = cursor.fetchone()
                if not result:
                    return {'error': 'No matching lottery result found'}
                
                # Parse numbers from database
                predicted_main = list(prediction['predicted_numbers'])
                actual_main = json.loads(result['main_numbers']) if isinstance(result['main_numbers'], str) else list(result['main_numbers'])
                
                predicted_bonus = list(prediction['bonus_numbers']) if prediction['bonus_numbers'] else []
                actual_bonus = json.loads(result['bonus_numbers']) if result['bonus_numbers'] and isinstance(result['bonus_numbers'], str) else (list(result['bonus_numbers']) if result['bonus_numbers'] else [])
                
                # Calculate accuracy
                accuracy_data = self.calculate_prediction_accuracy(
                    predicted_main, actual_main, predicted_bonus, actual_bonus
                )
                
                # Update prediction record with validation results
                cursor.execute("""
                    UPDATE lottery_predictions 
                    SET is_verified = true,
                        verified_at = %s,
                        main_number_matches = %s,
                        bonus_number_matches = %s,
                        matched_main_numbers = %s,
                        matched_bonus_numbers = %s,
                        accuracy_percentage = %s,
                        accuracy_score = %s,
                        prize_tier = %s,
                        validation_status = %s
                    WHERE id = %s
                """, (
                    datetime.now(),
                    accuracy_data['main_number_matches'],
                    accuracy_data['bonus_number_matches'],
                    accuracy_data['matched_main_numbers'],
                    accuracy_data['matched_bonus_numbers'],
                    accuracy_data['accuracy_percentage'],
                    accuracy_data['accuracy_score'],
                    accuracy_data['prize_tier'],
                    accuracy_data['validation_status'],
                    prediction_id
                ))
                
                # After successful validation, unlock prediction and generate new one for next draw
                if accuracy_data['validation_status'] == 'validated':
                    # Unlock this prediction so it can be replaced
                    cursor.execute("""
                        UPDATE lottery_predictions 
                        SET is_locked = FALSE,
                            lock_reason = 'Unlocked after validation - ready for next draw generation'
                        WHERE id = %s
                    """, (prediction_id,))
                    
                    logger.info(f"🔓 Unlocked prediction {prediction_id} after validation - ready for next draw")
                
                # Generate new prediction for next draw after validation
                if accuracy_data['validation_status'] == 'validated':
                    self._generate_next_draw_prediction(prediction['game_type'], result['draw_date'], cursor)
                
                # Also update with the specific draw number for display on result pages
                cursor.execute("""
                    UPDATE lottery_predictions 
                    SET verified_draw_number = %s
                    WHERE id = %s
                """, (result['draw_number'], prediction_id))
                
                self.conn.commit()
                
                # Note: Replacement prediction generation moved to validate_all_pending_predictions 
                # to only generate for game types that actually had new results validated
                
                return {
                    'success': True,
                    'prediction_id': prediction_id,
                    'result_id': result['id'],
                    'game_type': prediction['game_type'],
                    'draw_number': result['draw_number'],
                    'draw_date': str(result['draw_date']),
                    'predicted_numbers': predicted_main,
                    'actual_numbers': actual_main,
                    'predicted_bonus': predicted_bonus,
                    'actual_bonus': actual_bonus,
                    **accuracy_data
                }
                
        except Exception as e:
            logger.error(f"Validation error: {e}")
            return {'error': str(e)}
    
    def validate_all_pending_predictions(self) -> List[Dict]:
        """
        Validate all pending predictions against available results
        Only generates replacement predictions for game types that had successful validations
        """
        results = []
        successfully_validated_game_types = set()  # Track which game types had successful validations
        
        try:
            with self.conn.cursor(cursor_factory=RealDictCursor) as cursor:
                # Get all unverified predictions
                cursor.execute("""
                    SELECT id, game_type, target_draw_date, created_at 
                    FROM lottery_predictions 
                    WHERE is_verified = false OR is_verified IS NULL
                    ORDER BY created_at DESC
                """)
                
                predictions = cursor.fetchall()
                logger.info(f"Found {len(predictions)} pending predictions to validate")
                
                for prediction in predictions:
                    # Try to find matching lottery result
                    # Look for results that match the game type and target date
                    game_type = prediction['game_type']
                    target_date = prediction['target_draw_date']
                    
                    # Map game types for lottery results
                    lottery_type_map = {
                        'DAILY LOTTO': 'DAILY LOTTO',
                        'LOTTO': 'LOTTO',
                        'LOTTO PLUS 1': 'LOTTO PLUS 1',
                        'LOTTO PLUS 2': 'LOTTO PLUS 2',
                        'POWERBALL': 'POWERBALL',
                        'POWERBALL PLUS': 'POWERBALL PLUS'
                    }
                    
                    cursor.execute("""
                        SELECT * FROM lottery_results 
                        WHERE lottery_type = %s AND draw_date = %s
                        ORDER BY created_at DESC LIMIT 1
                    """, (lottery_type_map.get(game_type, game_type), target_date))
                    
                    result = cursor.fetchone()
                    if result:
                        # Validate this prediction
                        validation_result = self.validate_prediction(
                            prediction['id'], 
                            lottery_result_id=result['id']
                        )
                        
                        if validation_result.get('success'):
                            successfully_validated_game_types.add(game_type)
                            results.append(validation_result)
                            logger.info(f"✅ Validated {game_type} prediction {prediction['id']}")
                        else:
                            logger.warning(f"❌ Failed to validate {game_type} prediction {prediction['id']}: {validation_result.get('error')}")
                    else:
                        logger.info(f"⏳ No result yet for {game_type} prediction {prediction['id']} targeting {target_date}")
                
                logger.info(f"Validation complete: {len(results)} predictions validated for {len(successfully_validated_game_types)} game types")
                
        except Exception as e:
            logger.error(f"Error validating pending predictions: {e}")
            
        return {
            'validation_results': {game_type: len([r for r in results if r.get('game_type') == game_type]) for game_type in successfully_validated_game_types},
            'total_validated': len(results),
            'game_types_with_validations': list(successfully_validated_game_types)
        }
    
    def validate_prediction(self, prediction_id: int, lottery_result_id: int = None, draw_number: int = None, game_type: str = None) -> Dict:
        """Validate a single prediction against lottery result"""
        return self.validate_prediction_against_result(prediction_id, lottery_result_id, draw_number, game_type)
    
    def generate_accuracy_report(self) -> Dict:
        """
        Generate comprehensive accuracy report for all validated predictions
        """
        try:
            with self.conn.cursor(cursor_factory=RealDictCursor) as cursor:
                # Overall statistics
                cursor.execute("""
                    SELECT 
                        game_type,
                        COUNT(*) as total_predictions,
                        COUNT(CASE WHEN is_verified = true THEN 1 END) as validated_predictions,
                        AVG(CASE WHEN is_verified = true THEN accuracy_score END) as avg_accuracy,
                        MAX(CASE WHEN is_verified = true THEN accuracy_score END) as best_accuracy,
                        COUNT(CASE WHEN prize_tier != 'No Prize' THEN 1 END) as winning_predictions
                    FROM lottery_predictions 
                    GROUP BY game_type
                    ORDER BY game_type
                """)
                
                game_stats = cursor.fetchall()
                
                # Recent validations
                cursor.execute("""
                    SELECT 
                        game_type, accuracy_score, prize_tier, 
                        main_number_matches, verified_at
                    FROM lottery_predictions 
                    WHERE is_verified = true 
                    ORDER BY verified_at DESC 
                    LIMIT 10
                """)
                
                recent_validations = cursor.fetchall()
                
                return {
                    'game_statistics': [dict(stat) for stat in game_stats],
                    'recent_validations': [dict(val) for val in recent_validations],
                    'generated_at': datetime.now().isoformat()
                }
                
        except Exception as e:
            logger.error(f"Error generating accuracy report: {e}")
            return {'error': str(e)}
    
    def _generate_next_draw_prediction(self, game_type: str, validated_draw_date, cursor):
        """Generate new prediction for next draw after successful validation"""
        try:
            from datetime import timedelta
            from ai_lottery_predictor import AILotteryPredictor
            
            # Calculate next draw date based on game type
            if game_type == 'DAILY LOTTO':
                next_draw_date = validated_draw_date + timedelta(days=1)
            elif game_type in ['POWERBALL', 'POWERBALL PLUS']:
                # PowerBall draws on Tuesday and Friday
                days_ahead = 2 if validated_draw_date.weekday() == 1 else 4  # Tuesday=1, Friday=4
                next_draw_date = validated_draw_date + timedelta(days=days_ahead)
            else:  # LOTTO games
                # LOTTO draws on Wednesday and Saturday
                days_ahead = 3 if validated_draw_date.weekday() == 2 else 4  # Wednesday=2, Saturday=5
                next_draw_date = validated_draw_date + timedelta(days=days_ahead)
            
            # Generate new intelligent prediction
            predictor = AILotteryPredictor()
            historical_data = predictor.get_historical_data_for_prediction(game_type, 100)
            
            if historical_data:
                prediction = predictor.generate_intelligent_prediction(game_type, historical_data)
                
                if prediction:
                    # Store the new prediction with locked=True for stability
                    cursor.execute("""
                        INSERT INTO lottery_predictions (
                            game_type, predicted_numbers, bonus_numbers, 
                            confidence_score, prediction_method, reasoning, 
                            target_draw_date, created_at, is_locked, lock_reason
                        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    """, (
                        prediction.game_type,
                        prediction.predicted_numbers,
                        prediction.bonus_numbers,
                        prediction.confidence_score,
                        prediction.prediction_method,
                        prediction.reasoning,
                        next_draw_date,
                        prediction.created_at,
                        True,  # Lock immediately for stability
                        'Prediction stability - locked to prevent automatic changes'
                    ))
                    
                    logger.info(f"✅ Generated new locked prediction for {game_type} targeting {next_draw_date}")
                    logger.info(f"Numbers: {prediction.predicted_numbers}, Confidence: {prediction.confidence_score}")
                else:
                    logger.warning(f"❌ Failed to generate intelligent prediction for {game_type}")
            else:
                logger.warning(f"❌ No historical data available for {game_type}")
                
        except Exception as e:
            logger.error(f"Error generating next draw prediction for {game_type}: {e}")
                """)
                
                recent_validations = cursor.fetchall()
                
                return {
                    'report_generated_at': datetime.now().isoformat(),
                    'game_statistics': [dict(stat) for stat in game_stats],
                    'recent_validations': [dict(val) for val in recent_validations],
                    'summary': {
                        'total_games': len(game_stats),
                        'overall_avg_accuracy': round(sum(stat['avg_accuracy'] or 0 for stat in game_stats) / len(game_stats) if game_stats else 0, 2)
                    }
                }
                
        except Exception as e:
            logger.error(f"Report generation error: {e}")
            return {'error': str(e)}
    
    def _generate_replacement_prediction(self, game_type: str):
        """Generate a new prediction to replace the validated one"""
        try:
            # Import the prediction generator
            from generate_ai_predictions import GeminiLotteryPredictor
            
            logger.info(f"Generating replacement prediction for {game_type}")
            predictor = GeminiLotteryPredictor()
            
            # Generate single prediction for this game type
            result = predictor.generate_single_prediction(game_type)
            
            if result.get('success'):
                logger.info(f"Successfully generated replacement prediction for {game_type}")
            else:
                logger.error(f"Failed to generate replacement prediction: {result.get('error', 'Unknown error')}")
                
        except Exception as e:
            logger.error(f"Error generating replacement prediction for {game_type}: {e}")
    
    def close(self):
        """Close database connection"""
        if self.conn:
            self.conn.close()
            logger.info("Database connection closed")

def main():
    """
    Main function to run prediction validation
    """
    logger.info("=== STARTING PREDICTION VALIDATION SYSTEM ===")
    
    try:
        validator = PredictionValidator()
        
        # Validate all pending predictions
        logger.info("Validating all pending predictions...")
        validation_results = validator.validate_all_pending_predictions()
        
        # Generate accuracy report
        logger.info("Generating accuracy report...")
        report = validator.generate_accuracy_report()
        
        # Print summary
        print("\n" + "="*60)
        print("PREDICTION VALIDATION SUMMARY")
        print("="*60)
        
        if validation_results:
            successful = [r for r in validation_results if r.get('success')]
            failed = [r for r in validation_results if not r.get('success')]
            
            print(f"✅ Successfully validated: {len(successful)} predictions")
            print(f"❌ Failed validations: {len(failed)} predictions")
            
            # Show detailed results for successful validations
            for result in successful:
                if result.get('success'):
                    print(f"\n🎯 {result['game_type']} Draw {result['draw_number']}:")
                    print(f"   Predicted: {result['predicted_numbers']}")
                    print(f"   Actual:    {result['actual_numbers']}")
                    print(f"   Matches:   {result['main_number_matches']}/{len(result['actual_numbers'])} ({result['accuracy_percentage']}%)")
                    print(f"   Prize:     {result['prize_tier']}")
        
        # Show accuracy report
        if report and 'game_statistics' in report:
            print("\n" + "="*60)
            print("ACCURACY STATISTICS BY GAME")
            print("="*60)
            
            for stat in report['game_statistics']:
                print(f"\n{stat['game_type']}:")
                print(f"  Total Predictions: {stat['total_predictions']}")
                print(f"  Validated: {stat['validated_predictions']}")
                print(f"  Average Accuracy: {stat['avg_accuracy']:.1f}%" if stat['avg_accuracy'] else "  Average Accuracy: N/A")
                print(f"  Best Accuracy: {stat['best_accuracy']:.1f}%" if stat['best_accuracy'] else "  Best Accuracy: N/A")
                print(f"  Winning Predictions: {stat['winning_predictions']}")
        
        validator.close()
        
        print(f"\n{'='*60}")
        print("VALIDATION COMPLETE")
        print(f"{'='*60}")
        
        return validation_results
        
    except Exception as e:
        logger.error(f"Validation system failed: {e}")
        raise

if __name__ == "__main__":
    main()