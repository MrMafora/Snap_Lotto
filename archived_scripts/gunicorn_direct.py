#!/usr/bin/env python3
"""
Direct Gunicorn starter that binds to port 8080 with minimal workers
This script:
1. Kills all existing Python processes
2. Starts Gunicorn with 4 workers only
3. Binds directly to port 8080
"""
import logging
import os
import signal
import subprocess
import sys
import time

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('gunicorn_direct')

def kill_existing_processes():
    """Kill all existing Python processes"""
    logger.info("Stopping existing processes")
    
    try:
        subprocess.check_call("pkill -9 python", shell=True)
        time.sleep(2)  # Give time for processes to terminate
    except:
        logger.info("No processes to kill")

def start_gunicorn():
    """Start Gunicorn with minimal workers, directly on port 8080"""
    logger.info("Starting optimized Gunicorn on port 8080")
    
    # Command with all options explicitly set
    cmd = [
        "gunicorn",
        "--bind", "0.0.0.0:8080",
        "--workers", "4",
        "--threads", "2",
        "--worker-class", "gthread",
        "--max-requests", "1000",
        "--timeout", "60",
        "--graceful-timeout", "30",
        "--keep-alive", "30",
        "--log-level", "info",
        "main:app"
    ]
    
    try:
        process = subprocess.Popen(cmd)
        logger.info(f"Gunicorn started with PID: {process.pid}")
        return process.pid
    except Exception as e:
        logger.error(f"Failed to start Gunicorn: {e}")
        return None

def main():
    """Main function"""
    # Register signal handlers for graceful shutdown
    signal.signal(signal.SIGINT, lambda sig, frame: sys.exit(0))
    signal.signal(signal.SIGTERM, lambda sig, frame: sys.exit(0))
    
    # Kill existing processes
    kill_existing_processes()
    
    # Start Gunicorn
    pid = start_gunicorn()
    if not pid:
        return 1
    
    # Keep script running to handle signals
    try:
        logger.info("Server running. Press Ctrl+C to exit.")
        while True:
            # Check if process is still running
            try:
                os.kill(pid, 0)  # Signal 0 checks if process exists
                time.sleep(5)
            except OSError:
                logger.error("Gunicorn process died unexpectedly")
                return 1
    except KeyboardInterrupt:
        logger.info("Received interrupt. Shutting down.")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())