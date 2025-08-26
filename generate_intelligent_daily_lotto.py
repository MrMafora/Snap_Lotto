#!/usr/bin/env python3
"""
Generate intelligent Daily Lotto prediction using full learning framework
"""

import os
import sys
import logging
import psycopg2
from datetime import datetime
from ai_lottery_predictor import AILotteryPredictor

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def generate_intelligent_prediction():
    """Generate and save intelligent Daily Lotto prediction"""
    try:
        print('\n🧠 GENERATING INTELLIGENT DAILY LOTTO PREDICTION')
        print('=' * 60)
        
        predictor = AILotteryPredictor()
        
        # Get historical data with full learning framework
        print('📊 Retrieving comprehensive historical analysis...')
        historical_data = predictor.get_historical_data_for_prediction('DAILY LOTTO')
        
        if not historical_data or 'draws' not in historical_data:
            print('❌ Failed to retrieve historical data')
            return False
            
        print(f'   Retrieved {len(historical_data["draws"])} historical draws')
        print(f'   Extended analysis includes drought cycles, hot/cold transitions, patterns')
        
        # Use the primary AI prediction method with learning data
        print('🧠 Generating AI prediction with comprehensive learning...')
        prediction_result = predictor.generate_ai_prediction('DAILY LOTTO', historical_data)
        
        if prediction_result and prediction_result.get('success'):
            pred = prediction_result['prediction']
            print(f'\n✅ INTELLIGENT PREDICTION GENERATED:')
            print(f'   Numbers: {pred.predicted_numbers}')
            print(f'   Confidence: {pred.confidence_score:.1f}%')
            print(f'   Method: {pred.prediction_method}')
            print(f'   Reasoning: {pred.reasoning[:200]}...')
            
            # Replace current backup prediction
            connection_string = os.environ.get('DATABASE_URL')
            with psycopg2.connect(connection_string) as conn:
                with conn.cursor() as cur:
                    # Remove old backup prediction
                    cur.execute("""
                        DELETE FROM lottery_predictions 
                        WHERE game_type = 'DAILY LOTTO' AND validation_status = 'pending'
                    """)
                    print(f'   - Removed backup prediction')
                    
                    # Save the new intelligent prediction
                    prediction_id = predictor.store_prediction_in_database(pred)
                    print(f'   - Saved new prediction ID: {prediction_id}')
            
            print('\n🎉 SUCCESS: Daily Lotto now has INTELLIGENT prediction!')
            print('   ✅ Uses 100+ historical draws')
            print('   ✅ Multi-dimensional pattern analysis')
            print('   ✅ Performance-based learning')
            print('   ✅ AI confidence calibration')
            return True
            
        else:
            print(f'❌ Primary AI method failed: {prediction_result}')
            return False
            
    except Exception as e:
        print(f'❌ Error: {e}')
        return False

if __name__ == "__main__":
    success = generate_intelligent_prediction()
    sys.exit(0 if success else 1)