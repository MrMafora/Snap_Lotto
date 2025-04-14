"""
Ultra-lightweight Flask server that starts instantly for Replit preview
and then redirects to the main application on port 8080.
"""
import threading
import time
import os
import sys
import signal
from flask import Flask, redirect

# Create a minimal Flask application that starts instantly
app = Flask(__name__)

@app.route('/')
def home():
    """Redirect to the main application"""
    return redirect('http://localhost:8080/')

@app.route('/<path:path>')
def catch_all(path):
    """Redirect all paths to the main application"""
    return redirect(f'http://localhost:8080/{path}')

def start_main_app():
    """Start the main Flask application on port 8080"""
    # Wait briefly to ensure the preview server is running
    time.sleep(1)
    
    print("Starting the main Flask application on port 8080...")
    
    # Start the main application with the proper port
    os.system("python3 main.py replit_preview.py")

if __name__ == '__main__':
    # Start the main application in a background thread
    main_app_thread = threading.Thread(target=start_main_app)
    main_app_thread.daemon = True
    main_app_thread.start()
    
    # Start the minimal Flask app on port 5000
    print("Starting lightweight Flask server on port 5000...")
    app.run(host='0.0.0.0', port=5000, threaded=True)