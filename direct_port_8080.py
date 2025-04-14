"""
DIRECT PORT 8080 BINDING FOR REPLIT

This is a direct binding solution that starts the Flask application
directly on port 8080 without relying on proxies or redirects.
"""
import os
import sys
import time
import threading
from werkzeug.serving import run_simple

# Add the current directory to the path so we can import the app
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def start_app():
    """Start the Flask application directly on port 8080"""
    from main import app
    
    # Run the Flask application on port 8080
    run_simple('0.0.0.0', 8080, app, use_reloader=True, use_debugger=True)

if __name__ == "__main__":
    print("Starting application directly on port 8080...")
    start_app()