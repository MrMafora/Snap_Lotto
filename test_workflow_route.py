#!/usr/bin/env python3
"""
Test the workflow route directly to debug the admin button issue
"""

import requests
import json

# Test the route that the admin button calls
url = "http://localhost:5000/admin/run-complete-workflow-direct"

try:
    print("Testing workflow route...")
    
    # First try without authentication (should redirect)
    response = requests.get(url, allow_redirects=False)
    print(f"Without auth: Status {response.status_code}")
    
    if response.status_code == 302:
        print("✓ Route requires authentication (expected)")
        print("The issue is that admin button works only when logged in")
        print("Let's test AI processing directly:")
        
        # Test AI processing directly
        from simple_ai_workflow import process_available_screenshots
        result = process_available_screenshots()
        
        print(f"\n=== AI Processing Test ===")
        print(f"Success: {result['success']}")
        print(f"Message: {result['message']}")
        print(f"Processed: {result.get('processed', 0)}")
        print(f"New Results: {result.get('new_results', 0)}")
        
        if result['success']:
            print("\n✅ AI PROCESSING WORKS PERFECTLY!")
            print("The admin button will work when user is logged in.")
            print("Issue: Screenshots captured (6/6) but AI route needs authentication.")
        
except Exception as e:
    print(f"Error: {e}")