#!/usr/bin/env python3
"""
Script to run the application with optimized settings.
This script:
1. Uses gunicorn directly with optimized settings
2. Binds directly to port 8080 instead of using a proxy
3. Uses significantly fewer worker processes
4. Optimizes memory usage and performance
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
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('run_optimized')

def handle_signal(signum, frame):
    """Handle termination signals"""
    logger.info(f"Received signal {signum}, shutting down...")
    sys.exit(0)

def kill_existing_processes():
    """Kill any existing Python processes"""
    logger.info("Killing existing Python processes...")
    try:
        subprocess.run(['pkill', '-9', 'python'], check=False)
        subprocess.run(['pkill', '-9', 'gunicorn'], check=False)
        time.sleep(2)  # Give processes time to terminate
        return True
    except Exception as e:
        logger.error(f"Error killing processes: {e}")
        return False

def run_optimized_server():
    """Run the server with optimized settings"""
    logger.info("Starting optimized server on port 8080...")
    
    # Only use 4 worker processes to avoid resource contention
    worker_count = "4"
    
    # Use gunicorn directly on port 8080
    cmd = [
        'gunicorn',
        '--bind', '0.0.0.0:8080',
        '--workers', worker_count,
        '--timeout', '120',
        '--keep-alive', '5',
        '--worker-class', 'gthread',
        '--threads', '4',
        '--forwarded-allow-ips', '*',
        '--log-level', 'info',
        'main:app'
    ]
    
    try:
        # Use Popen to start server in the background
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            universal_newlines=True
        )
        
        logger.info(f"Server started with PID: {process.pid}")
        
        # Check if process started successfully
        time.sleep(3)
        if process.poll() is not None:
            output, _ = process.communicate()
            logger.error(f"Server failed to start: {output}")
            return False
            
        return True
    except Exception as e:
        logger.error(f"Error starting server: {e}")
        return False

if __name__ == "__main__":
    # Register signal handlers
    signal.signal(signal.SIGINT, handle_signal)
    signal.signal(signal.SIGTERM, handle_signal)
    
    # Kill existing processes
    if not kill_existing_processes():
        logger.error("Failed to kill existing processes")
        sys.exit(1)
    
    # Start optimized server
    if not run_optimized_server():
        logger.error("Failed to start optimized server")
        sys.exit(1)
    
    logger.info("Optimized server running on port 8080")
    
    # Keep the script running to maintain logging and signal handling
    while True:
        time.sleep(60)