#!/usr/bin/env python3
"""
Prediction Validation System
Automatically validates predictions against actual draw results and provides insights for improvement
"""

import logging
import os
import sys
from datetime import datetime, timedelta
from typing import Dict, List, Any
import psycopg2
from ai_lottery_predictor import predictor

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('prediction_validation.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class PredictionValidationSystem:
    """Handles prediction validation against actual lottery results"""
    
    def __init__(self):
        self.connection_string = os.environ.get('DATABASE_URL')
    
    def auto_validate_pending_predictions(self) -> Dict[str, Any]:
        """Automatically validate predictions against available lottery results"""
        logger.info("=== STARTING AUTOMATIC PREDICTION VALIDATION ===")
        
        validation_results = {
            'validated_count': 0,
            'pending_count': 0,
            'results': []
        }
        
        try:
            with psycopg2.connect(self.connection_string) as conn:
                with conn.cursor() as cur:
                    # Get unvalidated predictions that should have results by now
                    cur.execute("""
                        SELECT p.id, p.game_type, p.predicted_numbers, p.bonus_numbers, 
                               p.target_draw_date, p.created_at, p.confidence_score
                        FROM lottery_predictions p
                        WHERE p.is_verified = false 
                        AND p.target_draw_date <= CURRENT_DATE
                        ORDER BY p.target_draw_date DESC, p.created_at DESC
                    """)
                    
                    pending_predictions = cur.fetchall()
                    validation_results['pending_count'] = len(pending_predictions)
                    
                    for prediction in pending_predictions:
                        pred_id, game_type, predicted_main, predicted_bonus, target_date, created_at, confidence = prediction
                        
                        # Find matching actual result
                        actual_result = self.find_matching_draw_result(cur, game_type, target_date)
                        
                        if actual_result:
                            actual_main, actual_bonus, draw_date = actual_result
                            
                            # Validate prediction
                            validation = predictor.validate_prediction_against_draw(
                                pred_id, actual_main, actual_bonus
                            )
                            
                            if 'error' not in validation:
                                validation_results['validated_count'] += 1
                                validation_results['results'].append(validation)
                                
                                logger.info(f"✓ Validated {game_type} prediction {pred_id}: "
                                          f"{validation['main_matches']} matches ({validation['accuracy_percentage']:.1f}%)")
                            else:
                                logger.error(f"Failed to validate prediction {pred_id}: {validation['error']}")
                        else:
                            logger.info(f"No matching result found for {game_type} prediction {pred_id} (target: {target_date})")
            
            logger.info(f"=== VALIDATION COMPLETE: {validation_results['validated_count']}/{validation_results['pending_count']} predictions validated ===")
            
        except Exception as e:
            logger.error(f"Error in auto validation: {e}")
            validation_results['error'] = str(e)
        
        return validation_results
    
    def find_matching_draw_result(self, cursor, game_type: str, target_date) -> tuple:
        """Find the actual lottery result that matches a prediction"""
        try:
            # Look for results within 7 days of target date
            cursor.execute("""
                SELECT main_numbers, bonus_numbers, draw_date
                FROM lottery_results 
                WHERE lottery_type = %s 
                AND draw_date >= %s 
                AND draw_date <= %s + INTERVAL '7 days'
                ORDER BY ABS(EXTRACT(DAY FROM (draw_date - %s)))
                LIMIT 1
            """, (game_type, target_date, target_date, target_date))
            
            return cursor.fetchone()
            
        except Exception as e:
            logger.error(f"Error finding matching draw result: {e}")
            return None
    
    def get_validation_summary_report(self, days: int = 30) -> Dict[str, Any]:
        """Generate a comprehensive validation summary report"""
        try:
            insights = predictor.get_prediction_accuracy_insights(days=days)
            
            report = {
                'report_date': datetime.now().isoformat(),
                'analysis_period': f"Last {days} days",
                'summary': insights,
                'recommendations': self.generate_improvement_recommendations(insights)
            }
            
            return report
            
        except Exception as e:
            logger.error(f"Error generating validation report: {e}")
            return {'error': str(e)}
    
    def generate_improvement_recommendations(self, insights: Dict[str, Any]) -> List[str]:
        """Generate recommendations for improving prediction accuracy"""
        recommendations = []
        
        try:
            accuracy_stats = insights.get('accuracy_stats', [])
            successful_numbers = insights.get('successful_numbers', [])
            
            if accuracy_stats:
                # Find best and worst performing games
                best_game = max(accuracy_stats, key=lambda x: x['avg_accuracy'])
                worst_game = min(accuracy_stats, key=lambda x: x['avg_accuracy'])
                
                recommendations.append(f"Best performing game: {best_game['game_type']} ({best_game['avg_accuracy']:.1f}% accuracy)")
                recommendations.append(f"Focus improvement on: {worst_game['game_type']} ({worst_game['avg_accuracy']:.1f}% accuracy)")
                
                # Analyze confidence vs accuracy correlation
                high_confidence_low_accuracy = [
                    game for game in accuracy_stats 
                    if game['avg_confidence'] > 0.4 and game['avg_accuracy'] < 20
                ]
                
                if high_confidence_low_accuracy:
                    recommendations.append("Consider reducing confidence scores for predictions that consistently underperform")
                
            if successful_numbers:
                top_numbers = [str(num['number']) for num in successful_numbers[:5]]
                recommendations.append(f"Numbers with highest success rate: {', '.join(top_numbers)}")
                
                # Look for patterns in successful numbers
                hot_numbers = [num for num in successful_numbers if num['avg_matches_when_predicted'] > 1.5]
                if hot_numbers:
                    recommendations.append(f"Consider prioritizing these high-performing numbers in future predictions")
            
            # General recommendations
            recommendations.extend([
                "Validate predictions daily to maintain accurate performance metrics",
                "Consider adjusting AI temperature based on game-specific accuracy patterns",
                "Analyze number frequency patterns from recent draws for better predictions"
            ])
            
        except Exception as e:
            logger.error(f"Error generating recommendations: {e}")
            recommendations.append("Error generating specific recommendations - review accuracy data manually")
        
        return recommendations

def main():
    """Main execution function for validation system"""
    try:
        validator = PredictionValidationSystem()
        
        # Run automatic validation
        results = validator.auto_validate_pending_predictions()
        
        # Generate and log summary report
        report = validator.get_validation_summary_report()
        
        logger.info("=== VALIDATION SUMMARY ===")
        for recommendation in report.get('recommendations', []):
            logger.info(f"📝 {recommendation}")
        
        return 0
        
    except Exception as e:
        logger.error(f"Validation system failed: {e}")
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)