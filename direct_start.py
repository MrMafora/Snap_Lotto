#!/usr/bin/env python3
"""
Direct application startup script to bypass port conflicts
"""
import sys
import os
import signal
import time

def cleanup_ports():
    """Clean up any existing processes on port 5000"""
    import subprocess
    try:
        # Kill any existing gunicorn processes
        subprocess.run(['pkill', '-f', 'gunicorn'], check=False, capture_output=True)
        subprocess.run(['pkill', '-f', 'python.*main'], check=False, capture_output=True)
        time.sleep(1)
    except:
        pass

def start_application():
    """Start the Flask application directly"""
    cleanup_ports()
    
    # Set environment variables for proper startup
    os.environ['FLASK_ENV'] = 'production'
    os.environ['FLASK_DEBUG'] = 'False'
    
    # Import and run the main application
    try:
        import main
        print("Starting Flask application on 0.0.0.0:5000")
        main.app.run(host="0.0.0.0", port=5000, debug=False, use_reloader=False, threaded=True)
    except Exception as e:
        print(f"Application startup error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    start_application()