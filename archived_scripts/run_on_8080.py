#!/usr/bin/env python3
"""
Direct application starter for port 8080
Binds the Flask application directly to port 8080 with Gunicorn
"""
import os
import sys
import signal
import logging
import subprocess
from time import sleep

# Set up logging
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('direct_starter')

# Environment settings
PORT = 8080
WORKERS = 4
TIMEOUT = 120
APP_MODULE = "main:app"

def run_gunicorn():
    """Run the gunicorn server directly on port 8080"""
    logger.info(f"Starting application on port {PORT} with {WORKERS} workers")
    
    # Prepare gunicorn command
    cmd = [
        "gunicorn",
        "--bind", f"0.0.0.0:{PORT}",
        "--workers", str(WORKERS),
        "--timeout", str(TIMEOUT),
        "--reuse-port",  # Important for Replit to allow restarting
        "--reload",      # Auto-reload on code changes
        APP_MODULE
    ]
    
    try:
        logger.info(f"Executing: {' '.join(cmd)}")
        process = subprocess.Popen(cmd)
        logger.info(f"Application started with PID {process.pid}")
        
        # Set up signal handlers to cleanly terminate child process
        signal.signal(signal.SIGTERM, lambda sig, frame: handle_signal(sig, frame, process))
        signal.signal(signal.SIGINT, lambda sig, frame: handle_signal(sig, frame, process))
        
        # Wait for process to complete
        process.wait()
        
        if process.returncode != 0:
            logger.error(f"Application exited with code {process.returncode}")
            return False
        
        logger.info("Application stopped")
        return True
    
    except Exception as e:
        logger.error(f"Error starting application: {e}")
        return False

def handle_signal(signum, frame, process):
    """Handle termination signals"""
    logger.info(f"Received signal {signum}, shutting down application...")
    
    # Forward signal to child process
    if process and process.pid:
        os.kill(process.pid, signum)
        
    # Wait a moment before exiting
    sleep(2)
    sys.exit(0)

if __name__ == "__main__":
    # Start the application
    if not run_gunicorn():
        sys.exit(1)