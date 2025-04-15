"""
This script runs a background process that binds to port 8080
and forwards requests to the main application on port 5000.
It's designed to be run automatically at application startup.
"""
from flask import Flask, request, redirect
import threading
import time
import os
import sys

# Create a simple Flask application for port 8080
app = Flask(__name__)

@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def catch_all(path):
    """Redirect all requests to the main application on port 5000"""
    # Get the original URL and replace the port number
    url_parts = request.url.split(':', 2)
    if len(url_parts) >= 3:
        # Replace port number (after second colon)
        redirect_url = f"{url_parts[0]}:{url_parts[1]}:5000{request.path}"
        if request.query_string:
            redirect_url += f"?{request.query_string.decode()}"
    else:
        # Fallback to hard-coded redirect
        host = request.headers.get('Host', '').split(':')[0]
        redirect_url = f"http://{host}:5000{request.path}"
        if request.query_string:
            redirect_url += f"?{request.query_string.decode()}"
    
    return redirect(redirect_url, code=302)

def run_flask_app():
    """Run the Flask application on port 8080"""
    try:
        app.run(host='0.0.0.0', port=8080, debug=False, use_reloader=False)
    except Exception as e:
        print(f"Error starting bridge on port 8080: {str(e)}")

if __name__ == "__main__":
    print("Starting port 8080 bridge application...")
    
    # Start the Flask app in a separate thread
    flask_thread = threading.Thread(target=run_flask_app)
    flask_thread.daemon = True
    flask_thread.start()
    
    print(f"Port 8080 bridge started successfully")
    
    # Keep the script running
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("Shutting down port 8080 bridge...")
        sys.exit(0)