#!/usr/bin/env python3
"""
Neural Network Ensemble for Lottery Prediction
Implements Gradient Boosting, Random Forest, and Neural Networks
with dynamic ensemble weights and calibrated confidence scoring
"""

import os
import numpy as np
import pandas as pd
import logging
from typing import Dict, List, Tuple, Optional
from collections import Counter
import json
import pickle
from datetime import datetime

# Scikit-learn imports
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.preprocessing import StandardScaler
from sklearn.multioutput import MultiOutputClassifier

# Neural network imports  
try:
    from sklearn.neural_network import MLPClassifier
    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False
    logging.warning("scikit-learn not fully available")

from ml_feature_engineering import LotteryFeatureEngineer
from ml_training_infrastructure import LotteryMLTrainer

logger = logging.getLogger(__name__)

class NeuralEnsemble:
    """
    Ensemble of machine learning models for lottery prediction
    with dynamic weighting and continuous learning
    """
    
    def __init__(self, game_type: str, game_config: Dict):
        self.game_type = game_type
        self.game_config = game_config
        self.feature_engineer = LotteryFeatureEngineer(game_config)
        self.trainer = LotteryMLTrainer()
        
        # Model components
        self.models = {
            'random_forest': None,
            'gradient_boosting': None,
            'neural_network': None
        }
        
        self.model_weights = {
            'random_forest': 0.35,
            'gradient_boosting': 0.40,
            'neural_network': 0.25
        }
        
        self.scaler = StandardScaler()
        self.is_trained = False
        
        # Performance tracking
        self.performance_history = {
            'random_forest': [],
            'gradient_boosting': [],
            'neural_network': []
        }
    
    def prepare_training_data(self, historical_df: pd.DataFrame) -> Tuple[np.ndarray, np.ndarray]:
        """
        Prepare training data from historical draws
        
        Args:
            historical_df: DataFrame with historical lottery draws
        
        Returns:
            Tuple of (X_train, y_train) arrays
        """
        X_train = []
        y_train = []
        
        # Use sliding window approach - adaptive based on available data
        window_size = min(15, len(historical_df) // 2)  # Use 15 draws or half available, whichever is smaller
        
        if len(historical_df) < window_size + 5:
            logger.warning(f"Insufficient data: {len(historical_df)} draws, need at least {window_size + 5}")
            return np.array([]), np.array([])
        
        for i in range(window_size, len(historical_df)):
            try:
                # Training window
                train_window = historical_df.iloc[i-window_size:i]
                
                # Extract features from training window
                features = self.feature_engineer.extract_all_features(train_window)
            except Exception as e:
                logger.warning(f"Feature extraction failed for window {i-window_size}:{i}: {e}")
                continue
            
            # Create feature vector for each number
            number_range = range(self.game_config['main_range'][0], 
                               self.game_config['main_range'][1] + 1)
            
            feature_vector = []
            for num in number_range:
                num_features = [
                    features.get('temporal_main_freq', {}).get(num, 0),
                    features.get('recency_scores', {}).get(num, 0),
                    features.get('current_gaps', {}).get(num, 0) / 100.0,  # Normalize
                    features.get('avg_historical_gaps', {}).get(num, 0) / 100.0,
                    features.get('gap_momentum', {}).get(num, 0),
                    features.get('carry_over_rate', {}).get(num, 0),
                    features.get('momentum_score', {}).get(num, 0),
                    1 if num in features.get('short_term_hot', []) else 0,
                    1 if num in features.get('long_term_hot', []) else 0,
                    len(features.get('number_associations', {}).get(num, [])) / 10.0  # Normalize
                ]
                feature_vector.extend(num_features)
            
            X_train.append(feature_vector)
            
            # Target: which numbers appeared in next draw
            target_numbers = historical_df.iloc[i]['main_numbers']
            target_vector = np.zeros(len(number_range))
            for num in target_numbers:
                # Validate number is in valid range
                if num < self.game_config['main_range'][0] or num > self.game_config['main_range'][1]:
                    logger.warning(f"Invalid number {num} for {self.game_type}, skipping")
                    continue
                idx = num - self.game_config['main_range'][0]
                if 0 <= idx < len(target_vector):
                    target_vector[idx] = 1
            
            y_train.append(target_vector)
        
        return np.array(X_train), np.array(y_train)
    
    def train_models(self, historical_df: pd.DataFrame) -> bool:
        """
        Train all ensemble models on historical data
        
        Args:
            historical_df: DataFrame with historical lottery draws
        
        Returns:
            True if training successful
        """
        try:
            logger.info(f"🧠 Training ensemble models for {self.game_type}...")
            
            if len(historical_df) < 30:
                logger.warning(f"Insufficient data for training: {len(historical_df)} draws")
                return False
            
            # Prepare training data
            X_train, y_train = self.prepare_training_data(historical_df)
            
            if len(X_train) == 0:
                logger.warning("No training data generated")
                return False
            
            logger.info(f"Training on {len(X_train)} samples with {X_train.shape[1]} features")
            
            # Scale features
            X_train_scaled = self.scaler.fit_transform(X_train)
            
            # Train Random Forest
            logger.info("Training Random Forest...")
            self.models['random_forest'] = MultiOutputClassifier(
                RandomForestClassifier(
                    n_estimators=100,
                    max_depth=15,
                    min_samples_split=5,
                    random_state=42,
                    n_jobs=-1
                )
            )
            self.models['random_forest'].fit(X_train_scaled, y_train)
            logger.info("✅ Random Forest trained")
            
            # Train Gradient Boosting
            logger.info("Training Gradient Boosting...")
            self.models['gradient_boosting'] = MultiOutputClassifier(
                GradientBoostingClassifier(
                    n_estimators=100,
                    max_depth=5,
                    learning_rate=0.1,
                    random_state=42
                )
            )
            self.models['gradient_boosting'].fit(X_train_scaled, y_train)
            logger.info("✅ Gradient Boosting trained")
            
            # Train Neural Network (if available)
            if SKLEARN_AVAILABLE:
                logger.info("Training Neural Network...")
                self.models['neural_network'] = MultiOutputClassifier(
                    MLPClassifier(
                        hidden_layer_sizes=(100, 50, 25),
                        activation='relu',
                        solver='adam',
                        learning_rate='adaptive',
                        max_iter=300,
                        random_state=42
                    )
                )
                self.models['neural_network'].fit(X_train_scaled, y_train)
                logger.info("✅ Neural Network trained")
            else:
                logger.warning("Neural Network not available")
                self.model_weights['neural_network'] = 0
                # Redistribute weights
                self.model_weights['random_forest'] = 0.50
                self.model_weights['gradient_boosting'] = 0.50
            
            self.is_trained = True
            logger.info(f"🎉 Ensemble training complete for {self.game_type}")
            
            return True
            
        except Exception as e:
            logger.error(f"Error training ensemble: {e}")
            return False
    
    def predict(self, historical_df: pd.DataFrame) -> Optional[Dict]:
        """
        Generate prediction using ensemble models
        
        Args:
            historical_df: DataFrame with recent historical draws
        
        Returns:
            Dictionary with prediction results
        """
        try:
            if not self.is_trained:
                logger.warning("Models not trained yet")
                return None
            
            # Extract features from recent history
            features = self.feature_engineer.extract_all_features(historical_df)
            
            # Create feature vector
            number_range = range(self.game_config['main_range'][0], 
                               self.game_config['main_range'][1] + 1)
            
            feature_vector = []
            for num in number_range:
                num_features = [
                    features.get('temporal_main_freq', {}).get(num, 0),
                    features.get('recency_scores', {}).get(num, 0),
                    features.get('current_gaps', {}).get(num, 0) / 100.0,
                    features.get('avg_historical_gaps', {}).get(num, 0) / 100.0,
                    features.get('gap_momentum', {}).get(num, 0),
                    features.get('carry_over_rate', {}).get(num, 0),
                    features.get('momentum_score', {}).get(num, 0),
                    1 if num in features.get('short_term_hot', []) else 0,
                    1 if num in features.get('long_term_hot', []) else 0,
                    len(features.get('number_associations', {}).get(num, [])) / 10.0
                ]
                feature_vector.extend(num_features)
            
            X_pred = np.array([feature_vector])
            X_pred_scaled = self.scaler.transform(X_pred)
            
            # Get predictions from each model
            model_predictions = {}
            model_probabilities = {}
            
            for model_name, model in self.models.items():
                if model is None:
                    continue
                
                # Get probability predictions
                try:
                    probs = model.predict_proba(X_pred_scaled)
                    # Extract probability of class 1 (number being drawn) for each number
                    number_probs = {}
                    for idx, num in enumerate(number_range):
                        # Get probability for this number being drawn (class 1)
                        if hasattr(probs[idx], 'shape') and len(probs[idx].shape) > 1:
                            number_probs[num] = probs[idx][0][1]  # Probability of class 1
                        else:
                            number_probs[num] = probs[idx][0]
                    
                    model_probabilities[model_name] = number_probs
                    
                    # Select top numbers based on probabilities
                    top_numbers = sorted(number_probs.items(), 
                                       key=lambda x: x[1], 
                                       reverse=True)[:self.game_config['main_count']]
                    model_predictions[model_name] = [num for num, _ in top_numbers]
                    
                except Exception as e:
                    logger.warning(f"Error getting predictions from {model_name}: {e}")
                    continue
            
            if not model_predictions:
                logger.warning("No valid predictions from ensemble")
                return None
            
            # Weighted ensemble voting
            number_scores = {}
            for num in number_range:
                score = 0.0
                for model_name, probs in model_probabilities.items():
                    weight = self.model_weights.get(model_name, 0)
                    score += probs.get(num, 0) * weight
                number_scores[num] = score
            
            # Select top numbers
            top_numbers = sorted(number_scores.items(), 
                               key=lambda x: x[1], 
                               reverse=True)[:self.game_config['main_count']]
            main_numbers = sorted([num for num, _ in top_numbers])
            
            # Calculate confidence based on model agreement and score strength
            confidence = self.calculate_ensemble_confidence(
                main_numbers, model_predictions, number_scores
            )
            
            # Generate reasoning
            reasoning = self.generate_reasoning(
                main_numbers, model_predictions, features, confidence
            )
            
            return {
                'main_numbers': main_numbers,
                'bonus_numbers': [],  # Handle separately if needed
                'confidence': confidence,
                'reasoning': reasoning,
                'model_predictions': model_predictions,
                'number_scores': number_scores
            }
            
        except Exception as e:
            logger.error(f"Error generating ensemble prediction: {e}")
            return None
    
    def calculate_ensemble_confidence(self, selected_numbers: List[int],
                                     model_predictions: Dict,
                                     number_scores: Dict) -> float:
        """
        Calculate calibrated confidence score based on ensemble agreement
        """
        # Model agreement: how many models selected each number
        agreement_scores = []
        for num in selected_numbers:
            agreement = sum(1 for pred in model_predictions.values() if num in pred)
            agreement_scores.append(agreement / len(model_predictions))
        
        avg_agreement = np.mean(agreement_scores)
        
        # Score strength: how confident were the models
        avg_score = np.mean([number_scores[num] for num in selected_numbers])
        
        # Realistic base confidence for lottery (2-4% range)
        base_confidence = 2.5
        
        # Add bonuses based on model agreement and strength
        agreement_bonus = avg_agreement * 1.0  # Max 1.0% bonus
        strength_bonus = avg_score * 0.5  # Max ~0.5% bonus
        
        confidence = base_confidence + agreement_bonus + strength_bonus
        
        # Cap at realistic lottery prediction range (2.0-4.5%)
        confidence = max(2.0, min(4.5, round(confidence, 1)))
        
        return confidence
    
    def generate_reasoning(self, selected_numbers: List[int],
                          model_predictions: Dict,
                          features: Dict,
                          confidence: float) -> str:
        """Generate human-readable reasoning for the prediction"""
        reasoning_parts = []
        
        # Model agreement
        model_names = list(model_predictions.keys())
        reasoning_parts.append(f"Ensemble of {len(model_names)} ML models")
        
        # Feature insights
        hot_count = sum(1 for n in selected_numbers if n in features.get('short_term_hot', []))
        if hot_count > 0:
            reasoning_parts.append(f"{hot_count} hot numbers selected")
        
        # Pattern insights
        high_affinity = features.get('high_affinity_pairs', [])
        if high_affinity:
            reasoning_parts.append(f"Co-occurrence patterns detected")
        
        reasoning_parts.append(f"{confidence}% confidence based on model agreement")
        
        return " | ".join(reasoning_parts)
    
    def update_weights(self, actual_numbers: List[int], 
                      model_predictions: Dict) -> None:
        """
        Update model weights based on prediction accuracy (continuous learning)
        """
        try:
            actual_set = set(actual_numbers)
            
            # Calculate accuracy for each model
            model_accuracies = {}
            for model_name, predicted in model_predictions.items():
                predicted_set = set(predicted)
                matches = len(actual_set & predicted_set)
                accuracy = matches / self.game_config['main_count']
                model_accuracies[model_name] = accuracy
                
                # Track in performance history
                self.performance_history[model_name].append(accuracy)
                
                # Keep only last 20 results
                if len(self.performance_history[model_name]) > 20:
                    self.performance_history[model_name] = self.performance_history[model_name][-20:]
            
            # Recalculate weights based on recent performance
            if all(len(hist) >= 5 for hist in self.performance_history.values()):
                total_performance = 0
                avg_performances = {}
                
                for model_name in self.models.keys():
                    if model_name in self.performance_history:
                        avg_perf = np.mean(self.performance_history[model_name][-10:])
                        avg_performances[model_name] = avg_perf
                        total_performance += avg_perf
                
                # Normalize to weights
                if total_performance > 0:
                    for model_name in avg_performances:
                        self.model_weights[model_name] = avg_performances[model_name] / total_performance
                    
                    logger.info(f"Updated ensemble weights: {self.model_weights}")
            
        except Exception as e:
            logger.error(f"Error updating weights: {e}")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    print("Neural Ensemble module ready")
