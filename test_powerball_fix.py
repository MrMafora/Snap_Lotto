#!/usr/bin/env python3
"""
Test the Powerball case sensitivity fix
"""

import os
import sys
sys.path.append('.')

from models import db, LotteryResult
from main import app

def test_powerball_fix():
    """Test that Powerball data can be found with the new case sensitivity handling"""
    
    with app.app_context():
        print("=== TESTING POWERBALL CASE SENSITIVITY FIX ===")
        
        # Test the case variations we expect to find
        variations = ['POWERBALL', 'PowerBall', 'Powerball']
        
        for variation in variations:
            results = LotteryResult.query.filter_by(lottery_type=variation).limit(3).all()
            print(f"\nLottery type '{variation}': {len(results)} results found")
            
            if results:
                for result in results[:2]:  # Show first 2
                    numbers = [result.number_1, result.number_2, result.number_3, result.number_4, result.number_5]
                    print(f"  Draw {result.draw_number}: Numbers {numbers}, Powerball: {result.powerball_number}")
        
        # Test the new query logic - this should find all PowerBall variations
        test_variations = ['POWERBALL', 'PowerBall', 'Powerball']
        combined_results = LotteryResult.query.filter(LotteryResult.lottery_type.in_(test_variations)).limit(5).all()
        print(f"\nCombined query for all variations: {len(combined_results)} results found")
        
        if combined_results:
            print("\nFirst few results from combined query:")
            for result in combined_results[:3]:
                numbers = [result.number_1, result.number_2, result.number_3, result.number_4, result.number_5]
                print(f"  {result.lottery_type} - Draw {result.draw_number}: Numbers {numbers}, Powerball: {result.powerball_number}")

if __name__ == "__main__":
    test_powerball_fix()