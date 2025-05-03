#!/usr/bin/env python3
"""
Direct Gunicorn Starter for port 8080 binding
This script directly configures and starts Gunicorn to bind on port 8080
"""
import os
import sys
import signal
import logging
import subprocess

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('direct_gunicorn_start')

def signal_handler(sig, frame):
    """Handle termination signals"""
    logger.info(f"Received signal {sig}, shutting down")
    sys.exit(0)

def run_gunicorn():
    """Start Gunicorn server directly on port 8080"""
    logger.info("Starting Gunicorn directly on port 8080")
    
    # Force port to be 8080
    os.environ['PORT'] = '8080'
    os.environ['FLASK_RUN_PORT'] = '8080'
    os.environ['GUNICORN_PORT'] = '8080'
    
    # Command to run Gunicorn
    cmd = [
        "gunicorn",
        "--bind", "0.0.0.0:8080",  # Explicitly bind to port 8080
        "--workers", "2",
        "--threads", "2",
        "--worker-class", "gthread",
        "--log-level", "info",
        "--reload",
        "main:app"
    ]
    
    logger.info(f"Running command: {' '.join(cmd)}")
    
    try:
        # Execute Gunicorn directly
        process = subprocess.Popen(cmd)
        logger.info(f"Gunicorn started with PID {process.pid}")
        process.wait()
    except Exception as e:
        logger.error(f"Error starting Gunicorn: {e}")
        sys.exit(1)

if __name__ == "__main__":
    # Register signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    logger.info("Starting direct Gunicorn launcher")
    run_gunicorn()