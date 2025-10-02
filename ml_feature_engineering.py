#!/usr/bin/env python3
"""
Advanced Feature Engineering for Lottery Prediction
Implements temporal decay, inter-draw gaps, seasonality, co-occurrence patterns, etc.
"""

import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Set
from collections import Counter, defaultdict
import logging

logger = logging.getLogger(__name__)

class LotteryFeatureEngineer:
    """
    Engineers advanced features from historical lottery data
    for machine learning models
    """
    
    def __init__(self, game_config: Dict):
        self.game_config = game_config
        self.main_range = game_config['main_range']
        self.main_count = game_config['main_count']
        self.bonus_range = game_config.get('bonus_range', (0, 0))
        self.bonus_count = game_config.get('bonus_count', 0)
    
    def extract_all_features(self, historical_df: pd.DataFrame, 
                            target_date: datetime = None) -> Dict:
        """
        Extract all features from historical draws
        
        Args:
            historical_df: DataFrame with historical lottery draws
            target_date: Date for which to generate features (default: next draw)
        
        Returns:
            Dictionary with all engineered features
        """
        if historical_df.empty:
            return {}
        
        features = {}
        
        # Temporal features
        try:
            features.update(self.temporal_decay_features(historical_df))
        except Exception as e:
            logger.warning(f"Temporal features failed: {e}")
        
        # Gap-based features
        try:
            features.update(self.inter_draw_gap_features(historical_df))
        except Exception as e:
            logger.warning(f"Gap features failed: {e}")
        
        # Seasonality features
        try:
            features.update(self.seasonality_features(historical_df, target_date))
        except Exception as e:
            logger.warning(f"Seasonality features failed: {e}")
        
        # Co-occurrence patterns
        try:
            features.update(self.co_occurrence_features(historical_df))
        except Exception as e:
            logger.warning(f"Co-occurrence features failed: {e}")
        
        # Sequential dependencies
        try:
            features.update(self.sequential_dependency_features(historical_df))
        except Exception as e:
            logger.warning(f"Sequential features failed: {e}")
        
        # Statistical momentum
        try:
            features.update(self.statistical_momentum_features(historical_df))
        except Exception as e:
            logger.warning(f"Momentum features failed: {e}")
        
        logger.info(f"✅ Extracted {len(features)} feature categories")
        return features
    
    def temporal_decay_features(self, df: pd.DataFrame, 
                                decay_factor: float = 0.95) -> Dict:
        """
        Calculate frequency with temporal decay (recent draws weighted higher)
        
        Args:
            df: Historical draws DataFrame
            decay_factor: Decay rate for older draws (0.95 = 5% decay per draw)
        
        Returns:
            Dict with decay-weighted frequencies
        """
        features = {
            'temporal_main_freq': {},
            'temporal_bonus_freq': {},
            'recency_scores': {}
        }
        
        # Calculate decay weights (most recent = 1.0, older draws decay)
        n_draws = len(df)
        weights = np.array([decay_factor ** i for i in range(n_draws)])[::-1]
        
        # Temporal frequency for main numbers
        main_freq = defaultdict(float)
        for position, (idx, row) in enumerate(df.iterrows()):
            weight = weights[position]
            for num in row['main_numbers']:
                main_freq[num] += weight
        
        # Normalize to 0-1 range
        if main_freq:
            max_freq = max(main_freq.values())
            features['temporal_main_freq'] = {
                num: freq / max_freq for num, freq in main_freq.items()
            }
        
        # Temporal frequency for bonus numbers
        if self.bonus_count > 0:
            bonus_freq = defaultdict(float)
            for position, (idx, row) in enumerate(df.iterrows()):
                weight = weights[position]
                for num in row['bonus_numbers']:
                    bonus_freq[num] += weight
            
            if bonus_freq:
                max_bonus_freq = max(bonus_freq.values())
                features['temporal_bonus_freq'] = {
                    num: freq / max_bonus_freq for num, freq in bonus_freq.items()
                }
        
        # Recency scores (how recently each number appeared)
        for num in range(self.main_range[0], self.main_range[1] + 1):
            # Find most recent appearance
            for idx in range(len(df) - 1, -1, -1):
                if num in df.iloc[idx]['main_numbers']:
                    draws_ago = len(df) - idx
                    features['recency_scores'][num] = 1.0 / (draws_ago + 1)
                    break
            
            # If never appeared, set low score
            if num not in features['recency_scores']:
                features['recency_scores'][num] = 0.0
        
        return features
    
    def inter_draw_gap_features(self, df: pd.DataFrame) -> Dict:
        """
        Calculate gap patterns (how long since each number last appeared)
        """
        features = {
            'current_gaps': {},
            'avg_historical_gaps': {},
            'gap_momentum': {}
        }
        
        n_draws = len(df)
        
        for num in range(self.main_range[0], self.main_range[1] + 1):
            appearances = []
            
            # Find all appearances
            for idx, row in df.iterrows():
                if num in row['main_numbers']:
                    appearances.append(idx)
            
            if not appearances:
                # Never appeared
                features['current_gaps'][num] = n_draws
                features['avg_historical_gaps'][num] = 999  # High value
                features['gap_momentum'][num] = 0.0
            else:
                # Current gap (draws since last appearance)
                features['current_gaps'][num] = n_draws - appearances[-1] - 1
                
                # Average gap between appearances
                if len(appearances) > 1:
                    gaps = [appearances[i] - appearances[i-1] for i in range(1, len(appearances))]
                    features['avg_historical_gaps'][num] = np.mean(gaps)
                    
                    # Gap momentum (is gap growing or shrinking?)
                    recent_gaps = gaps[-3:] if len(gaps) >= 3 else gaps
                    features['gap_momentum'][num] = np.mean(recent_gaps) if recent_gaps else 0.0
                else:
                    features['avg_historical_gaps'][num] = features['current_gaps'][num]
                    features['gap_momentum'][num] = 0.0
        
        return features
    
    def seasonality_features(self, df: pd.DataFrame, 
                            target_date: datetime = None) -> Dict:
        """
        Extract seasonality patterns (day of week, month, quarter)
        """
        if target_date is None:
            target_date = datetime.now()
        
        features = {
            'day_of_week': target_date.weekday(),  # 0=Monday, 6=Sunday
            'month': target_date.month,
            'quarter': (target_date.month - 1) // 3 + 1,
            'day_of_week_freq': {},
            'month_freq': {},
            'quarter_freq': {}
        }
        
        # Analyze patterns by day of week
        dow_numbers = defaultdict(list)
        for _, row in df.iterrows():
            dow = row['draw_date'].weekday()
            dow_numbers[dow].extend(row['main_numbers'])
        
        # Calculate frequency for target day of week
        target_dow = target_date.weekday()
        if target_dow in dow_numbers:
            dow_freq = Counter(dow_numbers[target_dow])
            features['day_of_week_freq'] = dict(dow_freq)
        
        # Analyze patterns by month
        month_numbers = defaultdict(list)
        for _, row in df.iterrows():
            month = row['draw_date'].month
            month_numbers[month].extend(row['main_numbers'])
        
        target_month = target_date.month
        if target_month in month_numbers:
            month_freq = Counter(month_numbers[target_month])
            features['month_freq'] = dict(month_freq)
        
        # Analyze patterns by quarter
        quarter_numbers = defaultdict(list)
        for _, row in df.iterrows():
            quarter = (row['draw_date'].month - 1) // 3 + 1
            quarter_numbers[quarter].extend(row['main_numbers'])
        
        target_quarter = (target_date.month - 1) // 3 + 1
        if target_quarter in quarter_numbers:
            quarter_freq = Counter(quarter_numbers[target_quarter])
            features['quarter_freq'] = dict(quarter_freq)
        
        return features
    
    def co_occurrence_features(self, df: pd.DataFrame) -> Dict:
        """
        Find which numbers frequently appear together
        """
        features = {
            'pair_frequencies': {},
            'high_affinity_pairs': [],
            'number_associations': defaultdict(list)
        }
        
        # Count number pairs
        pair_counts = Counter()
        for _, row in df.iterrows():
            numbers = row['main_numbers']
            for i, num1 in enumerate(numbers):
                for num2 in numbers[i+1:]:
                    pair = tuple(sorted([num1, num2]))
                    pair_counts[pair] += 1
        
        # Store pair frequencies
        features['pair_frequencies'] = dict(pair_counts)
        
        # Find high-affinity pairs (appear together frequently)
        total_draws = len(df)
        high_affinity_threshold = total_draws * 0.15  # 15% of draws
        
        for pair, count in pair_counts.items():
            if count >= high_affinity_threshold:
                features['high_affinity_pairs'].append({
                    'numbers': pair,
                    'frequency': count,
                    'percentage': (count / total_draws) * 100
                })
        
        # Build association map (for each number, which numbers appear with it often)
        for (num1, num2), count in pair_counts.items():
            if count >= total_draws * 0.10:  # 10% threshold
                features['number_associations'][num1].append(num2)
                features['number_associations'][num2].append(num1)
        
        return features
    
    def sequential_dependency_features(self, df: pd.DataFrame, 
                                      window_size: int = 5) -> Dict:
        """
        Analyze sequential patterns across consecutive draws
        """
        features = {
            'carry_over_rate': {},  # How often numbers repeat in next draw
            'alternating_patterns': {},
            'consecutive_appearances': {}
        }
        
        if len(df) < 2:
            return features
        
        # Analyze carry-over (numbers appearing in consecutive draws)
        carry_over_counts = defaultdict(int)
        carry_over_total = defaultdict(int)
        
        for idx in range(len(df) - 1):
            current_nums = set(df.iloc[idx]['main_numbers'])
            next_nums = set(df.iloc[idx + 1]['main_numbers'])
            
            for num in current_nums:
                carry_over_total[num] += 1
                if num in next_nums:
                    carry_over_counts[num] += 1
        
        # Calculate carry-over rates
        for num in carry_over_total:
            if carry_over_total[num] > 0:
                features['carry_over_rate'][num] = carry_over_counts[num] / carry_over_total[num]
        
        # Consecutive appearance streaks
        for num in range(self.main_range[0], self.main_range[1] + 1):
            max_streak = 0
            current_streak = 0
            
            for _, row in df.iterrows():
                if num in row['main_numbers']:
                    current_streak += 1
                    max_streak = max(max_streak, current_streak)
                else:
                    current_streak = 0
            
            features['consecutive_appearances'][num] = max_streak
        
        return features
    
    def statistical_momentum_features(self, df: pd.DataFrame, 
                                     short_window: int = 10,
                                     long_window: int = 30) -> Dict:
        """
        Calculate momentum indicators (hot/cold trends)
        """
        features = {
            'short_term_hot': [],
            'short_term_cold': [],
            'long_term_hot': [],
            'long_term_cold': [],
            'momentum_score': {}
        }
        
        if len(df) < short_window:
            return features
        
        # Short-term frequency
        short_df = df.tail(short_window)
        short_freq = Counter()
        for _, row in short_df.iterrows():
            short_freq.update(row['main_numbers'])
        
        # Long-term frequency
        long_df = df.tail(long_window) if len(df) >= long_window else df
        long_freq = Counter()
        for _, row in long_df.iterrows():
            long_freq.update(row['main_numbers'])
        
        # Identify hot/cold numbers
        features['short_term_hot'] = [num for num, _ in short_freq.most_common(10)]
        features['short_term_cold'] = [num for num, _ in short_freq.most_common()[-10:]]
        
        features['long_term_hot'] = [num for num, _ in long_freq.most_common(10)]
        features['long_term_cold'] = [num for num, _ in long_freq.most_common()[-10:]]
        
        # Calculate momentum score (short-term vs long-term frequency)
        for num in range(self.main_range[0], self.main_range[1] + 1):
            short_count = short_freq.get(num, 0) / short_window
            long_count = long_freq.get(num, 0) / len(long_df)
            
            # Positive momentum = heating up, negative = cooling down
            features['momentum_score'][num] = short_count - long_count
        
        return features
    
    def create_feature_vector(self, features: Dict, target_numbers: Set[int]) -> np.ndarray:
        """
        Convert feature dictionary into numerical vector for ML models
        
        Args:
            features: Feature dictionary from extract_all_features()
            target_numbers: Set of numbers to create features for
        
        Returns:
            NumPy array with feature vector
        """
        feature_vector = []
        
        for num in sorted(target_numbers):
            num_features = [
                features.get('temporal_main_freq', {}).get(num, 0),
                features.get('recency_scores', {}).get(num, 0),
                features.get('current_gaps', {}).get(num, 0),
                features.get('avg_historical_gaps', {}).get(num, 0),
                features.get('gap_momentum', {}).get(num, 0),
                features.get('carry_over_rate', {}).get(num, 0),
                features.get('momentum_score', {}).get(num, 0),
                1 if num in features.get('short_term_hot', []) else 0,
                1 if num in features.get('long_term_hot', []) else 0,
                len(features.get('number_associations', {}).get(num, []))
            ]
            feature_vector.extend(num_features)
        
        return np.array(feature_vector)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    # Test feature engineering
    print("Feature engineering module ready for use")
