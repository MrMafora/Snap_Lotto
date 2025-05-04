#!/usr/bin/env python3
"""
Simple starter script for Flask application.
Forces binding to port 8080 by overriding Flask's run method.
"""
import os
import sys
from main import app

if __name__ == "__main__":
    print("Starting application on port 8080")
    # Set port in environment variable
    os.environ['PORT'] = '8080'
    
    # Run the Flask application directly
    app.run(host='0.0.0.0', port=8080, debug=True)