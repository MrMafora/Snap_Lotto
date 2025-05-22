#!/usr/bin/env python3
"""
Direct port 8080 starter for Flask application.
This script directly starts the Flask app on port 8080 without using Gunicorn.
"""
import os
import sys
import time
import socket
import logging
from threading import Thread

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('use_port_8080_directly')

def is_port_in_use(port):
    """Check if a port is already in use"""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex(('127.0.0.1', port)) == 0

def start_flask_app():
    """Start the Flask app directly on port 8080"""
    from main import app
    logger.info("Starting Flask directly on port 8080")
    app.run(host='0.0.0.0', port=8080)

if __name__ == "__main__":
    # Set environment variables for port 8080
    os.environ['PORT'] = '8080'
    os.environ['FLASK_RUN_PORT'] = '8080'
    
    # Check if port 8080 is already in use
    if is_port_in_use(8080):
        logger.warning("Port 8080 is already in use, attempting to free it")
        # Kill any process using port 8080
        os.system("fuser -k 8080/tcp 2>/dev/null || true")
        time.sleep(1)
    
    if is_port_in_use(8080):
        logger.error("Port 8080 is still in use after attempt to free it. Cannot start.")
        sys.exit(1)
    
    logger.info("Starting application on port 8080")
    start_flask_app()