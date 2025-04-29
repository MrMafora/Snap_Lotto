#!/usr/bin/env python3
"""
Restart script for the optimized server.
This script:
1. Kills all existing Python processes
2. Starts the server directly on port 8080
3. Avoids using multiple concurrent workers
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
    filename='restart.log'
)
logger = logging.getLogger('restart_optimized')

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
        
        return True
    except Exception as e:
        logger.error(f"Error killing processes: {e}")
        return False

def start_server():
    """Start the Gunicorn server directly on port 8080"""
    logger.info("Starting server directly on port 8080...")
    
    try:
        # Run gunicorn directly with optimized settings
        cmd = [
            'gunicorn',
            '--bind', '0.0.0.0:8080',
            '--workers', '2',              # Only use 2 workers
            '--timeout', '120',            # Longer timeout
            '--keep-alive', '5',           # Short keep-alive
            '--worker-class', 'sync',      # Simpler worker class
            '--log-level', 'info',
            'main:app'
        ]
        
        # Execute the command directly (blocking)
        subprocess.run(cmd)
        
        return True
    except Exception as e:
        logger.error(f"Error starting server: {e}")
        return False

if __name__ == "__main__":
    logger.info("Starting restart process...")
    
    # Kill existing processes
    if not kill_existing_processes():
        logger.error("Failed to kill existing processes")
        sys.exit(1)
    
    # Start server
    if not start_server():
        logger.error("Failed to start server")
        sys.exit(1)
    
    logger.info("Server started successfully")