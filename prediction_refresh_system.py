#!/usr/bin/env python3
"""
Prediction Refresh System
Updates AI predictions only when new draw results become available for each game type.
Predictions remain static until validated against actual results.
"""

import logging
import os
import psycopg2
from datetime import datetime, timedelta
from ai_lottery_predictor import predictor

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('prediction_refresh.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class PredictionRefreshSystem:
    """Manages prediction refresh based on new draw results"""
    
    def __init__(self):
        self.game_types = [
            'LOTTO', 'LOTTO PLUS 1', 'LOTTO PLUS 2', 
            'POWERBALL', 'POWERBALL PLUS', 'DAILY LOTTO'
        ]
        
    def get_latest_draw_date(self, game_type):
        """Get the date of the most recent draw for a game type"""
        try:
            with psycopg2.connect(os.environ.get('DATABASE_URL')) as conn:
                with conn.cursor() as cur:
                    cur.execute("""
                        SELECT MAX(draw_date) 
                        FROM lottery_results 
                        WHERE lottery_type = %s
                    """, (game_type,))
                    result = cur.fetchone()
                    return result[0] if result and result[0] else None
        except Exception as e:
            logger.error(f"Error getting latest draw date for {game_type}: {e}")
            return None
    
    def get_last_prediction_update(self, game_type):
        """Get the date when predictions were last updated for a game type"""
        try:
            with psycopg2.connect(os.environ.get('DATABASE_URL')) as conn:
                with conn.cursor() as cur:
                    cur.execute("""
                        SELECT MAX(created_at) 
                        FROM lottery_predictions 
                        WHERE game_type = %s
                    """, (game_type,))
                    result = cur.fetchone()
                    return result[0] if result and result[0] else None
        except Exception as e:
            logger.error(f"Error getting last prediction update for {game_type}: {e}")
            return None
    
    def should_refresh_predictions(self, game_type):
        """Check if predictions should be refreshed based on new draw data"""
        latest_draw = self.get_latest_draw_date(game_type)
        last_prediction_update = self.get_last_prediction_update(game_type)
        
        if not latest_draw:
            logger.info(f"No draw data found for {game_type}")
            return False
            
        if not last_prediction_update:
            logger.info(f"No predictions exist for {game_type} - refresh needed")
            return True
            
        # Refresh if there's a new draw since last prediction update
        if latest_draw > last_prediction_update.date():
            logger.info(f"New draw data available for {game_type} - refresh needed")
            logger.info(f"  Latest draw: {latest_draw}")
            logger.info(f"  Last prediction update: {last_prediction_update.date()}")
            return True
            
        logger.info(f"No new draws for {game_type} - predictions remain static")
        return False
    
    def refresh_predictions_for_game(self, game_type):
        """Generate fresh predictions for a specific game type"""
        logger.info(f"Refreshing predictions for {game_type}")
        
        try:
            # Clear existing predictions for this game
            with psycopg2.connect(os.environ.get('DATABASE_URL')) as conn:
                with conn.cursor() as cur:
                    cur.execute("DELETE FROM lottery_predictions WHERE game_type = %s", (game_type,))
                    conn.commit()
                    logger.info(f"Cleared existing predictions for {game_type}")
            
            # Generate 3 new predictions
            generated_count = 0
            for i in range(3):
                try:
                    # Get fresh historical data
                    historical_data = predictor.get_historical_data_for_prediction(game_type, 365)
                    
                    # Generate AI prediction with unique seed
                    variation_seed = (i + 1) * 17 + hash(game_type) % 100
                    prediction = predictor.generate_ai_prediction(
                        game_type, 
                        historical_data,
                        variation_seed=variation_seed
                    )
                    
                    if prediction:
                        success = predictor.store_prediction_in_database(
                            game_type, 
                            prediction, 
                            f"Refreshed after new draw #{i+1}"
                        )
                        
                        if success:
                            generated_count += 1
                            logger.info(f"✅ Generated new {game_type} prediction #{i+1}")
                        else:
                            logger.error(f"❌ Failed to store {game_type} prediction #{i+1}")
                    else:
                        logger.error(f"❌ Failed to generate {game_type} prediction #{i+1}")
                        
                except Exception as e:
                    logger.error(f"Error generating {game_type} prediction #{i+1}: {e}")
                    continue
            
            logger.info(f"Successfully refreshed {generated_count}/3 predictions for {game_type}")
            return generated_count
            
        except Exception as e:
            logger.error(f"Error refreshing predictions for {game_type}: {e}")
            return 0
    
    def check_and_refresh_all_predictions(self):
        """Check all game types and refresh predictions where new draw data exists"""
        logger.info("=== CHECKING FOR PREDICTION REFRESH NEEDS ===")
        
        refresh_summary = {}
        total_refreshed = 0
        
        for game_type in self.game_types:
            try:
                if self.should_refresh_predictions(game_type):
                    refreshed_count = self.refresh_predictions_for_game(game_type)
                    refresh_summary[game_type] = {
                        'action': 'refreshed',
                        'count': refreshed_count
                    }
                    total_refreshed += refreshed_count
                else:
                    refresh_summary[game_type] = {
                        'action': 'kept_static',
                        'count': 0
                    }
                    
            except Exception as e:
                logger.error(f"Error processing {game_type}: {e}")
                refresh_summary[game_type] = {
                    'action': 'error',
                    'count': 0
                }
        
        # Generate summary report
        logger.info("=== PREDICTION REFRESH SUMMARY ===")
        for game_type, summary in refresh_summary.items():
            if summary['action'] == 'refreshed':
                logger.info(f"🔄 {game_type}: Refreshed {summary['count']}/3 predictions")
            elif summary['action'] == 'kept_static':
                logger.info(f"📌 {game_type}: Keeping existing predictions (no new draws)")
            else:
                logger.info(f"❌ {game_type}: Error during refresh")
        
        logger.info(f"Total predictions refreshed: {total_refreshed}")
        return refresh_summary

def main():
    """Run prediction refresh check"""
    refresh_system = PredictionRefreshSystem()
    return refresh_system.check_and_refresh_all_predictions()

if __name__ == "__main__":
    main()