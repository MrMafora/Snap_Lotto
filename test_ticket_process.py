#!/usr/bin/env python3
"""
Quick test of ticket processing with Google Gemini 2.5 Pro
"""

import os
import json
import google.generativeai as genai
import PIL.Image

def test_ticket_processing():
    """Test ticket processing with a real image"""
    try:
        # Configure Gemini
        genai.configure(api_key=os.environ.get('GOOGLE_API_KEY_SNAP_LOTTERY'))
        model = genai.GenerativeModel('gemini-1.5-pro')
        
        # Load the test image
        image_path = 'attached_assets/IMG_8497.jpeg'
        image = PIL.Image.open(image_path)
        
        # Simple prompt
        prompt = """Extract lottery ticket data from this image.

Return only JSON:
{
    "lottery_type": "PowerBall",
    "all_lines": [[12,17,24,26,35], [5,15,17,24,32]],
    "all_powerball": [12, 12],
    "draw_date": "18/04/25",
    "draw_number": "1607",
    "ticket_cost": "R37.50"
}"""
        
        response = model.generate_content([image, prompt])
        print("Raw response:")
        print(response.text)
        
        # Try to parse JSON
        import re
        json_match = re.search(r'\{.*\}', response.text, re.DOTALL)
        if json_match:
            json_text = json_match.group()
            ticket_data = json.loads(json_text)
            print("\nParsed JSON:")
            print(json.dumps(ticket_data, indent=2))
            return True
        else:
            print("No JSON found in response")
            return False
            
    except Exception as e:
        print(f"Error: {e}")
        return False

if __name__ == "__main__":
    test_ticket_processing()