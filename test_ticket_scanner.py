#!/usr/bin/env python3
"""
Test the ticket scanner functionality with a sample image
"""
import os
import requests
import json

def test_ticket_scanner():
    """Test the ticket scanner with a sample image"""
    
    # Use one of the existing lottery ticket images
    test_image_path = "attached_assets/IMG_8494.png"
    
    if not os.path.exists(test_image_path):
        print(f"Test image not found: {test_image_path}")
        return
    
    # Test the process-ticket endpoint
    url = "http://localhost:5000/process-ticket"
    
    try:
        with open(test_image_path, 'rb') as f:
            files = {'ticket_image': f}
            response = requests.post(url, files=files, timeout=30)
        
        print(f"Response status: {response.status_code}")
        print(f"Response content: {response.text}")
        
        if response.status_code == 200:
            try:
                result = response.json()
                print("\n=== TICKET SCANNER TEST RESULTS ===")
                print(json.dumps(result, indent=2))
                
                if result.get('success'):
                    print("\n✓ Ticket scanner is working correctly!")
                else:
                    print(f"\n✗ Ticket scanner failed: {result.get('error')}")
            except json.JSONDecodeError:
                print("Failed to parse JSON response")
        else:
            print(f"HTTP error: {response.status_code}")
            
    except Exception as e:
        print(f"Error testing ticket scanner: {e}")

if __name__ == "__main__":
    test_ticket_scanner()