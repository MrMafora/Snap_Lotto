#!/usr/bin/env python3
"""
Final direct port solution for Replit deployment.
This script starts the application directly on port 8080 without proxies.

Usage:
    python final_direct_port_solution.py
"""

import os
import sys
import signal
import logging
import subprocess
from logger import setup_logger

# Set up logger
logger = setup_logger("final_port_solution", level=logging.INFO)

def run_on_port_8080():
    """Run the application directly on port 8080"""
    logger.info("Starting application directly on port 8080")
    
    try:
        # Set environment variable for port preference
        os.environ["DIRECT_PORT"] = "8080"
        
        # Build the gunicorn command
        cmd = [
            "gunicorn",
            "--bind", "0.0.0.0:8080",
            "--workers", "1",
            "--timeout", "600",
            "--reload",
            "main:app"
        ]
        
        # Log the command we're about to run
        logger.info(f"Running command: {' '.join(cmd)}")
        
        # Start gunicorn process
        process = subprocess.Popen(cmd)
        
        # Signal handler for clean shutdown
        def signal_handler(sig, frame):
            logger.info("Shutdown signal received, stopping application")
            process.terminate()
            sys.exit(0)
        
        # Register signal handlers
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
        
        # Wait for the process to complete
        return_code = process.wait()
        
        if return_code != 0:
            logger.error(f"Application exited with code {return_code}")
            sys.exit(return_code)
            
    except Exception as e:
        logger.error(f"Error starting application: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    logger.info("Starting direct port 8080 solution")
    run_on_port_8080()