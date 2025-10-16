#!/usr/bin/env python3
"""
Confidence Calibration System
Learns from actual prediction accuracy to provide better confidence scores
Tracks historical performance and adjusts confidence dynamically
"""

import logging
import psycopg2
import os
import json
from typing import Dict, Optional
from datetime import datetime, timedelta
import numpy as np

logger = logging.getLogger(__name__)


class ConfidenceCalibrator:
    """
    Dynamically calibrates confidence scores based on historical accuracy
    """
    
    def __init__(self):
        self.connection_string = os.environ.get('DATABASE_URL')
        self.performance_cache = {}
    
    def get_historical_accuracy(self, lottery_type: str, days_back: int = 90) -> Dict:
        """
        Get actual prediction accuracy from validated predictions
        
        Returns:
            Dict with accuracy metrics
        """
        try:
            conn = psycopg2.connect(self.connection_string)
            cur = conn.cursor()
            
            # Get validated predictions (where we know the actual results)
            cur.execute('''
                SELECT 
                    main_number_matches,
                    bonus_number_matches,
                    confidence_score,
                    accuracy_percentage,
                    prediction_method,
                    created_at
                FROM lottery_predictions
                WHERE game_type = %s
                  AND validation_status IN ('verified', 'validated')
                  AND created_at >= CURRENT_DATE - make_interval(days => %s)
                ORDER BY created_at DESC
                LIMIT 100
            ''', (lottery_type, days_back))
            
            results = cur.fetchall()
            cur.close()
            conn.close()
            
            if not results:
                logger.info(f"No historical accuracy data for {lottery_type}")
                return {
                    'avg_matches': 0.0,
                    'avg_accuracy': 0.0,
                    'predictions_count': 0,
                    'calibration_needed': False
                }
            
            # Calculate actual performance
            main_matches = []
            accuracies = []
            confidence_scores = []
            
            for main_match, bonus_match, confidence, accuracy, method, created in results:
                if main_match is not None:
                    main_matches.append(main_match)
                if accuracy is not None:
                    accuracies.append(float(accuracy))
                if confidence is not None:
                    confidence_scores.append(float(confidence))
            
            avg_matches = np.mean(main_matches) if main_matches else 0.0
            avg_accuracy = np.mean(accuracies) if accuracies else 0.0
            avg_confidence = np.mean(confidence_scores) if confidence_scores else 0.0
            
            # Check if calibration is needed
            # If actual accuracy is significantly different from predicted confidence
            calibration_needed = abs(avg_accuracy - avg_confidence) > 1.0
            
            metrics = {
                'avg_matches': avg_matches,
                'avg_accuracy': avg_accuracy,
                'avg_confidence': avg_confidence,
                'predictions_count': len(results),
                'calibration_needed': calibration_needed,
                'confidence_error': avg_confidence - avg_accuracy  # Positive = overconfident
            }
            
            logger.info(f"📊 Historical Accuracy for {lottery_type}:")
            logger.info(f"   Avg Matches: {avg_matches:.2f}")
            logger.info(f"   Avg Accuracy: {avg_accuracy:.2f}%")
            logger.info(f"   Avg Confidence: {avg_confidence:.2f}%")
            logger.info(f"   Calibration Error: {metrics['confidence_error']:.2f}%")
            
            return metrics
            
        except Exception as e:
            logger.error(f"Error getting historical accuracy: {e}")
            return {
                'avg_matches': 0.0,
                'avg_accuracy': 0.0,
                'predictions_count': 0,
                'calibration_needed': False
            }
    
    def calibrate_confidence(self, lottery_type: str, raw_confidence: float, 
                           prediction_method: str = 'ensemble') -> float:
        """
        Adjust confidence score based on historical performance
        
        Args:
            lottery_type: Type of lottery
            raw_confidence: Uncalibrated confidence from model
            prediction_method: Which prediction method was used
        
        Returns:
            Calibrated confidence score
        """
        try:
            # Get historical accuracy
            metrics = self.get_historical_accuracy(lottery_type)
            
            if metrics['predictions_count'] < 5:
                # Not enough data for calibration, return raw
                logger.info(f"Insufficient calibration data, using raw confidence: {raw_confidence}%")
                return raw_confidence
            
            # Calculate calibration adjustment
            confidence_error = metrics.get('confidence_error', 0.0)
            
            # Adjust confidence down if we've been overconfident
            # Adjust up if we've been underconfident
            calibrated = raw_confidence - (confidence_error * 0.5)  # Use 50% of error for gradual adjustment
            
            # Keep within realistic lottery prediction range (1.5-4.5%)
            calibrated = max(1.5, min(4.5, calibrated))
            
            logger.info(f"🎯 Confidence Calibration for {lottery_type}:")
            logger.info(f"   Raw: {raw_confidence:.2f}%")
            logger.info(f"   Adjustment: {-confidence_error * 0.5:.2f}%")
            logger.info(f"   Calibrated: {calibrated:.2f}%")
            
            return round(calibrated, 1)
            
        except Exception as e:
            logger.error(f"Error calibrating confidence: {e}")
            return raw_confidence
    
    def get_prediction_quality_score(self, lottery_type: str) -> str:
        """
        Get a quality rating for current predictions
        
        Returns:
            Quality score: 'excellent', 'good', 'fair', 'poor', 'insufficient_data'
        """
        try:
            metrics = self.get_historical_accuracy(lottery_type)
            
            if metrics['predictions_count'] < 10:
                return 'insufficient_data'
            
            avg_accuracy = metrics['avg_accuracy']
            
            # Quality thresholds for lottery predictions
            if avg_accuracy >= 3.5:
                return 'excellent'
            elif avg_accuracy >= 2.5:
                return 'good'
            elif avg_accuracy >= 1.5:
                return 'fair'
            else:
                return 'poor'
                
        except Exception as e:
            logger.error(f"Error getting quality score: {e}")
            return 'unknown'
    
    def save_calibration_metrics(self, lottery_type: str, metrics: Dict):
        """Save calibration metrics to database for tracking"""
        try:
            conn = psycopg2.connect(self.connection_string)
            cur = conn.cursor()
            
            # Create calibration metrics table if not exists
            cur.execute('''
                CREATE TABLE IF NOT EXISTS confidence_calibration_metrics (
                    id SERIAL PRIMARY KEY,
                    lottery_type VARCHAR(50) NOT NULL,
                    avg_matches DECIMAL(5,2),
                    avg_accuracy DECIMAL(5,2),
                    avg_confidence DECIMAL(5,2),
                    confidence_error DECIMAL(5,2),
                    predictions_count INTEGER,
                    quality_score VARCHAR(20),
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Insert metrics
            quality = self.get_prediction_quality_score(lottery_type)
            
            cur.execute('''
                INSERT INTO confidence_calibration_metrics 
                (lottery_type, avg_matches, avg_accuracy, avg_confidence, 
                 confidence_error, predictions_count, quality_score)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            ''', (
                lottery_type,
                metrics.get('avg_matches'),
                metrics.get('avg_accuracy'),
                metrics.get('avg_confidence'),
                metrics.get('confidence_error'),
                metrics.get('predictions_count'),
                quality
            ))
            
            conn.commit()
            cur.close()
            conn.close()
            
            logger.info(f"✅ Calibration metrics saved for {lottery_type}")
            
        except Exception as e:
            logger.error(f"Error saving calibration metrics: {e}")


# Global calibrator instance
_calibrator = None

def get_calibrator() -> ConfidenceCalibrator:
    """Get singleton calibrator instance"""
    global _calibrator
    if _calibrator is None:
        _calibrator = ConfidenceCalibrator()
    return _calibrator


def calibrate_prediction_confidence(lottery_type: str, raw_confidence: float, 
                                   prediction_method: str = 'ensemble') -> float:
    """
    Convenience function to calibrate confidence
    
    Usage:
        calibrated_conf = calibrate_prediction_confidence('LOTTO', 3.5, 'ensemble')
    """
    calibrator = get_calibrator()
    return calibrator.calibrate_confidence(lottery_type, raw_confidence, prediction_method)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    # Test calibration
    print("Testing Confidence Calibration...")
    
    calibrator = ConfidenceCalibrator()
    
    for lottery_type in ['LOTTO', 'LOTTO PLUS 1', 'POWERBALL', 'DAILY LOTTO']:
        print(f"\n{'='*60}")
        print(f"Lottery: {lottery_type}")
        
        # Get historical accuracy
        metrics = calibrator.get_historical_accuracy(lottery_type)
        print(f"Historical Accuracy: {metrics['avg_accuracy']:.2f}%")
        print(f"Predictions Count: {metrics['predictions_count']}")
        
        # Test calibration
        raw_conf = 3.5
        calibrated = calibrator.calibrate_confidence(lottery_type, raw_conf)
        print(f"Raw Confidence: {raw_conf}% → Calibrated: {calibrated}%")
        
        # Get quality score
        quality = calibrator.get_prediction_quality_score(lottery_type)
        print(f"Prediction Quality: {quality}")
