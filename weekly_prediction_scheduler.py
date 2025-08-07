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
        # Games with their draw frequencies
        self.game_schedules = {
            'LOTTO': {'draws_per_week': 2, 'predictions_per_draw': 3},  # Wed, Sat
            'LOTTO PLUS 1': {'draws_per_week': 2, 'predictions_per_draw': 3},  # Wed, Sat
            'LOTTO PLUS 2': {'draws_per_week': 2, 'predictions_per_draw': 3},  # Wed, Sat
            'POWERBALL': {'draws_per_week': 2, 'predictions_per_draw': 3},  # Tue, Fri
            'POWERBALL PLUS': {'draws_per_week': 2, 'predictions_per_draw': 3},  # Tue, Fri
            'DAILY LOTTO': {'draws_per_week': 7, 'predictions_per_draw': 3}  # Every day
        }
        
    def cleanup_old_predictions(self, game_type, max_predictions):
        """Remove old predictions to maintain target count per game"""
        try:
            with psycopg2.connect(os.environ.get('DATABASE_URL')) as conn:
                with conn.cursor() as cur:
                    # Count current predictions for this game
                    cur.execute("SELECT COUNT(*) FROM lottery_predictions WHERE game_type = %s", (game_type,))
                    current_count = cur.fetchone()[0]
                    
                    if current_count > max_predictions:
                        excess_count = current_count - max_predictions
                        logger.info(f"Removing {excess_count} old {game_type} predictions (keeping newest {max_predictions})")
                        
                        # Delete oldest predictions beyond the limit
                        cur.execute("""
                            DELETE FROM lottery_predictions 
                            WHERE id IN (
                                SELECT id FROM lottery_predictions 
                                WHERE game_type = %s 
                                ORDER BY created_at ASC 
                                LIMIT %s
                            )
                        """, (game_type, excess_count))
                        
                        conn.commit()
                        logger.info(f"Successfully cleaned up {excess_count} old predictions for {game_type}")
                        
        except Exception as e:
            logger.error(f"Error cleaning up predictions for {game_type}: {e}")

    def generate_weekly_predictions(self):
        """Generate predictions for each lottery game based on draw frequency"""
        logger.info("=== STARTING WEEKLY PREDICTION GENERATION ===")
        
        total_generated = 0
        results = {}
        
        # First, cleanup old predictions to maintain target counts
        for game_type, schedule in self.game_schedules.items():
            target_count = schedule['draws_per_week'] * schedule['predictions_per_draw']
            self.cleanup_old_predictions(game_type, target_count)
        
        for game_type, schedule in self.game_schedules.items():
            try:
                draws_per_week = schedule['draws_per_week']
                predictions_per_draw = schedule['predictions_per_draw']
                total_predictions_needed = draws_per_week * predictions_per_draw
                
                logger.info(f"Generating {total_predictions_needed} predictions for {game_type} "
                          f"({draws_per_week} draws × {predictions_per_draw} predictions per draw)")
                
                game_results = []
                
                # Check how many predictions already exist
                with psycopg2.connect(os.environ.get('DATABASE_URL')) as conn:
                    with conn.cursor() as cur:
                        cur.execute("SELECT COUNT(*) FROM lottery_predictions WHERE game_type = %s", (game_type,))
                        existing_count = cur.fetchone()[0]
                
                predictions_to_generate = max(0, total_predictions_needed - existing_count)
                
                if predictions_to_generate == 0:
                    logger.info(f"{game_type} already has {existing_count} predictions - skipping generation")
                    results[game_type] = {'generated': 0, 'existing': existing_count}
                    continue
                
                logger.info(f"Generating {predictions_to_generate} new predictions for {game_type} (existing: {existing_count})")
                
                # Generate only the needed predictions
                generated_count = 0
                for i in range(predictions_to_generate):
                    try:
                        # Calculate unique variation seed
                        variation_seed = (i + existing_count + 1) * 13  # Unique seed
                        
                        logger.info(f"Generating {game_type} Prediction #{i+1}/{predictions_to_generate}")
                        
                        # Get historical data
                        historical_data = predictor.get_historical_data_for_prediction(game_type, 365)
                        
                        # Generate AI prediction with unique variation
                        prediction = predictor.generate_ai_prediction(
                            game_type, 
                            historical_data,
                            variation_seed=variation_seed
                        )
                        
                        if prediction:
                            # Store prediction in database
                            success = predictor.store_prediction_in_database(
                                game_type, prediction, f"Weekly Auto-Generation #{i+1}"
                            )
                            
                            if success:
                                game_results.append({
                                    'prediction': i+1,
                                    'numbers': prediction.predicted_numbers,
                                    'bonus': getattr(prediction, 'bonus_numbers', []),
                                    'confidence': prediction.confidence_score
                                })
                                generated_count += 1
                                total_generated += 1
                                logger.info(f"✅ Stored {game_type} Prediction #{i+1}")
                            else:
                                logger.error(f"❌ Failed to store {game_type} Prediction #{i+1}")
                        else:
                            logger.error(f"❌ Failed to generate {game_type} Prediction #{i+1}")
                            
                    except Exception as e:
                        logger.error(f"Error generating {game_type} Prediction #{i+1}: {e}")
                        continue
                
                results[game_type] = {'generated': generated_count, 'existing': existing_count, 'total': existing_count + generated_count}
                logger.info(f"Completed {game_type}: {generated_count} new + {existing_count} existing = {existing_count + generated_count} total predictions")
                
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
        report_content.append("Prediction Strategy: 3 predictions per draw, tailored to each game's schedule")
        report_content.append("")
        
        for game_type, predictions in results.items():
            schedule = self.game_schedules.get(game_type, {})
            draws_per_week = schedule.get('draws_per_week', 0)
            predictions_per_draw = schedule.get('predictions_per_draw', 0)
            expected_total = draws_per_week * predictions_per_draw
            
            report_content.append(f"🎲 {game_type}:")
            report_content.append(f"   Schedule: {draws_per_week} draws/week × {predictions_per_draw} predictions/draw = {expected_total} total")
            report_content.append(f"   Generated: {len(predictions)} predictions")
            
            if predictions:
                avg_confidence = sum(p['confidence'] for p in predictions) / len(predictions)
                report_content.append(f"   Average Confidence: {avg_confidence:.1%}")
                
                # Group by draw
                draws = {}
                for pred in predictions:
                    draw_num = pred.get('draw_number', 1)
                    if draw_num not in draws:
                        draws[draw_num] = []
                    draws[draw_num].append(pred)
                
                for draw_num in sorted(draws.keys()):
                    report_content.append(f"   Draw #{draw_num}:")
                    for pred in draws[draw_num]:
                        numbers_str = ', '.join(map(str, sorted(pred['numbers'])))
                        pred_num = pred.get('prediction_number', 0)
                        report_content.append(f"     P{pred_num}: [{numbers_str}] ({pred['confidence']:.1%})")
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