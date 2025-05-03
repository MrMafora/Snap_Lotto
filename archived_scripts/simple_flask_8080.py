#!/usr/bin/env python3
"""
Simple Flask starter that directly runs on port 8080
"""
import os
import sys

# Force port to 8080
os.environ['PORT'] = '8080'
os.environ['FLASK_RUN_PORT'] = '8080'

# Import the Flask app
from main import app

if __name__ == '__main__':
    print(f"Starting Flask application directly on port 8080", file=sys.stderr)
    app.run(host='0.0.0.0', port=8080, debug=True)