#!/usr/bin/env python3
"""
Test a single Lottery Analysis API endpoint
"""
import requests
import sys

# Create a session and login
session = requests.Session()

# Login as admin
response = session.get("http://localhost:5000/login")
if response.status_code != 200:
    print(f"Failed to load login page: {response.status_code}")
    sys.exit(1)

# Now login
login_data = {
    "username": "admin",
    "password": "St0n3@g3"
}

response = session.post("http://localhost:5000/login", data=login_data)
if response.status_code == 200 or response.status_code == 302:
    print("Login successful")
else:
    print(f"Login failed: {response.status_code}")
    sys.exit(1)

# Test the time series endpoint
url = "http://localhost:5000/api/lottery-analysis/time-series?lottery_type=Lotto&days=365"
print(f"Testing: {url}")
response = session.get(url)
print(f"Status code: {response.status_code}")

if response.status_code == 200:
    data = response.json()
    print("Success! Time series API is working.")
    
    # Check for errors
    if isinstance(data, dict) and "error" in data:
        print(f"API returned error: {data['error']}")
    elif isinstance(data, dict) and "Lotto" in data:
        if "error" in data["Lotto"]:
            print(f"API returned error for Lotto: {data['Lotto']['error']}")
        elif "chart_base64" in data["Lotto"]:
            print("API returned chart data correctly.")
    else:
        print("API returned data without errors.")
else:
    print("API call failed")