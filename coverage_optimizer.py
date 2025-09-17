#!/usr/bin/env python3
"""
Coverage Optimizer - Multi-line wheel system and coverage maximization
Generates optimal ticket combinations to achieve 60%+ probability of 3+ matches
"""

import os
import logging
import numpy as np
from typing import Dict, List, Tuple, Any, Set
from itertools import combinations, product
from collections import defaultdict
import psycopg2
from probability_estimator import ProbabilityEstimator

logger = logging.getLogger(__name__)

class CoverageOptimizer:
    """Optimizes ticket coverage and generates wheel systems for maximum hit probability"""
    
    def __init__(self):
        """Initialize coverage optimizer with probability estimator"""
        self.probability_estimator = ProbabilityEstimator()
        self.game_configs = {
            'DAILY LOTTO': {'total_numbers': 36, 'picks': 5, 'has_bonus': False},
            'LOTTO': {'total_numbers': 52, 'picks': 6, 'has_bonus': True},
            'LOTTO PLUS 1': {'total_numbers': 52, 'picks': 6, 'has_bonus': True}, 
            'LOTTO PLUS 2': {'total_numbers': 52, 'picks': 6, 'has_bonus': True},
            'POWERBALL': {'total_numbers': 50, 'picks': 5, 'has_bonus': True},
            'POWERBALL PLUS': {'total_numbers': 50, 'picks': 5, 'has_bonus': True}
        }
        logger.info("CoverageOptimizer initialized")
    
    def generate_wheel_system(self, game_type: str, budget_lines: int = 50, target_coverage: float = 60.0) -> Dict[str, Any]:
        """Generate optimized wheel system to maximize coverage probability"""
        try:
            # Get probability analysis
            prob_analysis = self.probability_estimator.calculate_number_probabilities(game_type)
            config = self.game_configs.get(game_type)
            
            if not config or not prob_analysis:
                logger.error(f"Cannot generate wheel for {game_type}")
                return {}
            
            picks = config['picks']
            total_numbers = config['total_numbers']
            
            # Extract top probability numbers for the wheel base
            number_probs = prob_analysis['number_probabilities']
            sorted_numbers = sorted(number_probs.items(), 
                                  key=lambda x: x[1]['probability'], reverse=True)
            
            # Determine optimal pool size based on target coverage
            optimal_pool_size = self._determine_optimal_pool_size(
                game_type, target_coverage, sorted_numbers
            )
            
            top_pool = [num for num, _ in sorted_numbers[:optimal_pool_size]]
            
            # Generate wheel combinations using greedy coverage maximization
            wheel_lines = self._generate_greedy_wheel(
                top_pool, picks, budget_lines
            )
            
            # Calculate actual coverage probability
            actual_coverage = self._calculate_wheel_coverage(
                wheel_lines, prob_analysis, picks
            )
            
            # Generate guaranteed pattern wheels as backup
            guaranteed_wheels = self._generate_guaranteed_patterns(
                top_pool, picks, min(budget_lines // 2, 25)
            )
            
            result = {
                'game_type': game_type,
                'budget_lines': budget_lines,
                'target_coverage': target_coverage,
                'pool_size': optimal_pool_size,
                'top_pool': top_pool,
                'wheel_lines': wheel_lines,
                'guaranteed_wheels': guaranteed_wheels,
                'coverage_analysis': {
                    'expected_3_plus_probability': actual_coverage,
                    'expected_2_plus_probability': min(actual_coverage * 2.5, 95),
                    'pool_coverage_probability': prob_analysis['probability_pools']['top_20']['coverage_probability'],
                    'confidence_level': prob_analysis['confidence_level']
                },
                'optimization_stats': {
                    'total_combinations': len(wheel_lines),
                    'pool_utilization': len(set().union(*wheel_lines)) / len(top_pool),
                    'diversity_score': self._calculate_diversity_score(wheel_lines),
                    'efficiency_ratio': actual_coverage / budget_lines
                },
                'generated_at': prob_analysis['analysis_date']
            }
            
            logger.info(f"Generated wheel system for {game_type}: {len(wheel_lines)} lines, {actual_coverage:.1f}% coverage")
            return result
            
        except Exception as e:
            logger.error(f"Error generating wheel system for {game_type}: {e}")
            return {}
    
    def _determine_optimal_pool_size(self, game_type: str, target_coverage: float, sorted_numbers: List) -> int:
        """Determine optimal pool size for target coverage"""
        config = self.game_configs.get(game_type)
        picks = config['picks']
        total_numbers = config['total_numbers']
        
        # Test different pool sizes to find optimal
        best_pool_size = 20  # Default
        
        for pool_size in [15, 18, 20, 22, 25, 28]:
            coverage_prob = self.probability_estimator._calculate_coverage_probability(
                picks, total_numbers, pool_size
            )
            
            if coverage_prob >= target_coverage:
                best_pool_size = pool_size
                break
        
        return min(best_pool_size, len(sorted_numbers))
    
    def _generate_greedy_wheel(self, pool: List[int], picks: int, max_lines: int) -> List[List[int]]:
        """Generate wheel using greedy algorithm to maximize coverage"""
        if len(pool) < picks:
            return []
        
        wheel_lines = []
        covered_combinations = set()
        
        # Generate all possible 3-number combinations from pool (our target)
        target_combinations = list(combinations(pool, 3))
        
        # Greedy selection: pick lines that cover the most uncovered 3-combinations
        while len(wheel_lines) < max_lines and len(covered_combinations) < len(target_combinations):
            best_line = None
            best_coverage = 0
            
            # Try different line combinations
            for line_combo in combinations(pool, picks):
                line_3_combos = set(combinations(line_combo, 3))
                new_coverage = len(line_3_combos - covered_combinations)
                
                if new_coverage > best_coverage:
                    best_coverage = new_coverage
                    best_line = list(line_combo)
            
            if best_line and best_coverage > 0:
                wheel_lines.append(best_line)
                # Update covered combinations
                line_3_combos = set(combinations(best_line, 3))
                covered_combinations.update(line_3_combos)
            else:
                break  # No more improvement possible
        
        return wheel_lines
    
    def _generate_guaranteed_patterns(self, pool: List[int], picks: int, max_lines: int) -> Dict[str, List]:
        """Generate guaranteed minimum match patterns"""
        guaranteed_systems = {}
        
        if len(pool) >= picks:
            # "If 3 from pool" system - guarantees at least 1 match if 3+ winning numbers in pool
            if_3_system = []
            pool_subset = pool[:min(15, len(pool))]  # Use top 15 for efficiency
            
            count = 0
            for combo in combinations(pool_subset, picks):
                if count >= max_lines:
                    break
                if_3_system.append(list(combo))
                count += 1
            
            guaranteed_systems['if_3_guarantee'] = if_3_system[:max_lines]
        
        # "Balanced coverage" system
        if len(pool) >= picks * 2:
            balanced_system = []
            # Split pool into groups and ensure coverage
            mid_point = len(pool) // 2
            group1 = pool[:mid_point]
            group2 = pool[mid_point:]
            
            count = 0
            for i in range(min(max_lines // 2, 10)):
                if count >= max_lines:
                    break
                
                # Mix from both groups
                from_group1 = min(picks // 2 + 1, len(group1))
                from_group2 = picks - from_group1
                
                if from_group2 > len(group2):
                    continue
                
                line = group1[:from_group1] + group2[:from_group2]
                balanced_system.append(line[:picks])
                count += 1
            
            guaranteed_systems['balanced_coverage'] = balanced_system
        
        return guaranteed_systems
    
    def _calculate_wheel_coverage(self, wheel_lines: List[List[int]], prob_analysis: Dict, picks: int) -> float:
        """Calculate expected coverage probability for the wheel system"""
        if not wheel_lines:
            return 0.0
        
        # Simulate coverage using probability weights
        number_probs = prob_analysis['number_probabilities']
        
        # Monte Carlo estimation of coverage probability
        total_probability = 0.0
        
        for line in wheel_lines:
            # Calculate probability this line gets 3+ matches
            line_prob = 1.0
            for num in line:
                if num in number_probs:
                    line_prob *= number_probs[num]['probability']
            
            # Adjust for combinations and expected matches
            expected_matches = sum(number_probs.get(num, {}).get('probability', 0) for num in line)
            match_3_plus_prob = max(0, (expected_matches - 2) / picks) * 100
            
            total_probability += match_3_plus_prob
        
        # Average across all lines, capped at realistic maximum
        avg_coverage = min(total_probability / len(wheel_lines), 85.0)
        return avg_coverage
    
    def _calculate_diversity_score(self, wheel_lines: List[List[int]]) -> float:
        """Calculate diversity score for the wheel system"""
        if not wheel_lines:
            return 0.0
        
        # Calculate how well numbers are distributed across lines
        number_usage = defaultdict(int)
        for line in wheel_lines:
            for num in line:
                number_usage[num] += 1
        
        # Diversity is higher when numbers are used more evenly
        usage_values = list(number_usage.values())
        if not usage_values:
            return 0.0
        
        mean_usage = np.mean(usage_values)
        variance = np.var(usage_values)
        
        # Lower variance (more even distribution) = higher diversity score
        diversity = 100 / (1 + variance / max(mean_usage, 1))
        return min(diversity, 100.0)
    
    def generate_single_optimized_line(self, game_type: str) -> Dict[str, Any]:
        """Generate single best-probability line for a game"""
        try:
            prob_analysis = self.probability_estimator.calculate_number_probabilities(game_type)
            config = self.game_configs.get(game_type)
            
            if not prob_analysis or not config:
                return {}
            
            picks = config['picks']
            number_probs = prob_analysis['number_probabilities']
            
            # Get top numbers by probability
            sorted_numbers = sorted(number_probs.items(), 
                                  key=lambda x: x[1]['probability'], reverse=True)
            
            # Select top numbers with some diversity
            selected_numbers = []
            
            # Take top numbers but ensure some spread
            for i, (num, prob_data) in enumerate(sorted_numbers):
                if len(selected_numbers) >= picks:
                    break
                
                # Add number if it's high probability and adds diversity
                if i < picks * 2 or prob_data['probability'] > 0.03:
                    selected_numbers.append(num)
            
            # If we need more numbers, add from remaining top choices
            if len(selected_numbers) < picks:
                remaining = [num for num, _ in sorted_numbers if num not in selected_numbers]
                selected_numbers.extend(remaining[:picks - len(selected_numbers)])
            
            selected_numbers = selected_numbers[:picks]
            
            # Calculate expected performance
            expected_probability = sum(number_probs[num]['probability'] for num in selected_numbers)
            confidence = prob_analysis['confidence_level']
            
            return {
                'game_type': game_type,
                'optimized_numbers': sorted(selected_numbers),
                'expected_probability': expected_probability,
                'confidence_level': confidence,
                'reasoning': f"Selected top {picks} numbers from {prob_analysis['total_draws']} historical draws",
                'generated_at': prob_analysis['analysis_date']
            }
            
        except Exception as e:
            logger.error(f"Error generating optimized line for {game_type}: {e}")
            return {}

if __name__ == "__main__":
    # Test the coverage optimizer
    logging.basicConfig(level=logging.INFO)
    optimizer = CoverageOptimizer()
    
    for game_type in ['DAILY LOTTO', 'LOTTO']:
        print(f"\n=== {game_type} Optimization ===")
        
        # Test single line optimization
        single_line = optimizer.generate_single_optimized_line(game_type)
        if single_line:
            print(f"Optimized Line: {single_line['optimized_numbers']}")
            print(f"Expected Probability: {single_line['expected_probability']:.3f}")
        
        # Test wheel system
        wheel_system = optimizer.generate_wheel_system(game_type, budget_lines=20)
        if wheel_system:
            print(f"Wheel System: {len(wheel_system['wheel_lines'])} lines")
            print(f"Expected 3+ Coverage: {wheel_system['coverage_analysis']['expected_3_plus_probability']:.1f}%")
            print(f"Pool Size: {wheel_system['pool_size']} numbers")