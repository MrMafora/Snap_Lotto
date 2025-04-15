"""
Final solution for port binding in Replit.
This script runs two instances of the Flask application:
1. One on port 5000 (for development)
2. One on port 8080 (for Replit deployment)
"""

import os
import sys
import subprocess
import signal
import time
import logging
import threading

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("final_solution")

# Global process variables
p5000 = None
p8080 = None

def run_on_port(port):
    """Run Gunicorn on the specified port"""
    try:
        cmd = [
            "gunicorn",
            "--bind", f"0.0.0.0:{port}",
            "--workers=2",
            "--reuse-port",
            "--reload",
            "main:app"
        ]
        
        logger.info(f"Starting application on port {port}")
        process = subprocess.Popen(cmd)
        logger.info(f"Started Gunicorn on port {port} with PID: {process.pid}")
        return process
    except Exception as e:
        logger.error(f"Error starting application on port {port}: {e}")
        return None

def run_servers():
    """Run servers on both ports"""
    global p5000, p8080
    
    # Start server on port 5000
    p5000 = run_on_port(5000)
    
    # Start server on port 8080
    p8080 = run_on_port(8080)
    
    logger.info("Both servers are running")

def signal_handler(sig, frame):
    """Handle signals gracefully"""
    logger.info(f"Received signal {sig}, shutting down...")
    
    # Shutdown both processes
    if p5000:
        p5000.terminate()
    if p8080:
        p8080.terminate()
    
    # Wait for processes to terminate
    if p5000:
        p5000.wait()
    if p8080:
        p8080.wait()
    
    logger.info("All servers shut down")
    sys.exit(0)

if __name__ == "__main__":
    # Register signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Start the servers
    run_servers()
    
    # Keep the script running
    try:
        while True:
            time.sleep(1)
            
            # Check if processes are still alive and restart if needed
            if p5000 and p5000.poll() is not None:
                logger.info("Port 5000 process died, restarting...")
                p5000 = run_on_port(5000)
            
            if p8080 and p8080.poll() is not None:
                logger.info("Port 8080 process died, restarting...")
                p8080 = run_on_port(8080)
    except KeyboardInterrupt:
        signal_handler(signal.SIGINT, None)