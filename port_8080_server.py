#!/usr/bin/env python3
"""
Simple, direct port 8080 server for Replit deployment.
This is a standalone server that runs the application on port 8080.
"""

import os
import sys
import subprocess
import signal
import logging
import time

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('port_8080_server')

def run_server():
    """Run the Flask application directly on port 8080"""
    
    # Register signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    logger.info("Starting server on port 8080...")
    
    # Command to start gunicorn on port 8080
    cmd = [
        "gunicorn",
        "--bind", "0.0.0.0:8080",
        "--workers=4",
        "--timeout=120",
        "--reuse-port",
        "--reload",
        "main:app"
    ]
    
    try:
        # Start the server process
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            universal_newlines=True
        )
        
        # Log the process ID
        logger.info(f"Server started with PID: {process.pid}")
        
        # Monitor process without relying on stdout iteration
        try:
            while True:
                output = process.stdout.readline()
                if output == '' and process.poll() is not None:
                    break
                if output:
                    logger.info(output.strip())
        except AttributeError:
            # If stdout is not available for reading
            logger.info("Process output monitoring not available")
        
        # Wait for the process to complete
        return_code = process.wait()
        if return_code != 0:
            logger.error(f"Server process exited with code {return_code}")
            sys.exit(return_code)
            
    except Exception as e:
        logger.error(f"Error starting server: {str(e)}")
        sys.exit(1)

def signal_handler(sig, frame):
    """Handle signals gracefully"""
    logger.info("Shutting down server")
    sys.exit(0)

if __name__ == "__main__":
    run_server()