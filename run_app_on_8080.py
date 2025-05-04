#!/usr/bin/env python3
"""
Direct Flask app runner on port 8080
This script bypasses Gunicorn and runs Flask directly on port 8080
"""
import os
import sys
import signal
import socket
import logging
import time

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('run_app_on_8080')

def is_port_in_use(port):
    """Check if a port is already in use"""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex(('127.0.0.1', port)) == 0

def handle_signal(sig, frame):
    """Handle termination signals"""
    logger.info(f"Received signal {sig}, shutting down")
    sys.exit(0)

if __name__ == "__main__":
    # Register signal handlers
    signal.signal(signal.SIGINT, handle_signal)
    signal.signal(signal.SIGTERM, handle_signal)
    
    # Make sure the port is free
    if is_port_in_use(8080):
        logger.warning("Port 8080 is already in use, attempting to free it")
        os.system("fuser -k 8080/tcp 2>/dev/null || true")
        time.sleep(1)
    
    # Force Flask to use port 8080
    os.environ['PORT'] = '8080'
    os.environ['FLASK_RUN_PORT'] = '8080'
    os.environ['GUNICORN_PORT'] = '8080'
    
    # Import the Flask app
    logger.info("Starting Flask app directly on port 8080")
    
    # Import the app
    try:
        from main import app
        app.run(host='0.0.0.0', port=8080, debug=True, use_reloader=True)
    except Exception as e:
        logger.error(f"Error starting Flask app: {e}")
        sys.exit(1)