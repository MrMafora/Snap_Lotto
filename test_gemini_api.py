#!/usr/bin/env python3
"""
Test Google Gemini API connectivity and basic functionality
"""

import os
import google.generativeai as genai

def test_gemini_connection():
    """Test if Google Gemini API is working"""
    try:
        # Configure API
        api_key = os.environ.get('GOOGLE_API_KEY_SNAP_LOTTERY')
        if not api_key:
            print("ERROR: GOOGLE_API_KEY_SNAP_LOTTERY not found in environment")
            return False
            
        print(f"API Key found: {api_key[:10]}...{api_key[-10:]}")
        
        genai.configure(api_key=api_key)
        
        # Test with a simple prompt
        model = genai.GenerativeModel('gemini-1.5-pro')
        
        response = model.generate_content("Say hello and confirm you are working.")
        print(f"Gemini Response: {response.text}")
        
        return True
        
    except Exception as e:
        print(f"ERROR: {e}")
        return False

if __name__ == "__main__":
    test_gemini_connection()