#!/usr/bin/env python3
"""
Script to test the lottery analysis API endpoints to verify functionality
after JavaScript improvements.
"""
import requests
import json
import sys
import time

BASE_URL = "http://localhost:5000"

def login_admin():
    """Login as admin to get the session cookies"""
    session = requests.Session()
    
    # First get the CSRF token
    response = session.get(f"{BASE_URL}/login")
    if response.status_code != 200:
        print(f"Failed to load login page: {response.status_code}")
        return None
    
    # Now login
    login_data = {
        "username": "admin",
        "password": "St0n3@g3",
        "remember": False
    }
    
    response = session.post(f"{BASE_URL}/login", data=login_data)
    if response.status_code == 200 or response.status_code == 302:
        print("Login successful")
        return session
    else:
        print(f"Login failed: {response.status_code}")
        return None

def test_api_endpoint(session, endpoint, params=None):
    """Test a specific API endpoint"""
    print(f"\nTesting endpoint: {endpoint}")
    url = f"{BASE_URL}{endpoint}"
    
    if params:
        param_str = "&".join([f"{k}={v}" for k, v in params.items()])
        url = f"{url}?{param_str}"
    
    try:
        start_time = time.time()
        response = session.get(url)
        end_time = time.time()
        
        print(f"Response time: {end_time - start_time:.2f} seconds")
        print(f"Status code: {response.status_code}")
        
        if response.status_code == 200:
            try:
                data = response.json()
                # Simplify output by just showing top level keys
                if isinstance(data, dict):
                    print("Response data keys:", list(data.keys()))
                    
                    # Check for errors
                    has_error = False
                    if "error" in data:
                        print(f"Error found: {data['error']}")
                        has_error = True
                    
                    # Check each lottery type for errors
                    for key, value in data.items():
                        if isinstance(value, dict) and "error" in value:
                            print(f"Error in {key}: {value['error']}")
                            has_error = True
                    
                    if not has_error:
                        print("No errors found in response")
                        return True
                else:
                    print("Response data:", data)
                    return True
            except json.JSONDecodeError:
                print("Failed to parse JSON response")
                print("Raw response:", response.text[:100] + "...")
        else:
            print("API call failed")
        
        return False
    except Exception as e:
        print(f"Request error: {str(e)}")
        return False

def main():
    """Test all lottery analysis API endpoints"""
    session = login_admin()
    if not session:
        sys.exit(1)
    
    # Test for common lottery types
    lottery_types = ["Lotto", "Powerball", "Daily Lotto"]
    
    # Define endpoints to test
    endpoints = [
        ("/api/lottery-analysis/patterns", {"lottery_type": "", "days": "365"}),
        ("/api/lottery-analysis/time-series", {"lottery_type": "", "days": "365"}),
        ("/api/lottery-analysis/winners", {"lottery_type": "", "days": "365"}),
        ("/api/lottery-analysis/correlations", {"days": "365"})
    ]
    
    success_count = 0
    total_tests = len(endpoints)
    
    for endpoint, params in endpoints:
        if test_api_endpoint(session, endpoint, params):
            success_count += 1
    
    # Also test lottery-specific endpoints
    for lottery_type in lottery_types:
        for endpoint, params in endpoints[:3]:  # Skip correlations for specific lottery types
            params["lottery_type"] = lottery_type
            if test_api_endpoint(session, endpoint, params):
                success_count += 1
            total_tests += 1
    
    print(f"\nTest results: {success_count}/{total_tests} successful ({success_count/total_tests*100:.1f}%)")

if __name__ == "__main__":
    main()