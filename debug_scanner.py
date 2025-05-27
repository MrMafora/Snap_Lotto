#!/usr/bin/env python3
"""
Debug script to test PowerBall scanner response processing
"""
import json
import sys
import os

# Add the current directory to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_json_parsing():
    """Test different JSON parsing scenarios"""
    
    # Test case 1: Clean JSON response
    test_response_1 = '''
    {
        "lottery_type": "PowerBall",
        "main_numbers": [1, 2, 3, 4, 5],
        "powerball_number": "10",
        "powerball_plus_included": "YES",
        "draw_date": "16/05/2025",
        "draw_number": "PB1615",
        "ticket_cost": "R15.00"
    }
    '''
    
    # Test case 2: JSON with extra text
    test_response_2 = '''Looking at this PowerBall ticket, I can extract:
    
    {
        "lottery_type": "PowerBall",
        "main_numbers": [7, 14, 21, 28, 35],
        "powerball_number": "12",
        "powerball_plus_included": "YES",
        "draw_date": "18/05/2025",
        "draw_number": "PB1618",
        "ticket_cost": "R15.00"
    }
    
    This ticket includes PowerBall Plus as indicated by YES.'''
    
    test_cases = [
        ("Clean JSON", test_response_1),
        ("JSON with text", test_response_2)
    ]
    
    for name, response in test_cases:
        print(f"\n=== Testing {name} ===")
        print(f"Response: {response[:100]}...")
        
        try:
            # Try direct JSON parsing
            cleaned = response.strip()
            data = json.loads(cleaned)
            print(f"✓ Direct parsing successful: {data}")
            continue
        except json.JSONDecodeError:
            print("✗ Direct parsing failed")
        
        try:
            # Try regex extraction
            import re
            json_match = re.search(r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}', response, re.DOTALL)
            if json_match:
                data = json.loads(json_match.group())
                print(f"✓ Regex parsing successful: {data}")
                continue
        except json.JSONDecodeError:
            print("✗ Regex parsing failed")
        
        print("✗ All parsing methods failed")

if __name__ == "__main__":
    print("PowerBall Scanner Debug Test")
    print("=" * 40)
    test_json_parsing()