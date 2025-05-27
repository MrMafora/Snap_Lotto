#!/usr/bin/env python3
"""
Simple test to verify what data the ticket scanner returns
"""

import requests
import json

def test_ticket_scanner():
    """Test the ticket scanner endpoint"""
    url = "http://localhost:5000/process-ticket"
    
    # Simulate a ticket upload (we'll use a simple test)
    test_data = {
        'ticket_image': 'test'  # This will trigger our fallback path
    }
    
    try:
        response = requests.post(url, data=test_data)
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.text}")
        
        if response.status_code == 200:
            data = response.json()
            print("\nParsed JSON:")
            print(json.dumps(data, indent=2))
            
            # Check the specific fields the frontend expects
            print(f"\nlottery_type: {data.get('lottery_type', 'MISSING')}")
            print(f"draw_date: {data.get('draw_date', 'MISSING')}")
            print(f"draw_number: {data.get('draw_number', 'MISSING')}")
            
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_ticket_scanner()