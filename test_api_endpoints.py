"""
Test script to check the lottery analysis API endpoints.
"""
import requests
import sys
import json

BASE_URL = "http://localhost:5000"

def login_and_get_csrf(session):
    """Log in and get CSRF token"""
    print("Logging in to get CSRF token...")
    
    # First get login page to get initial CSRF token
    login_url = f"{BASE_URL}/login"
    response = session.get(login_url)
    
    if response.status_code != 200:
        print(f"Failed to get login page: {response.status_code}")
        return False
    
    # Extract CSRF token from login page
    login_html = response.text
    import re
    csrf_match = re.search(r'<input[^>]*name="csrf_token"[^>]*value="([^"]*)"', login_html)
    if not csrf_match:
        print("Failed to find CSRF token in login page")
        return False
    
    csrf_token = csrf_match.group(1)
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
        return False
    
    print("Login successful!")
    
    # Get CSRF token from cookie
    csrf_token = session.cookies.get("csrf_token")
    if not csrf_token:
        print("Failed to get CSRF token after login")
        return False
    
    return True

def test_api_endpoint(session, endpoint, params=None):
    """Test an API endpoint"""
    url = f"{BASE_URL}{endpoint}"
    csrf_token = session.cookies.get("csrf_token")
    
    headers = {
        "X-CSRFToken": csrf_token,
        "Referer": BASE_URL
    }
    
    print(f"Testing endpoint: {url}")
    print(f"With CSRF token: {csrf_token[:10] if csrf_token else 'None'}...")
    
    try:
        response = session.get(url, headers=headers, params=params)
        print(f"Status code: {response.status_code}")
        
        if response.status_code == 200:
            try:
                data = response.json()
                print(f"Response is valid JSON")
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
    print("Testing lottery analysis API endpoints...")
    
    # Create a session to maintain cookies
    session = requests.Session()
    
    # Login and get CSRF token
    if not login_and_get_csrf(session):
        print("Login failed, cannot continue tests")
        return
    
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