#!/usr/bin/env python3
"""
Extract Lotto Plus 2 data using AI from the provided image
"""
import os
import base64
import json
from anthropic import Anthropic

def extract_lottery_data():
    """Extract lottery data using Anthropic AI"""
    
    # Get API key
    api_key = os.environ.get('ANTHROPIC_API_SNAP_LOTTERY')
    if not api_key:
        print("Error: ANTHROPIC_API_SNAP_LOTTERY environment variable not set")
        return None
    
    # Initialize Anthropic client
    client = Anthropic(api_key=api_key)
    
    # Image path
    image_path = "attached_assets/20250530_030508_lotto_plus_2_results.png"
    
    if not os.path.exists(image_path):
        print(f"Error: Image not found at {image_path}")
        return None
    
    # Encode image to base64
    with open(image_path, "rb") as image_file:
        image_data = base64.b64encode(image_file.read()).decode('utf-8')
    
    print("Sending image to AI for analysis...")
    
    try:
        # the newest Anthropic model is "claude-3-5-sonnet-20241022" which was released October 22, 2024
        response = client.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=1000,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": """Please extract the lottery data from this South African National Lottery screenshot. 

I need you to identify:
1. The lottery type (Lotto, Lotto Plus 1, Lotto Plus 2, PowerBall, PowerBall Plus, Daily Lotto)
2. The draw number 
3. The draw date
4. The winning numbers (all numbers shown in the winning numbers section)
5. Any bonus ball if present

Please provide the winning numbers as a comma-separated list in the exact order they appear in the image.

Return the data as JSON in this exact format:
{
    "lottery_type": "exact lottery type name",
    "draw_number": "number",
    "draw_date": "YYYY-MM-DD",
    "numbers": "num1,num2,num3,num4,num5,num6",
    "bonus_ball": "number or null"
}"""
                        },
                        {
                            "type": "image",
                            "source": {
                                "type": "base64",
                                "media_type": "image/png",
                                "data": image_data
                            }
                        }
                    ]
                }
            ]
        )
        
        # Extract the response text
        response_text = response.content[0].text
        print(f"AI Response: {response_text}")
        
        # Try to parse JSON from the response
        try:
            # Find JSON in the response
            json_start = response_text.find('{')
            json_end = response_text.rfind('}') + 1
            if json_start >= 0 and json_end > json_start:
                json_str = response_text[json_start:json_end]
                data = json.loads(json_str)
                return data
            else:
                print("No JSON found in response")
                return None
        except json.JSONDecodeError as e:
            print(f"Error parsing JSON: {e}")
            print(f"Response text: {response_text}")
            return None
            
    except Exception as e:
        print(f"Error calling Anthropic API: {e}")
        return None

if __name__ == "__main__":
    result = extract_lottery_data()
    if result:
        print("\nExtracted Data:")
        print(json.dumps(result, indent=2))
    else:
        print("Failed to extract data")