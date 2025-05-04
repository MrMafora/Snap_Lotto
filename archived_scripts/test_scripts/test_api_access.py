import requests
import json
import sys

def test_api_endpoint(endpoint):
    """Test an API endpoint and print the results."""
    url = f"http://localhost:5000{endpoint}"
    print(f"Testing API endpoint: {url}")
    
    try:
        response = requests.get(url)
        print(f"Status code: {response.status_code}")
        
        if response.status_code == 200:
            # Try to parse the JSON response
            try:
                data = response.json()
                print(f"Response contains {len(data)} lottery types")
                # Print each lottery type
                for lottery_type in data.keys():
                    print(f"  - {lottery_type}")
                return True
            except json.JSONDecodeError:
                print("Could not parse JSON response")
                print(f"First 100 characters of response: {response.text[:100]}")
                return False
        else:
            print(f"Error response: {response.text[:100]}")
            return False
    except Exception as e:
        print(f"Exception occurred: {str(e)}")
        return False

def main():
    # Define the endpoints to test
    endpoints = [
        "/api/lottery-analysis/frequency?lottery_type=&days=30",
        "/api/lottery-analysis/patterns?lottery_type=&days=30",
        "/api/lottery-analysis/time-series?lottery_type=&days=30",
        "/api/lottery-analysis/correlations?days=30",
        "/api/lottery-analysis/winners?lottery_type=&days=30"
    ]
    
    # Test each endpoint
    results = []
    for endpoint in endpoints:
        result = test_api_endpoint(endpoint)
        results.append(result)
        print("-" * 50)
    
    # Print summary
    print("\nSummary:")
    for i, endpoint in enumerate(endpoints):
        status = "✓ Success" if results[i] else "✗ Failed"
        print(f"{status}: {endpoint}")
    
    # Exit with success if all endpoints worked
    if all(results):
        print("\nAll API endpoints are accessible!")
        return 0
    else:
        print("\nSome API endpoints failed!")
        return 1

if __name__ == "__main__":
    sys.exit(main())