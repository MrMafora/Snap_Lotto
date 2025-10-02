#!/usr/bin/env python3
"""
ML Training Infrastructure for Lottery Prediction
Implements proper train/test split, validation, and backtesting
"""

import os
import psycopg2
import numpy as np
import pandas as pd
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional
from collections import Counter
import json

logger = logging.getLogger(__name__)

class LotteryMLTrainer:
    """
    Handles training infrastructure for lottery prediction models
    with proper time-series validation
    """
    
    def __init__(self):
        self.connection_string = os.environ.get("DATABASE_URL")
        self.game_configs = {
            'LOTTO': {'main_count': 6, 'main_range': (1, 52), 'bonus_count': 0},
            'LOTTO PLUS 1': {'main_count': 6, 'main_range': (1, 52), 'bonus_count': 0}, 
            'LOTTO PLUS 2': {'main_count': 6, 'main_range': (1, 52), 'bonus_count': 0},
            'POWERBALL': {'main_count': 5, 'main_range': (1, 50), 'bonus_count': 1, 'bonus_range': (1, 20)},
            'POWERBALL PLUS': {'main_count': 5, 'main_range': (1, 50), 'bonus_count': 1, 'bonus_range': (1, 20)},
            'DAILY LOTTO': {'main_count': 5, 'main_range': (1, 36), 'bonus_count': 0}
        }
    
    def get_historical_draws(self, game_type: str, days_back: int = 365) -> pd.DataFrame:
        """
        Fetch historical lottery draws for training
        Returns DataFrame with proper temporal ordering
        """
        try:
            conn = psycopg2.connect(self.connection_string)
            cur = conn.cursor()
            
            cur.execute('''
                SELECT 
                    draw_number,
                    draw_date,
                    main_numbers,
                    bonus_numbers,
                    created_at
                FROM lottery_results
                WHERE lottery_type = %s 
                  AND draw_date >= CURRENT_DATE - make_interval(days => %s)
                ORDER BY draw_date ASC
            ''', (game_type, days_back))
            
            results = cur.fetchall()
            cur.close()
            conn.close()
            
            if not results:
                logger.warning(f"No historical data found for {game_type}")
                return pd.DataFrame()
            
            # Convert to DataFrame
            data = []
            for draw_num, draw_date, main_nums, bonus_nums, created_at in results:
                # Parse main numbers
                if isinstance(main_nums, str):
                    if main_nums.startswith('{') and main_nums.endswith('}'):
                        main_str = main_nums.strip('{}')
                        main_list = [int(x.strip()) for x in main_str.split(',') if x.strip()]
                    else:
                        main_list = json.loads(main_nums)
                elif isinstance(main_nums, list):
                    main_list = main_nums
                else:
                    continue
                
                # Parse bonus numbers
                bonus_list = []
                if bonus_nums:
                    if isinstance(bonus_nums, str):
                        if bonus_nums.startswith('{') and bonus_nums.endswith('}'):
                            bonus_str = bonus_nums.strip('{}')
                            if bonus_str:
                                bonus_list = [int(x.strip()) for x in bonus_str.split(',') if x.strip()]
                        else:
                            bonus_list = json.loads(bonus_nums)
                    elif isinstance(bonus_nums, list):
                        bonus_list = bonus_nums
                
                data.append({
                    'draw_number': draw_num,
                    'draw_date': draw_date,
                    'main_numbers': sorted(main_list),
                    'bonus_numbers': sorted(bonus_list),
                    'created_at': created_at
                })
            
            df = pd.DataFrame(data)
            df['draw_date'] = pd.to_datetime(df['draw_date'])
            df = df.sort_values('draw_date').reset_index(drop=True)
            
            logger.info(f"✅ Loaded {len(df)} historical draws for {game_type}")
            return df
            
        except Exception as e:
            logger.error(f"Error fetching historical draws: {e}")
            return pd.DataFrame()
    
    def time_series_split(self, df: pd.DataFrame, n_splits: int = 5, 
                          test_size: int = 10) -> List[Tuple[pd.DataFrame, pd.DataFrame]]:
        """
        Time-series cross-validation split
        Each split uses past data for training, future data for testing
        
        Args:
            df: Historical draws DataFrame
            n_splits: Number of validation splits
            test_size: Number of draws in each test set
        
        Returns:
            List of (train_df, test_df) tuples
        """
        if len(df) < test_size * (n_splits + 1):
            logger.warning(f"Insufficient data for {n_splits} splits")
            n_splits = max(1, len(df) // test_size - 1)
        
        splits = []
        total_size = len(df)
        
        for i in range(n_splits):
            # Calculate split indices
            test_end = total_size - (n_splits - i - 1) * test_size
            test_start = test_end - test_size
            
            if test_start <= 0:
                continue
            
            train_df = df.iloc[:test_start].copy()
            test_df = df.iloc[test_start:test_end].copy()
            
            splits.append((train_df, test_df))
            logger.info(f"Split {i+1}: Train={len(train_df)} draws, Test={len(test_df)} draws")
        
        return splits
    
    def backtest_predictions(self, game_type: str, prediction_strategy_func, 
                            n_splits: int = 5) -> Dict:
        """
        Backtest a prediction strategy on historical data
        
        Args:
            game_type: Type of lottery game
            prediction_strategy_func: Function that takes training data and returns prediction
            n_splits: Number of cross-validation splits
        
        Returns:
            Dictionary with backtesting metrics
        """
        logger.info(f"🔍 Starting backtest for {game_type}...")
        
        # Get historical data
        df = self.get_historical_draws(game_type, days_back=365)
        
        if df.empty or len(df) < 20:
            logger.warning(f"Insufficient data for backtesting {game_type}")
            return {'error': 'Insufficient data', 'total_tests': 0}
        
        # Create time-series splits
        splits = self.time_series_split(df, n_splits=n_splits)
        
        if not splits:
            return {'error': 'Could not create validation splits', 'total_tests': 0}
        
        # Run backtest on each split
        results = {
            'game_type': game_type,
            'total_tests': 0,
            'total_main_matches': [],
            'total_bonus_matches': [],
            'accuracies': [],
            'split_results': []
        }
        
        for split_idx, (train_df, test_df) in enumerate(splits):
            logger.info(f"Testing split {split_idx + 1}/{len(splits)}...")
            
            split_matches = []
            
            for test_idx, test_row in test_df.iterrows():
                # Generate prediction using training data
                try:
                    prediction = prediction_strategy_func(train_df, game_type)
                    
                    if not prediction or 'main_numbers' not in prediction:
                        continue
                    
                    # Calculate matches
                    predicted_main = set(prediction['main_numbers'])
                    actual_main = set(test_row['main_numbers'])
                    main_matches = len(predicted_main & actual_main)
                    
                    predicted_bonus = set(prediction.get('bonus_numbers', []))
                    actual_bonus = set(test_row['bonus_numbers'])
                    bonus_matches = len(predicted_bonus & actual_bonus)
                    
                    # Calculate accuracy
                    config = self.game_configs[game_type]
                    total_numbers = config['main_count']
                    accuracy = (main_matches / total_numbers) * 100
                    
                    match_result = {
                        'test_draw': test_row['draw_number'],
                        'test_date': str(test_row['draw_date'].date()),
                        'predicted': prediction['main_numbers'],
                        'actual': test_row['main_numbers'],
                        'main_matches': main_matches,
                        'bonus_matches': bonus_matches,
                        'accuracy': accuracy
                    }
                    
                    split_matches.append(match_result)
                    results['total_main_matches'].append(main_matches)
                    results['total_bonus_matches'].append(bonus_matches)
                    results['accuracies'].append(accuracy)
                    results['total_tests'] += 1
                    
                except Exception as e:
                    logger.warning(f"Prediction failed for test draw: {e}")
                    continue
            
            results['split_results'].append({
                'split': split_idx + 1,
                'matches': split_matches
            })
        
        # Calculate summary statistics
        if results['total_tests'] > 0:
            results['avg_main_matches'] = np.mean(results['total_main_matches'])
            results['avg_bonus_matches'] = np.mean(results['total_bonus_matches'])
            results['avg_accuracy'] = np.mean(results['accuracies'])
            results['std_accuracy'] = np.std(results['accuracies'])
            
            # Distribution of match counts
            match_distribution = Counter(results['total_main_matches'])
            results['match_distribution'] = dict(match_distribution)
            
            logger.info(f"✅ Backtest complete: {results['total_tests']} tests")
            logger.info(f"   Avg matches: {results['avg_main_matches']:.2f}")
            logger.info(f"   Avg accuracy: {results['avg_accuracy']:.2f}%")
            logger.info(f"   Match distribution: {results['match_distribution']}")
        
        return results
    
    def save_backtest_results(self, results: Dict):
        """Save backtest results to database for tracking"""
        try:
            conn = psycopg2.connect(self.connection_string)
            cur = conn.cursor()
            
            # Create backtest results table if not exists
            cur.execute('''
                CREATE TABLE IF NOT EXISTS ml_backtest_results (
                    id SERIAL PRIMARY KEY,
                    game_type VARCHAR(50) NOT NULL,
                    total_tests INTEGER,
                    avg_main_matches DECIMAL(5,2),
                    avg_bonus_matches DECIMAL(5,2),
                    avg_accuracy DECIMAL(5,2),
                    std_accuracy DECIMAL(5,2),
                    match_distribution JSONB,
                    full_results JSONB,
                    test_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Insert results
            cur.execute('''
                INSERT INTO ml_backtest_results 
                (game_type, total_tests, avg_main_matches, avg_bonus_matches, 
                 avg_accuracy, std_accuracy, match_distribution, full_results)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            ''', (
                results['game_type'],
                results.get('total_tests', 0),
                results.get('avg_main_matches', 0),
                results.get('avg_bonus_matches', 0),
                results.get('avg_accuracy', 0),
                results.get('std_accuracy', 0),
                json.dumps(results.get('match_distribution', {})),
                json.dumps(results, default=str)
            ))
            
            conn.commit()
            cur.close()
            conn.close()
            
            logger.info(f"✅ Saved backtest results for {results['game_type']}")
            
        except Exception as e:
            logger.error(f"Error saving backtest results: {e}")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    # Test the training infrastructure
    trainer = LotteryMLTrainer()
    
    # Test data loading
    df = trainer.get_historical_draws('LOTTO', days_back=180)
    print(f"\nLoaded {len(df)} historical draws")
    
    # Test time-series split
    if not df.empty:
        splits = trainer.time_series_split(df, n_splits=3)
        print(f"Created {len(splits)} time-series splits")
