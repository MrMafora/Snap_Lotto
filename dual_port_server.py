#!/usr/bin/env python3
"""
Dual port server for Replit deployments.
This script starts a Flask application on both port 5000 and port 8080.
"""
import threading
import subprocess
import os
import signal
import sys
import time
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('dual_port_server')

def run_on_port(port, app_module="main:app"):
    """Run Gunicorn on the specified port"""
    try:
        cmd = ["gunicorn", "--bind", f"0.0.0.0:{port}", "--reuse-port", app_module]
        logger.info(f"Starting server on port {port} with command: {' '.join(cmd)}")
        
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            universal_newlines=True
        )
        
        # Store process for cleanup
        return process
    except Exception as e:
        logger.error(f"Failed to start server on port {port}: {str(e)}")
        return None

def main():
    """Start servers on both ports"""
    # List to store all processes for cleanup
    processes = []
    
    try:
        # Start server on port 5000 (main application)
        process_5000 = run_on_port(5000)
        if process_5000:
            processes.append(process_5000)
            logger.info("Server started on port 5000")
        
        # Start server on port 8080 (for Replit deployment)
        process_8080 = run_on_port(8080)
        if process_8080:
            processes.append(process_8080)
            logger.info("Server started on port 8080")
        
        if processes:
            logger.info(f"Server is ready and listening on ports 5000 and 8080")
            print("Server is ready and listening on ports 5000 and 8080")
        else:
            logger.error("Failed to start servers")
            return
        
        # Keep running until interrupted
        while all(p.poll() is None for p in processes):
            time.sleep(1)
        
        # If we get here, at least one process has terminated unexpectedly
        for p in processes:
            if p.poll() is not None:
                logger.error(f"Process {p.pid} terminated unexpectedly with code {p.poll()}")
        
    except KeyboardInterrupt:
        logger.info("Shutdown requested")
    finally:
        # Clean up processes
        for p in processes:
            if p.poll() is None:  # If still running
                logger.info(f"Terminating process {p.pid}")
                p.terminate()
                try:
                    p.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    logger.warning(f"Process {p.pid} did not terminate, killing")
                    p.kill()

def signal_handler(sig, frame):
    """Handle signals gracefully"""
    logger.info(f"Received signal {sig}, shutting down")
    sys.exit(0)

if __name__ == "__main__":
    # Register signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    main()