#!/usr/bin/env python3
"""
Near-Miss Learning System for Lottery Prediction Enhancement
Analyzes predictions that were close to correct and learns from these patterns
"""

import os
import json
import logging
from datetime import datetime
from typing import List, Dict, Any, Tuple
import psycopg2
from google import genai
from google.genai import types

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize Gemini client
client = genai.Client(api_key=os.environ.get("GOOGLE_API_KEY_SNAP_LOTTERY"))

class NearMissLearningSystem:
    """Advanced system to learn from near-miss predictions and improve accuracy"""
    
    def __init__(self):
        self.connection_string = os.environ.get('DATABASE_URL')
    
    def analyze_near_misses(self, predicted: List[int], actual: List[int], threshold: int = 3) -> Dict[str, Any]:
        """
        Analyze how close predicted numbers were to actual results
        threshold: maximum distance to consider a "near miss"
        """
        near_misses = []
        distance_analysis = {}
        
        for pred_num in predicted:
            min_distance = float('inf')
            closest_actual = None
            
            for actual_num in actual:
                distance = abs(pred_num - actual_num)
                if distance < min_distance:
                    min_distance = distance
                    closest_actual = actual_num
            
            if min_distance <= threshold:
                near_misses.append({
                    'predicted': pred_num,
                    'closest_actual': closest_actual,
                    'distance': min_distance
                })
            
            distance_analysis[pred_num] = {
                'closest_actual': closest_actual,
                'distance': min_distance,
                'is_near_miss': min_distance <= threshold
            }
        
        # Calculate overall near-miss score
        total_distance = sum(analysis['distance'] for analysis in distance_analysis.values())
        avg_distance = total_distance / len(predicted)
        
        # Count how many were very close (1-2 spots)
        very_close_count = sum(1 for analysis in distance_analysis.values() 
                              if analysis['distance'] <= 2)
        close_count = sum(1 for analysis in distance_analysis.values() 
                         if analysis['distance'] <= threshold)
        
        return {
            'near_misses': near_misses,
            'distance_analysis': distance_analysis,
            'avg_distance': round(avg_distance, 2),
            'very_close_count': very_close_count,  # Within 1-2 numbers
            'close_count': close_count,  # Within threshold
            'near_miss_score': round((close_count / len(predicted)) * 100, 2),
            'precision_score': round((very_close_count / len(predicted)) * 100, 2)
        }
    
    def extract_near_miss_patterns(self, game_type: str, days_back: int = 30) -> List[Dict]:
        """Extract patterns from recent predictions that were close but not exact"""
        try:
            with psycopg2.connect(self.connection_string) as conn:
                with conn.cursor() as cur:
                    # Get recent predictions with their results
                    cur.execute("""
                        SELECT 
                            p.predicted_numbers,
                            p.confidence_score,
                            p.created_at,
                            r.main_numbers as actual_numbers,
                            r.draw_date
                        FROM lottery_predictions p
                        JOIN lottery_results r ON p.linked_draw_id = r.id  
                        WHERE p.game_type = %s 
                            AND p.created_at >= NOW() - INTERVAL '%s days'
                            AND r.main_numbers IS NOT NULL
                        ORDER BY r.draw_date DESC
                    """, (game_type, days_back))
                    
                    predictions = cur.fetchall()
                    patterns = []
                    
                    for pred_nums, confidence, pred_date, actual_nums, draw_date in predictions:
                        if pred_nums and actual_nums:
                            analysis = self.analyze_near_misses(pred_nums, actual_nums)
                            
                            # Only include predictions with good near-miss scores
                            if analysis['near_miss_score'] >= 40:  # At least 40% were close
                                patterns.append({
                                    'predicted': pred_nums,
                                    'actual': actual_nums,
                                    'analysis': analysis,
                                    'confidence': confidence,
                                    'prediction_date': pred_date,
                                    'draw_date': draw_date
                                })
                    
                    return patterns
        except Exception as e:
            logger.error(f"Error extracting patterns: {e}")
            return []
    
    def generate_adjustment_vector(self, near_miss_patterns: List[Dict]) -> Dict[int, float]:
        """
        Generate adjustment factors based on consistent near-miss patterns
        Returns a dictionary of number -> adjustment_factor
        """
        adjustment_factors = {}
        
        for pattern in near_miss_patterns:
            for pred_num, analysis in pattern['analysis']['distance_analysis'].items():
                if analysis['is_near_miss']:
                    # Calculate adjustment direction and strength
                    actual_num = analysis['closest_actual']
                    distance = analysis['distance']
                    direction = 1 if actual_num > pred_num else -1
                    
                    # Stronger adjustment for consistent patterns
                    strength = 1.0 / (distance + 1)  # Closer = stronger adjustment
                    
                    if pred_num not in adjustment_factors:
                        adjustment_factors[pred_num] = []
                    
                    adjustment_factors[pred_num].append({
                        'direction': direction,
                        'strength': strength,
                        'target': actual_num
                    })
        
        # Average the adjustments for each number
        final_adjustments = {}
        for num, adjustments in adjustment_factors.items():
            avg_direction = sum(adj['direction'] for adj in adjustments) / len(adjustments)
            avg_strength = sum(adj['strength'] for adj in adjustments) / len(adjustments)
            
            final_adjustments[num] = {
                'direction': avg_direction,
                'strength': avg_strength,
                'frequency': len(adjustments)
            }
        
        return final_adjustments
    
    def apply_near_miss_learning(self, base_prediction: List[int], adjustment_factors: Dict, 
                                game_range: Tuple[int, int]) -> List[int]:
        """
        Apply near-miss learning to adjust base prediction
        """
        adjusted_prediction = []
        min_num, max_num = game_range
        
        for num in base_prediction:
            adjusted_num = num
            
            if num in adjustment_factors:
                factor = adjustment_factors[num]
                # Apply adjustment based on learned patterns
                adjustment = factor['direction'] * factor['strength'] * 2  # Scale factor
                adjusted_num = round(num + adjustment)
                
                # Keep within valid range
                adjusted_num = max(min_num, min(max_num, adjusted_num))
            
            adjusted_prediction.append(adjusted_num)
        
        # Ensure no duplicates and sort
        adjusted_prediction = sorted(list(set(adjusted_prediction)))
        
        # If we lost numbers due to duplicates, fill gaps intelligently
        while len(adjusted_prediction) < len(base_prediction):
            # Find a number close to the adjustment patterns
            for candidate in range(min_num, max_num + 1):
                if candidate not in adjusted_prediction:
                    adjusted_prediction.append(candidate)
                    break
        
        return sorted(adjusted_prediction[:len(base_prediction)])
    
    def generate_ai_insights_on_near_misses(self, patterns: List[Dict]) -> str:
        """Use Gemini AI to analyze near-miss patterns and provide insights"""
        try:
            if not patterns:
                return "No near-miss patterns found in recent predictions."
            
            # Prepare data for AI analysis
            pattern_summary = []
            for pattern in patterns[:5]:  # Limit to recent 5 patterns
                pattern_summary.append({
                    'predicted': pattern['predicted'],
                    'actual': pattern['actual'],
                    'near_miss_score': pattern['analysis']['near_miss_score'],
                    'precision_score': pattern['analysis']['precision_score'],
                    'avg_distance': pattern['analysis']['avg_distance']
                })
            
            prompt = f"""Analyze these lottery prediction near-miss patterns and provide AI insights:

{json.dumps(pattern_summary, indent=2)}

The predictions were consistently close (1-2 spots off) but didn't match exactly. 

Provide insights on:
1. What patterns do you see in the near-misses?
2. Are there consistent directional biases (numbers tend to be higher/lower than predicted)?
3. Which number ranges show the best near-miss performance?
4. What adjustments would improve exact match accuracy?
5. Are there cyclical patterns in the close predictions?

Respond with actionable insights in JSON format:
{{
  "pattern_insights": "description of observed patterns",
  "directional_bias": "analysis of consistent over/under predictions",
  "best_performing_ranges": "number ranges with good near-miss performance",
  "recommended_adjustments": "specific adjustment strategies",
  "confidence_factors": "what increases prediction confidence"
}}"""

            response = client.models.generate_content(
                model="gemini-2.5-pro",
                contents=prompt
            )
            
            return response.text if response.text else "AI analysis unavailable"
            
        except Exception as e:
            logger.error(f"AI insight generation failed: {e}")
            return f"AI analysis failed: {str(e)}"

def test_near_miss_system():
    """Test the near-miss learning system with sample data"""
    system = NearMissLearningSystem()
    
    # Test with sample near-miss data
    predicted = [4, 9, 22, 30, 33]  # Example close prediction
    actual = [5, 8, 21, 31, 34]     # Actual result (1-2 spots off each)
    
    analysis = system.analyze_near_misses(predicted, actual)
    
    print("🎯 Near-Miss Analysis Results:")
    print(f"Average Distance: {analysis['avg_distance']}")
    print(f"Very Close Count (1-2 spots): {analysis['very_close_count']}/5")
    print(f"Near-Miss Score: {analysis['near_miss_score']}%")
    print(f"Precision Score: {analysis['precision_score']}%")
    
    print("\nDetailed Analysis:")
    for pred_num, details in analysis['distance_analysis'].items():
        print(f"  Predicted {pred_num} → Closest actual {details['closest_actual']} (distance: {details['distance']})")
    
    return analysis

if __name__ == "__main__":
    test_near_miss_system()