import requests
import json
import time

def test_endpoints():
    """Test the lottery analysis API endpoints"""
    base_url = "http://localhost:5000"
    
    # Test endpoints
    endpoints = [
        "/api/lottery-analysis/frequency",
        "/api/lottery-analysis/patterns",
        "/api/lottery-analysis/time-series",
        "/api/lottery-analysis/correlations",
        "/api/lottery-analysis/winners"
    ]
    
    for endpoint in endpoints:
        print(f"Testing {endpoint}...")
        try:
            response = requests.get(f"{base_url}{endpoint}")
            
            print(f"Status: {response.status_code}")
            if response.status_code == 200:
                data = response.json()
                print(f"Response contains {len(data)} items")
                print("Keys:", list(data.keys())[:5])  # Show first 5 keys
            else:
                print(f"Error response: {response.text[:100]}...")
                
        except Exception as e:
            print(f"Error: {str(e)}")
        
        print("-" * 50)
        time.sleep(1)  # Small delay between requests

if __name__ == "__main__":
    test_endpoints()