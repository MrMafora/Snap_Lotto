"""
WORKFLOW DUAL PORT STARTER

This script is used by the workflow to start both the main application
on port 5000 (via Gunicorn) and a redirection server on port 8080.

It ensures that the application is accessible on both ports.
"""
import sys
import os
import logging
import threading
import subprocess
import time

# Import our port binding solution
from port_binding_solution import ensure_port_8080_binding

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("workflow_starter")

def start_gunicorn():
    """Start Gunicorn on port 5000"""
    try:
        logger.info("Starting Gunicorn on port 5000")
        
        # Use the same command as the workflow
        cmd = ["gunicorn", "--bind", "0.0.0.0:5000", "--reuse-port", "--reload", "main:app"]
        
        # Start Gunicorn as a subprocess
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            universal_newlines=True
        )
        
        # Monitor Gunicorn output
        for line in process.stdout:
            print(line, end='')  # Print to console as well
            
        # If we get here, Gunicorn has exited
        logger.error("Gunicorn process has exited unexpectedly")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Error starting Gunicorn: {e}")
        sys.exit(1)

if __name__ == "__main__":
    logger.info("Starting dual-port workflow starter")
    
    # Start port 8080 binding in background thread
    port_8080_ready = ensure_port_8080_binding(target_port=5000)
    if port_8080_ready:
        logger.info("Port 8080 binding ready")
    else:
        logger.warning("Failed to bind to port 8080")
    
    # Start Gunicorn on port 5000
    # This is a blocking call and will only return if Gunicorn exits
    start_gunicorn()