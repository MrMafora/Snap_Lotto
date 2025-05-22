#!/usr/bin/env python3
"""
Test script to verify that the lottery analysis UI is working correctly.
This script will:
1. Log in as admin
2. Access the lottery analysis page
3. Extract and test all the API endpoints used by the JavaScript in the page
4. Check that the expected data is returned
"""

import json
import requests
import re
from urllib.parse import urljoin
import time
import sys

BASE_URL = "http://0.0.0.0:5000"
USERNAME = "admin"
PASSWORD = "St0n3@g3"

def get_csrf_token(session, url):
    """Extract CSRF token from a page"""
    response = session.get(url)
    csrf_token = None
    
    # Try to find the CSRF token in meta tags
    match = re.search(r'<meta name="csrf-token" content="([^"]+)"', response.text)
    if match:
        csrf_token = match.group(1)
    else:
        # Try to find it in a hidden input field
        match = re.search(r'<input[^>]*name="csrf_token"[^>]*value="([^"]+)"', response.text)
        if match:
            csrf_token = match.group(1)
        else:
            # Try to find it in the cookies
            if 'csrf_token' in session.cookies:
                csrf_token = session.cookies['csrf_token']
    
    return csrf_token

def login(session):
    """Log in to the application as admin"""
    login_url = urljoin(BASE_URL, "/login")
    csrf_token = get_csrf_token(session, login_url)
    
    if not csrf_token:
        print("ERROR: Could not find CSRF token for login")
        return False
    
    login_data = {
        "username": USERNAME,
        "password": PASSWORD,
        "csrf_token": csrf_token
    }
    
    response = session.post(login_url, data=login_data, allow_redirects=True)
    
    if response.url.endswith('/login'):
        print("ERROR: Login failed")
        return False
    
    print(f"✅ Login successful: {response.url}")
    return True

def access_lottery_analysis(session):
    """Access the lottery analysis page"""
    lottery_analysis_url = urljoin(BASE_URL, "/admin/lottery-analysis")
    response = session.get(lottery_analysis_url)
    
    if response.status_code != 200:
        print(f"ERROR: Failed to access lottery analysis page: {response.status_code}")
        return False
    
    print(f"✅ Accessed lottery analysis page: {response.status_code}")
    
    # Print a small sample of the page to help with debugging
    print("Page content preview (first 500 chars):")
    print(response.text[:500] + "...")
    
    # Print tab names - Bootstrap 5 style
    tab_pattern = re.compile(r'<button[^>]*class="nav-link"[^>]*>(.*?)</button>', re.DOTALL)
    tabs = tab_pattern.findall(response.text)
    print("\nFound tabs:", tabs)
    
    # Check that the page contains the expected tabs
    pattern_found = any("pattern" in tab.lower() for tab in tabs)
    time_series_found = any("time series" in tab.lower() or "timeseries" in tab.lower() for tab in tabs)
    winner_found = any("winner" in tab.lower() for tab in tabs)
    correlation_found = any("correlation" in tab.lower() for tab in tabs)
    
    if not pattern_found:
        print("ERROR: Lottery analysis page is missing Pattern Analysis tab")
        return False
    
    if not time_series_found:
        print("ERROR: Lottery analysis page is missing Time Series Analysis tab")
        return False
    
    if not winner_found:
        print("ERROR: Lottery analysis page is missing Winner Analysis tab")
        return False
    
    if not correlation_found:
        print("ERROR: Lottery analysis page is missing Correlation Analysis tab")
        return False
    
    print("✅ All expected tabs are present on the lottery analysis page")
    return True

def test_patterns_api(session):
    """Test the patterns API endpoint"""
    patterns_url = urljoin(BASE_URL, "/api/lottery-analysis/patterns?lottery_type=Lotto&days=365")
    csrf_token = get_csrf_token(session, urljoin(BASE_URL, "/admin/lottery-analysis"))
    
    headers = {
        "X-CSRFToken": csrf_token,
        "Accept": "application/json"
    }
    
    print(f"Testing patterns API with token: {csrf_token}")
    
    response = session.get(patterns_url, headers=headers)
    
    if response.status_code != 200:
        print(f"ERROR: Patterns API returned error status code: {response.status_code}")
        return False
    
    try:
        data = response.json()
        print(f"Pattern API response keys: {list(data.keys())}")
        
        # Check for nested chart_base64
        if "chart_base64" in data:
            print(f"✅ Patterns API returned valid data with chart_base64 ({len(data['chart_base64'])} chars)")
            return True
        
        # For the Lotto key which contains nested data
        if "Lotto" in data and isinstance(data["Lotto"], dict) and "chart_base64" in data["Lotto"]:
            print(f"✅ Patterns API returned valid data with nested chart_base64 ({len(data['Lotto']['chart_base64'])} chars)")
            return True
            
        print("ERROR: Patterns API did not return chart_base64 (not found in response)")
        return False
    except json.JSONDecodeError:
        print("ERROR: Patterns API did not return valid JSON")
        return False

