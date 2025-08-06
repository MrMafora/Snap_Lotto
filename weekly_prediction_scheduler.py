#!/usr/bin/env python3
"""
Weekly AI Lottery Prediction Scheduler
Automatically generates 3 predictions per game per week for all South African lottery games.
"""

import logging
import os
import sys
from datetime import datetime, timedelta
from ai_lottery_predictor import predictor
import psycopg2

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('weekly_predictions.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class WeeklyPredictionScheduler:
    """Handles automated weekly prediction generation"""
    
    def __init__(self):
        self.games = [
            'LOTTO',
            'LOTTO PLUS 1', 
            'LOTTO PLUS 2',
            'POWERBALL',
            'POWERBALL PLUS',
            'DAILY LOTTO'
        ]
        self.predictions_per_game = 3
        
    def generate_weekly_predictions(self):
        """Generate 3 predictions for each lottery game"""
        logger.info("=== STARTING WEEKLY PREDICTION GENERATION ===")
        
        total_generated = 0
        results = {}
        
        for game_type in self.games:
            try:
                logger.info(f"Generating {self.predictions_per_game} predictions for {game_type}")
                game_results = []
                
                for prediction_num in range(1, self.predictions_per_game + 1):
                    try:
                        # Generate prediction
                        logger.info(f"Generating {game_type} prediction #{prediction_num}")
                        
                        # Get historical data
                        historical_data = predictor.get_historical_data_for_prediction(game_type, 365)
                        
                        # Generate AI prediction with variation for multiple predictions
                        prediction = predictor.generate_ai_prediction(
                            game_type, 
                            historical_data,
                            variation_seed=prediction_num  # Add variation for different predictions
                        )
                        
                        # Save prediction to database
                        prediction_id = predictor.save_prediction(prediction)
                        
                        game_results.append({
                            'prediction_id': prediction_id,
                            'numbers': prediction.predicted_numbers,
                            'confidence': prediction.confidence_score
                        })
                        
                        total_generated += 1
                        logger.info(f"✓ Generated {game_type} prediction #{prediction_num} (ID: {prediction_id})")
                        
                    except Exception as e:
                        logger.error(f"Failed to generate {game_type} prediction #{prediction_num}: {e}")
                        continue
                
                results[game_type] = game_results
                logger.info(f"Completed {game_type}: {len(game_results)} predictions generated")
                
            except Exception as e:
                logger.error(f"Failed to process {game_type}: {e}")
                results[game_type] = []
                continue
        
        # Generate summary report
        self.generate_weekly_report(results, total_generated)
        
        logger.info(f"=== WEEKLY PREDICTION GENERATION COMPLETE ===")
        logger.info(f"Total predictions generated: {total_generated}")
        
        return results
    
    def generate_weekly_report(self, results, total_generated):
        """Generate a summary report of the week's predictions"""
        
        report_date = datetime.now().strftime("%Y-%m-%d")
        report_content = []
        
        report_content.append("=" * 60)
        report_content.append(f"WEEKLY AI PREDICTION REPORT - {report_date}")
        report_content.append("=" * 60)
        report_content.append(f"Total Predictions Generated: {total_generated}")
        report_content.append(f"Target per Game: {self.predictions_per_game}")
        report_content.append("")
        
        for game_type, predictions in results.items():
            report_content.append(f"🎲 {game_type}:")
            report_content.append(f"   Generated: {len(predictions)} predictions")
            
            if predictions:
                avg_confidence = sum(p['confidence'] for p in predictions) / len(predictions)
                report_content.append(f"   Average Confidence: {avg_confidence:.1%}")
                
                for i, pred in enumerate(predictions, 1):
                    numbers_str = ', '.join(map(str, sorted(pred['numbers'])))
                    report_content.append(f"   Prediction #{i}: [{numbers_str}] ({pred['confidence']:.1%})")
            else:
                report_content.append("   ❌ No predictions generated")
                
            report_content.append("")
        
        report_content.append("=" * 60)
        
        # Save report to file
        report_filename = f"weekly_predictions_report_{report_date}.txt"
        try:
            with open(report_filename, 'w') as f:
                f.write('\n'.join(report_content))
            logger.info(f"Weekly report saved: {report_filename}")
        except Exception as e:
            logger.error(f"Failed to save weekly report: {e}")
        
        # Log report to console
        for line in report_content:
            logger.info(line)
    
    def clean_old_predictions(self, days_to_keep=30):
        """Clean old predictions to prevent database bloat"""
        try:
            cutoff_date = datetime.now() - timedelta(days=days_to_keep)
            
            with psycopg2.connect(os.environ.get('DATABASE_URL')) as conn:
                with conn.cursor() as cur:
                    cur.execute("""
                        DELETE FROM lottery_predictions 
                        WHERE created_at < %s AND is_verified = false
                    """, (cutoff_date,))
                    
                    deleted_count = cur.rowcount
                    conn.commit()
                    
            logger.info(f"Cleaned {deleted_count} old unverified predictions older than {days_to_keep} days")
            
        except Exception as e:
            logger.error(f"Failed to clean old predictions: {e}")

def main():
    """Main execution function"""
    try:
        scheduler = WeeklyPredictionScheduler()
        
        # Clean old predictions first
        scheduler.clean_old_predictions()
        
        # Generate new weekly predictions
        results = scheduler.generate_weekly_predictions()
        
        # Exit with success
        logger.info("Weekly prediction generation completed successfully")
        return 0
        
    except Exception as e:
        logger.error(f"Weekly prediction generation failed: {e}")
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)