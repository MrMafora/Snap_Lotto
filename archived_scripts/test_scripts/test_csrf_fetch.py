"""
Test script to verify the lottery analysis API endpoints with CSRF tokens.
"""
import requests
import sys
import json
from urllib.parse import urljoin

BASE_URL = "http://localhost:5000"

def login_and_get_csrf(session):
    """
    Log in and get CSRF token
    """
    print("Logging in to get CSRF token...")
    
    # First get login page to get initial CSRF token
    login_url = urljoin(BASE_URL, "/login")
    response = session.get(login_url)
    
    if response.status_code != 200:
        print(f"Failed to get login page: {response.status_code}")
        sys.exit(1)
    
    # Extract CSRF token from login page
    login_html = response.text
    csrf_token = None
    
    # Look for the CSRF token in the HTML
    import re
    csrf_match = re.search(r'<input[^>]*name="csrf_token"[^>]*value="([^"]*)"', login_html)
    if csrf_match:
        csrf_token = csrf_match.group(1)
    else:
        print("Failed to find CSRF token in login page")
        sys.exit(1)
    
    print(f"Found CSRF token: {csrf_token[:10]}...")
    
    # Login with admin credentials
    login_data = {
        "username": "admin",
        "password": "St0n3@g3",
        "csrf_token": csrf_token
    }
    
    response = session.post(login_url, data=login_data)
    
    if response.status_code != 200 and response.status_code != 302:
        print(f"Login failed: {response.status_code}")
        sys.exit(1)
    
    print("Login successful!")
    
    # Get a new CSRF token after login
    csrf_token = session.cookies.get("csrf_token")
    if not csrf_token:
        print("Failed to get CSRF token after login")
        # Check for other cookies
        print("Available cookies:")
        for cookie in session.cookies:
            print(f"  {cookie.name}: {cookie.value}")
        sys.exit(1)
    
    return csrf_token

def test_api_endpoint(session, endpoint, params=None):
    """
    Test an API endpoint with CSRF token
    """
    url = urljoin(BASE_URL, endpoint)
    csrf_token = session.cookies.get("csrf_token")
    
    headers = {
        "X-CSRFToken": csrf_token,
        "Referer": BASE_URL  # Some CSRF protections check Referer header
    }
    
    print(f"Testing endpoint: {url}")
    print(f"With CSRF token: {csrf_token[:10]}...")
    
    try:
        response = session.get(url, headers=headers, params=params)
        print(f"Status code: {response.status_code}")
        
        if response.status_code == 200:
            try:
                data = response.json()
                keys = list(data.keys())
                print(f"Response contains keys: {keys[:5]}...")
                if len(keys) > 0:
                    print(f"First key '{keys[0]}' contains data of type: {type(data[keys[0]]).__name__}")
                return True
            except json.JSONDecodeError:
                print("Response is not valid JSON")
                print(f"Response text: {response.text[:100]}...")
                return False
        else:
            print(f"Response text: {response.text[:100]}...")
            return False
    except Exception as e:
        print(f"Error: {e}")
        return False

def main():
    """Main function"""
    print("Testing CSRF token fixes for lottery analysis API endpoints...")
    
    # Create a session to maintain cookies
    session = requests.Session()
    
    # Login and get CSRF token
    login_and_get_csrf(session)
    
    # Test endpoints
    endpoints = [
        ("/api/lottery-analysis/patterns", {"lottery_type": "Lotto", "days": "365"}),
        ("/api/lottery-analysis/time-series", {"lottery_type": "Lotto", "days": "365"}),
        ("/api/lottery-analysis/winners", {"lottery_type": "Lotto", "days": "365"}),
        ("/api/lottery-analysis/correlations", {"days": "365"})
    ]
    
    success_count = 0
    
    for endpoint, params in endpoints:
        print("\n" + "="*50)
        result = test_api_endpoint(session, endpoint, params)
        if result:
            success_count += 1
            print(f"✓ Success: {endpoint}")
        else:
            print(f"✗ Failed: {endpoint}")
    
    print("\n" + "="*50)
    print(f"Summary: {success_count}/{len(endpoints)} endpoints successful")

if __name__ == "__main__":
    main()