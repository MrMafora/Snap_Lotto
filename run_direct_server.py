#!/usr/bin/env python3
"""
Run script that stops all Python processes and starts the optimized server.
This ensures we don't have multiple competing server instances.
"""
import os
import subprocess
import time
import sys
import logging
import signal

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('run_direct_server')

def handle_signal(signum, frame):
    """Handle termination signals"""
    logger.info(f"Received signal {signum}, shutting down...")
    sys.exit(0)

def kill_python_processes():
    """Kill all running Python processes to avoid conflicts"""
    logger.info("Stopping all existing Python processes...")
    try:
        # Force kill all Python processes - this is aggressive but effective
        subprocess.run(['pkill', '-9', 'python'], check=False)
        # Give processes time to shut down
        time.sleep(2)
        return True
    except Exception as e:
        logger.error(f"Error stopping Python processes: {e}")
        return False

def start_optimized_server():
    """Start our optimized server on port 8080"""
    logger.info("Starting optimized server on port 8080...")
    try:
        # Use subprocess to start our optimized server
        server_process = subprocess.Popen(
            ['python', 'optimized_server.py'],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            universal_newlines=True
        )
        
        # Log the first few lines to confirm startup
        logger.info("Server started with PID: {}".format(server_process.pid))
        
        # Check if process is still running after a short delay
        time.sleep(2)
        if server_process.poll() is not None:
            # Process already exited
            output, _ = server_process.communicate()
            logger.error(f"Server failed to start. Output: {output}")
            return False
        
        logger.info("Server successfully started on port 8080")
        return True
    except Exception as e:
        logger.error(f"Error starting server: {e}")
        return False

def main():
    """Main function"""
    # Register signal handlers
    signal.signal(signal.SIGINT, handle_signal)
    signal.signal(signal.SIGTERM, handle_signal)
    
    # Kill existing processes
    if not kill_python_processes():
        logger.error("Failed to stop existing processes")
        return 1
    
    # Start optimized server
    if not start_optimized_server():
        logger.error("Failed to start optimized server")
        return 1
    
    logger.info("Direct server setup complete")
    return 0

if __name__ == "__main__":
    sys.exit(main())