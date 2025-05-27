#!/usr/bin/env python3
"""
Quick test to see what the AI is actually returning for PowerBall tickets
"""
import json
import base64
from anthropic import Anthropic
import os

# Set up the API client
client = Anthropic(api_key=os.environ.get('ANTHROPIC_API_SNAP_LOTTERY'))

# Simple test with a basic PowerBall prompt
def test_ai_response():
    # Create a simple test message
    message = client.messages.create(
        model="claude-3-5-sonnet-20241022",
        max_tokens=1000,
        messages=[{
            "role": "user",
            "content": [
                {
                    "type": "text",
                    "text": """Return this exact JSON format:
                    
                    {
                        "lottery_type": "PowerBall",
                        "main_numbers": [1, 2, 3, 4, 5],
                        "powerball_number": "10",
                        "powerball_plus_included": "YES",
                        "draw_date": "16/05/2025",
                        "draw_number": "PB1615",
                        "ticket_cost": "R15.00"
                    }
                    
                    Return ONLY the JSON object, no other text."""
                }
            ]
        }]
    )
    
    # Get the response
    response_text = message.content[0].text
    print("=== RAW AI RESPONSE ===")
    print(response_text)
    print("=====================")
    
    # Try to parse it
    try:
        data = json.loads(response_text.strip())
        print("=== PARSED JSON ===")
        print(json.dumps(data, indent=2))
        print("==================")
        return True
    except Exception as e:
        print(f"JSON parsing failed: {e}")
        return False

if __name__ == "__main__":
    success = test_ai_response()
    print(f"Test {'PASSED' if success else 'FAILED'}")