#!/usr/bin/env python3
"""
Test script to identify JSON import scope issues in ticket processing
"""
import json
import re
import os
import google.generativeai as genai

def test_json_parsing():
    """Test JSON parsing functionality"""
    test_response = '''```json
{
    "lottery_type": "LOTTO",
    "all_lines": [[8, 24, 32, 34, 36, 52]],
    "bonus_numbers": [26],
    "lotto_plus_1_included": "NO",
    "lotto_plus_2_included": "NO",
    "draw_date": "04/06/25",
    "draw_number": "2547"
}
```'''
    
    print("Testing JSON parsing...")
    json_match = re.search(r'\{.*\}', test_response, re.DOTALL)
    if json_match:
        json_text = json_match.group()
        print(f"Extracted JSON: {json_text}")
        
        try:
            ticket_data = json.loads(json_text)
            print(f"Parsed successfully: {ticket_data}")
            return True
        except Exception as e:
            print(f"JSON parsing failed: {e}")
            return False
    else:
        print("No JSON match found")
        return False

if __name__ == "__main__":
    success = test_json_parsing()
    print(f"Test result: {'PASS' if success else 'FAIL'}")