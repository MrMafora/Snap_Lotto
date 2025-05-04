#!/usr/bin/env python3
"""
Start script for the optimized server.
This script:
1. Kills all existing Python processes
2. Starts Gunicorn with our optimized configuration
3. Binds directly to port 8080
4. Features improved logging and error handling
"""
import os
import signal
import subprocess
import sys
import time
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    filename='optimized.log'
)
logger = logging.getLogger('start_optimized')

def kill_existing_processes():
    """Kill all existing Python and Gunicorn processes"""
    logger.info("Killing existing Python processes...")
    
    try:
        # First try a gentle terminate
        subprocess.run(['pkill', 'python'], check=False)
        subprocess.run(['pkill', 'gunicorn'], check=False)
        
        # Wait a moment for processes to terminate
        time.sleep(1)
        
        # Then force kill any remaining
        subprocess.run(['pkill', '-9', 'python'], check=False)
        subprocess.run(['pkill', '-9', 'gunicorn'], check=False)
        
        # Wait again to ensure all processes are terminated
        time.sleep(2)
        
        # Check if any Python processes are still running
        result = subprocess.run(['pgrep', 'python'], capture_output=True, text=True)
        if result.stdout.strip():
            logger.warning(f"Some Python processes still running: {result.stdout.strip()}")
        
        return True
    except Exception as e:
        logger.error(f"Error killing processes: {e}")
        return False

def start_server():
    """Start the Gunicorn server with optimized configuration"""
    logger.info("Starting server with optimized configuration...")
    
    try:
        # Run gunicorn with our optimized configuration file
        cmd = [
            'gunicorn',
            '-c', 'gunicorn_optimized.conf.py',
            'main:app'
        ]
        
        # Start the process and detach
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            universal_newlines=True
        )
        
        # Log the server start
        logger.info(f"Server started with PID: {process.pid}")
        
        # Wait a moment to make sure it's starting properly
        time.sleep(3)
        
        # Check if the process is still running
        if process.poll() is not None:
            # Process already exited
            output, _ = process.communicate()
            logger.error(f"Server failed to start. Output: {output}")
            return False
        
        # Check if the port is now being used
        port_check = subprocess.run(
            ['lsof', '-i', ':8080'],
            capture_output=True,
            text=True
        )
        
        if "gunicorn" in port_check.stdout:
            logger.info("Gunicorn successfully bound to port 8080")
        else:
            logger.warning("Port 8080 might not be properly bound")
        
        return True
    except Exception as e:
        logger.error(f"Error starting server: {e}")
        return False

if __name__ == "__main__":
    # Catch all common signals
    for sig in [signal.SIGINT, signal.SIGTERM]:
        signal.signal(sig, lambda s, f: sys.exit(0))
    
    logger.info("Starting optimized server process...")
    
    # Kill existing processes
    if not kill_existing_processes():
        logger.error("Failed to kill existing processes")
        sys.exit(1)
    
    # Start server
    if not start_server():
        logger.error("Failed to start server")
        sys.exit(1)
    
    logger.info("Server started successfully - leaving startup script")
    
    # Return success
    sys.exit(0)