def test_time_series_api(session):
    """Test the time series API endpoint"""
    time_series_url = urljoin(BASE_URL, "/api/lottery-analysis/time-series?lottery_type=Lotto&days=365")
    csrf_token = get_csrf_token(session, urljoin(BASE_URL, "/admin/lottery-analysis"))
    
    headers = {
        "X-CSRFToken": csrf_token,
        "Accept": "application/json"
    }
    
    response = session.get(time_series_url, headers=headers)
    
    if response.status_code != 200:
        print(f"ERROR: Time Series API returned error status code: {response.status_code}")
        return False
    
    try:
        data = response.json()
        print(f"Time Series API response keys: {list(data.keys())}")
        
        # Check for chart_base64 directly or in nested structure
        if "chart_base64" in data:
            print(f"✅ Time Series API returned valid data with chart_base64 ({len(data['chart_base64'])} chars)")
            return True
        
        # Check for nested structure
        for key, value in data.items():
            if isinstance(value, dict) and "chart_base64" in value:
                print(f"✅ Time Series API returned valid data with nested chart_base64 in '{key}' ({len(value['chart_base64'])} chars)")
                return True
                
        print("ERROR: Time Series API did not return chart_base64 (not found in response)")
        return False
    except json.JSONDecodeError:
        print("ERROR: Time Series API did not return valid JSON")
        return False

def test_winners_api(session):
    """Test the winners API endpoint"""
    winners_url = urljoin(BASE_URL, "/api/lottery-analysis/winners?lottery_type=Lotto&days=365")
    csrf_token = get_csrf_token(session, urljoin(BASE_URL, "/admin/lottery-analysis"))
    
    headers = {
        "X-CSRFToken": csrf_token,
        "Accept": "application/json"
    }
    
    response = session.get(winners_url, headers=headers)
    
    if response.status_code != 200:
        print(f"ERROR: Winners API returned error status code: {response.status_code}")
        return False
    
    try:
        data = response.json()
        print(f"Winners API response keys: {list(data.keys())}")
        
        # Check for chart_base64 directly
        if "chart_base64" in data:
            print(f"✅ Winners API returned valid data with chart_base64 ({len(data['chart_base64'])} chars)")
            return True
        
        # Check for nested structure
        for key, value in data.items():
            if isinstance(value, dict) and "chart_base64" in value:
                print(f"✅ Winners API returned valid data with nested chart_base64 in '{key}' ({len(value['chart_base64'])} chars)")
                return True
                
        print("ERROR: Winners API did not return chart_base64 (not found in response)")
        return False
    except json.JSONDecodeError:
        print("ERROR: Winners API did not return valid JSON")
        return False

def test_correlations_api(session):
    """Test the correlations API endpoint"""
    correlations_url = urljoin(BASE_URL, "/api/lottery-analysis/correlations?days=365")
    csrf_token = get_csrf_token(session, urljoin(BASE_URL, "/admin/lottery-analysis"))
    
    headers = {
        "X-CSRFToken": csrf_token,
        "Accept": "application/json"
    }
    
    response = session.get(correlations_url, headers=headers)
    
    if response.status_code != 200:
        print(f"ERROR: Correlations API returned error status code: {response.status_code}")
        return False
    
    try:
        data = response.json()
        print(f"Correlations API response keys: {list(data.keys())}")
        
        has_chart = False
        has_strong_correlations = False
        
        # Check for fields directly
        if "chart_base64" in data:
            print(f"✅ Correlations API returned valid data with chart_base64 ({len(data['chart_base64'])} chars)")
            has_chart = True
        
        if "strong_correlations" in data:
            print(f"✅ Correlations API returned strong_correlations array with {len(data['strong_correlations'])} items")
            has_strong_correlations = True
            
        # Check for nested data
        for key, value in data.items():
            if isinstance(value, dict):
                if "chart_base64" in value and not has_chart:
                    print(f"✅ Correlations API returned nested chart_base64 in '{key}' ({len(value['chart_base64'])} chars)")
                    has_chart = True
                    
                if "strong_correlations" in value and not has_strong_correlations:
                    print(f"✅ Correlations API returned nested strong_correlations array in '{key}' with {len(value['strong_correlations'])} items")
                    has_strong_correlations = True
        
        # Final verdict
        if not has_chart:
            print("ERROR: Correlations API did not return chart_base64 (not found in response)")
            return False
            
        if not has_strong_correlations:
            print("ERROR: Correlations API did not return strong_correlations array (not found in response)")
            return False
            
        return True
    except json.JSONDecodeError:
        print("ERROR: Correlations API did not return valid JSON")
        return False

def main():
    """Main test function"""
    session = requests.Session()
    
    print("Starting lottery analysis UI tests...")
    
    if not login(session):
        return 1
    
    if not access_lottery_analysis(session):
        return 1
    
    # Give the server a moment to process
    time.sleep(1)
    
    print("\nTesting API endpoints...")
    patterns_success = test_patterns_api(session)
    time_series_success = test_time_series_api(session)
    winners_success = test_winners_api(session)
    correlations_success = test_correlations_api(session)
    
    print("\nTest Summary:")
    print(f"- Patterns API: {'✅ PASS' if patterns_success else '❌ FAIL'}")
    print(f"- Time Series API: {'✅ PASS' if time_series_success else '❌ FAIL'}")
    print(f"- Winners API: {'✅ PASS' if winners_success else '❌ FAIL'}")
    print(f"- Correlations API: {'✅ PASS' if correlations_success else '❌ FAIL'}")
    
    if patterns_success and time_series_success and winners_success and correlations_success:
        print("\n🎉 All tests PASSED! The lottery analysis UI is working correctly.")
        return 0
    else:
        print("\n❌ Some tests FAILED. Please check the errors above.")
        return 1

if __name__ == "__main__":
    sys.exit(main())