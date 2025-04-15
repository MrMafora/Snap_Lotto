#!/usr/bin/env python3
"""
Direct port binding solution for Flask applications on Replit.
This script starts a Flask application on both port 5000 and port 8080 simultaneously.
"""
import os
import sys
import threading
import time
import logging
import signal
import subprocess

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(), logging.FileHandler('direct_binding.log')]
)
logger = logging.getLogger('direct_binding')

def run_on_port(port, app_module="main:app"):
    """Run Gunicorn on the specified port"""
    try:
        cmd = ["gunicorn", "--bind", f"0.0.0.0:{port}", app_module]
        if port == 5000:
            # Only add reload flag for development port
            cmd.append("--reload")
            
        logger.info(f"Starting application on port {port} with command: {' '.join(cmd)}")
        process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        
        # Log output from the process
        for line in iter(process.stdout.readline, b''):
            logger.info(f"Port {port}: {line.decode().strip()}")
            
        return process
    except Exception as e:
        logger.error(f"Failed to start application on port {port}: {str(e)}")
        return None

def start_application():
    """Start the application on both ports"""
    # Start on port 8080
    port_8080_process = run_on_port(8080)
    if not port_8080_process:
        logger.error("Failed to start application on port 8080")
        return False
    
    # Start on port 5000
    port_5000_process = run_on_port(5000)
    if not port_5000_process:
        logger.error("Failed to start application on port 5000")
        # Kill the 8080 process if 5000 fails
        port_8080_process.terminate()
        return False
    
    logger.info("Application successfully started on ports 5000 and 8080")
    
    # Monitor the processes
    try:
        while True:
            # Check if processes are still running
            if port_8080_process.poll() is not None:
                logger.error(f"Port 8080 process exited with code: {port_8080_process.poll()}")
                # Restart the process
                port_8080_process = run_on_port(8080)
                
            if port_5000_process.poll() is not None:
                logger.error(f"Port 5000 process exited with code: {port_5000_process.poll()}")
                # Restart the process
                port_5000_process = run_on_port(5000)
                
            time.sleep(5)  # Check every 5 seconds
    except KeyboardInterrupt:
        logger.info("Received keyboard interrupt, shutting down...")
    finally:
        # Clean up processes
        try:
            port_8080_process.terminate()
            port_5000_process.terminate()
        except:
            pass
    
    return True

if __name__ == "__main__":
    # Set up signal handlers
    def signal_handler(sig, frame):
        logger.info(f"Received signal {sig}, shutting down...")
        sys.exit(0)
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Start the application
    start_application()