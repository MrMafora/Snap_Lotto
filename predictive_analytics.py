"""
Predictive Analytics Engine for Lottery Data
Phase 4 Implementation - Advanced Pattern Recognition and Predictions
"""

import numpy as np
import logging
import json
from datetime import datetime, timedelta
from collections import Counter, defaultdict
from sklearn.ensemble import RandomForestRegressor
from sklearn.linear_model import LinearRegression
from sklearn.preprocessing import StandardScaler
from models import db, LotteryResult
from sqlalchemy import text

logger = logging.getLogger(__name__)

class LotteryPredictor:
    """Advanced lottery number prediction using machine learning"""
    
    def __init__(self):
        self.models = {}
        self.scalers = {}
        self.pattern_cache = {}
        
    def analyze_historical_patterns(self, lottery_type, days_back=365):
        """Analyze historical patterns for a specific lottery type"""
        try:
            # Get historical data
            cutoff_date = datetime.now().date() - timedelta(days=days_back)
            
            query = text("""
                SELECT main_numbers, bonus_numbers, draw_date, draw_number
                FROM lottery_result 
                WHERE lottery_type = :lottery_type 
                AND draw_date >= :cutoff_date
                ORDER BY draw_date DESC
            """)
            
            results = db.session.execute(query, {
                'lottery_type': lottery_type,
                'cutoff_date': cutoff_date
            }).fetchall()
            
            if not results:
                return None
            
            patterns = {
                'frequency_analysis': self._analyze_frequency(results),
                'sequence_patterns': self._analyze_sequences(results),
                'gap_analysis': self._analyze_gaps(results),
                'seasonal_trends': self._analyze_seasonal_trends(results),
                'prediction_scores': self._generate_predictions(results, lottery_type)
            }
            
            logger.info(f"Analyzed {len(results)} historical draws for {lottery_type}")
            return patterns
            
        except Exception as e:
            logger.error(f"Error analyzing patterns for {lottery_type}: {e}")
            return None
    
    def _analyze_frequency(self, results):
        """Analyze number frequency patterns"""
        all_numbers = []
        
        for result in results:
            # Parse main numbers
            if result.main_numbers:
                try:
                    numbers = json.loads(result.main_numbers.replace("'", '"'))
                    all_numbers.extend(numbers)
                except:
                    continue
            
            # Parse bonus numbers
            if result.bonus_numbers:
                try:
                    bonus = json.loads(result.bonus_numbers.replace("'", '"'))
                    if isinstance(bonus, list):
                        all_numbers.extend(bonus)
                    elif isinstance(bonus, int):
                        all_numbers.append(bonus)
                except:
                    continue
        
        frequency = Counter(all_numbers)
        
        return {
            'most_frequent': frequency.most_common(10),
            'least_frequent': frequency.most_common()[-10:],
            'average_frequency': np.mean(list(frequency.values())) if frequency else 0,
            'frequency_distribution': dict(frequency)
        }
    
    def _analyze_sequences(self, results):
        """Analyze number sequence patterns"""
        sequences = []
        consecutive_pairs = Counter()
        
        for result in results:
            if result.main_numbers:
                try:
                    numbers = json.loads(result.main_numbers.replace("'", '"'))
                    if isinstance(numbers, list) and len(numbers) > 1:
                        sorted_numbers = sorted(numbers)
                        sequences.append(sorted_numbers)
                        
                        # Find consecutive pairs
                        for i in range(len(sorted_numbers) - 1):
                            if sorted_numbers[i+1] - sorted_numbers[i] == 1:
                                consecutive_pairs[(sorted_numbers[i], sorted_numbers[i+1])] += 1
                except:
                    continue
        
        return {
            'consecutive_pairs': consecutive_pairs.most_common(10),
            'sequence_patterns': self._find_common_sequences(sequences),
            'gap_patterns': self._analyze_number_gaps(sequences)
        }
    
    def _analyze_gaps(self, results):
        """Analyze gaps between number draws"""
        number_draws = defaultdict(list)
        
        for i, result in enumerate(results):
            if result.main_numbers:
                try:
                    numbers = json.loads(result.main_numbers.replace("'", '"'))
                    for num in numbers:
                        number_draws[num].append(i)
                except:
                    continue
        
        gap_analysis = {}
        for number, draws in number_draws.items():
            if len(draws) > 1:
                gaps = [draws[i] - draws[i+1] for i in range(len(draws)-1)]
                gap_analysis[number] = {
                    'avg_gap': np.mean(gaps),
                    'min_gap': min(gaps),
                    'max_gap': max(gaps),
                    'last_seen': draws[0] if draws else None
                }
        
        return gap_analysis
    
    def _analyze_seasonal_trends(self, results):
        """Analyze seasonal and temporal trends"""
        trends = {
            'day_of_week': defaultdict(list),
            'month': defaultdict(list),
            'quarter': defaultdict(list)
        }
        
        for result in results:
            if result.draw_date and result.main_numbers:
                try:
                    numbers = json.loads(result.main_numbers.replace("'", '"'))
                    date = result.draw_date
                    
                    trends['day_of_week'][date.weekday()].extend(numbers)
                    trends['month'][date.month].extend(numbers)
                    trends['quarter'][(date.month - 1) // 3 + 1].extend(numbers)
                    
                except:
                    continue
        
        # Calculate frequency by time period
        seasonal_patterns = {}
        for period, data in trends.items():
            seasonal_patterns[period] = {}
            for time_unit, numbers in data.items():
                freq = Counter(numbers)
                seasonal_patterns[period][time_unit] = freq.most_common(5)
        
        return seasonal_patterns
    
    def _generate_predictions(self, results, lottery_type):
        """Generate ML-based predictions"""
        try:
            # Prepare training data
            X, y = self._prepare_training_data(results)
            
            if len(X) < 10:  # Need minimum data
                return {'error': 'Insufficient data for predictions'}
            
            # Train model
            model = RandomForestRegressor(n_estimators=100, random_state=42)
            scaler = StandardScaler()
            
            X_scaled = scaler.fit_transform(X)
            model.fit(X_scaled, y)
            
            # Generate predictions
            last_features = X_scaled[-1:] 
            predictions = model.predict(last_features)[0]
            
            # Convert to lottery numbers
            predicted_numbers = self._convert_to_lottery_numbers(predictions, lottery_type)
            
            # Calculate confidence scores
            feature_importance = model.feature_importances_
            confidence = np.mean(feature_importance) * 100
            
            return {
                'predicted_numbers': predicted_numbers,
                'confidence_score': round(confidence, 2),
                'model_type': 'Random Forest',
                'training_samples': len(X)
            }
            
        except Exception as e:
            logger.error(f"Error generating predictions: {e}")
            return {'error': str(e)}
    
    def _prepare_training_data(self, results):
        """Prepare data for machine learning"""
        X, y = [], []
        
        for i, result in enumerate(results[:-1]):  # Exclude last for target
            try:
                # Features: current draw numbers and metadata
                current_numbers = json.loads(result.main_numbers.replace("'", '"'))
                
                # Target: next draw numbers  
                next_result = results[i+1]
                next_numbers = json.loads(next_result.main_numbers.replace("'", '"'))
                
                # Create feature vector
                features = []
                features.extend(current_numbers)  # Current numbers
                features.append(len(current_numbers))  # Count of numbers
                features.append(sum(current_numbers))  # Sum of numbers
                features.append(max(current_numbers) - min(current_numbers))  # Range
                features.append(result.draw_date.weekday())  # Day of week
                
                # Pad to fixed length
                while len(features) < 20:
                    features.append(0)
                
                X.append(features[:20])
                y.append(next_numbers[:6])  # Predict first 6 numbers
                
            except:
                continue
        
        return np.array(X), np.array(y)
    
    def _convert_to_lottery_numbers(self, predictions, lottery_type):
        """Convert ML predictions to valid lottery numbers"""
        # Round and constrain to valid lottery number ranges
        if lottery_type in ['LOTTO', 'LOTTO PLUS 1', 'LOTTO PLUS 2']:
            # Numbers 1-52
            numbers = [max(1, min(52, int(round(p)))) for p in predictions]
        elif lottery_type in ['PowerBall', 'POWERBALL PLUS']:
            # Numbers 1-45 for main balls
            numbers = [max(1, min(45, int(round(p)))) for p in predictions[:5]]
            # PowerBall 1-20
            if len(predictions) > 5:
                numbers.append(max(1, min(20, int(round(predictions[5])))))
        else:  # Daily Lotto
            # Numbers 1-36
            numbers = [max(1, min(36, int(round(p)))) for p in predictions]
        
        # Remove duplicates and sort
        unique_numbers = sorted(list(set(numbers)))
        
        # Ensure we have the right count
        target_count = 6 if lottery_type.startswith('LOTTO') else 5
        if lottery_type == 'DAILY LOTTO':
            target_count = 5
        
        while len(unique_numbers) < target_count:
            # Fill missing numbers
            range_max = 52 if lottery_type.startswith('LOTTO') else 45
            if lottery_type == 'DAILY LOTTO':
                range_max = 36
                
            for num in range(1, range_max + 1):
                if num not in unique_numbers:
                    unique_numbers.append(num)
                    if len(unique_numbers) >= target_count:
                        break
        
        return sorted(unique_numbers[:target_count])
    
    def _find_common_sequences(self, sequences):
        """Find common number sequences"""
        sequence_patterns = Counter()
        
        for seq in sequences:
            if len(seq) >= 3:
                # Find 3-number patterns
                for i in range(len(seq) - 2):
                    pattern = tuple(seq[i:i+3])
                    sequence_patterns[pattern] += 1
        
        return sequence_patterns.most_common(10)
    
    def _analyze_number_gaps(self, sequences):
        """Analyze gaps between numbers in draws"""
        gap_patterns = Counter()
        
        for seq in sequences:
            if len(seq) >= 2:
                gaps = [seq[i+1] - seq[i] for i in range(len(seq)-1)]
                for gap in gaps:
                    gap_patterns[gap] += 1
        
        return gap_patterns.most_common(10)

class AlertSystem:
    """Custom alert system for lottery events"""
    
    def __init__(self):
        self.alert_rules = {}
        self.notifications = []
    
    def add_alert_rule(self, rule_id, lottery_type, condition, threshold):
        """Add a new alert rule"""
        self.alert_rules[rule_id] = {
            'lottery_type': lottery_type,
            'condition': condition,  # 'jackpot_high', 'number_frequency', 'gap_exceeded'
            'threshold': threshold,
            'active': True,
            'created_at': datetime.now()
        }
    
    def check_alerts(self, lottery_data):
        """Check if any alerts should be triggered"""
        triggered_alerts = []
        
        for rule_id, rule in self.alert_rules.items():
            if not rule['active']:
                continue
            
            if self._evaluate_condition(rule, lottery_data):
                alert = {
                    'rule_id': rule_id,
                    'lottery_type': rule['lottery_type'],
                    'condition': rule['condition'],
                    'message': self._generate_alert_message(rule, lottery_data),
                    'timestamp': datetime.now(),
                    'data': lottery_data
                }
                triggered_alerts.append(alert)
                self.notifications.append(alert)
        
        return triggered_alerts
    
    def _evaluate_condition(self, rule, data):
        """Evaluate if alert condition is met"""
        condition = rule['condition']
        threshold = rule['threshold']
        
        if condition == 'jackpot_high':
            return data.get('jackpot_amount', 0) > threshold
        elif condition == 'number_frequency':
            # Check if predicted numbers have high frequency
            freq_score = data.get('frequency_score', 0)
            return freq_score > threshold
        elif condition == 'gap_exceeded':
            # Check if number hasn't appeared for too long
            max_gap = data.get('max_gap', 0)
            return max_gap > threshold
        
        return False
    
    def _generate_alert_message(self, rule, data):
        """Generate human-readable alert message"""
        condition = rule['condition']
        lottery_type = rule['lottery_type']
        
        if condition == 'jackpot_high':
            amount = data.get('jackpot_amount', 0)
            return f"{lottery_type} jackpot reached R{amount:,} - above threshold!"
        elif condition == 'number_frequency':
            return f"High frequency numbers detected in {lottery_type} predictions"
        elif condition == 'gap_exceeded':
            return f"Numbers in {lottery_type} showing unusual gap patterns"
        
        return f"Alert triggered for {lottery_type}"

# Global instances
predictor = LotteryPredictor()
alert_system = AlertSystem()

def get_lottery_predictions(lottery_type, days_back=365):
    """Get predictions for a specific lottery type"""
    return predictor.analyze_historical_patterns(lottery_type, days_back)

def setup_default_alerts():
    """Setup default alert rules"""
    # High jackpot alerts
    alert_system.add_alert_rule('lotto_jackpot', 'LOTTO', 'jackpot_high', 100000000)  # R100M
    alert_system.add_alert_rule('powerball_jackpot', 'PowerBall', 'jackpot_high', 200000000)  # R200M
    
    # Frequency alerts
    alert_system.add_alert_rule('lotto_frequency', 'LOTTO', 'number_frequency', 0.8)
    alert_system.add_alert_rule('powerball_frequency', 'PowerBall', 'number_frequency', 0.8)
    
    logger.info("Default alert rules configured")