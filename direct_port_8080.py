"""
Direct port 8080 binding for Replit deployment.
This script runs the Flask application directly on port 8080.
"""

import os
import sys
import subprocess
import signal
import time
import logging

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("direct_port_8080")

def run_on_port_8080():
    """Run the application directly on port 8080"""
    try:
        logger.info("Starting application on port 8080")
        
        # Define the gunicorn command to run the app on port 8080
        cmd = [
            "gunicorn",
            "--bind", "0.0.0.0:8080",
            "--workers=4",
            "--reuse-port",
            "--reload",
            "main:app"
        ]
        
        # Function to handle signals
        def signal_handler(sig, frame):
            logger.info(f"Received signal {sig}, shutting down...")
            if process:
                process.terminate()
                process.wait()
            sys.exit(0)
        
        # Register signal handlers
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
        
        # Start the process
        process = subprocess.Popen(cmd)
        logger.info(f"Started gunicorn on port 8080 with PID: {process.pid}")
        
        # Wait for the process to complete
        process.wait()
        
    except Exception as e:
        logger.error(f"Error running application on port 8080: {e}")
        sys.exit(1)

if __name__ == "__main__":
    run_on_port_8080()