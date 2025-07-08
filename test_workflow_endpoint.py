#!/usr/bin/env python3
"""
Test the complete workflow endpoint to ensure it's working
"""
import requests
import json

# Test without authentication (for development)
print("Testing complete workflow endpoint...")

# Directly call the automation endpoint
url = "http://localhost:5000/admin/run-complete-workflow"

# Create a session to handle cookies
session = requests.Session()

# First, let's login as admin
login_url = "http://localhost:5000/dev-auto-login"
login_response = session.get(login_url)
print(f"Login status: {login_response.status_code}")

# Now call the workflow endpoint
response = session.post(url, json={})

print(f"Response status: {response.status_code}")

if response.status_code == 200:
    try:
        data = response.json()
        print(f"Success: {data}")
    except:
        print(f"Response text: {response.text[:500]}...")
else:
    print(f"Error: {response.text}")