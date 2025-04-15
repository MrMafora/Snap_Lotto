#!/usr/bin/env python3
"""
Dual port solution for Replit deployments.
This script runs two instances of the Flask application:
1. One on port 5000 (for internal Replit usage)
2. One on port 8080 (for external access)

Usage:
    python dual_port_solution.py

This approach ensures compatibility with both Replit's internal access
and external access requirements.
"""
import subprocess
import sys
import os
import time
import threading
import logging
import signal

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("dual_port")

# Process control
processes = []

def run_on_port(port):
    """Run Gunicorn on the specified port"""
    cmd = [
        "gunicorn",
        "--bind", f"0.0.0.0:{port}",
        "--reuse-port", 
        "--reload",
        "main:app"
    ]
    
    logger.info(f"Starting application on port {port}")
    
    # Start the process
    process = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        universal_newlines=True,
        bufsize=1
    )
    
    # Add to global processes
    processes.append(process)
    
    # Log the output in a separate thread to avoid blocking
    def log_output():
        if process.stdout:
            for line in process.stdout:
                logger.info(f"Port {port}: {line.strip()}")
        
    log_thread = threading.Thread(target=log_output)
    log_thread.daemon = True
    log_thread.start()
    
    # Wait for process to finish (this doesn't block in our case since we're in a thread)
    return_code = process.wait()
    logger.info(f"Process on port {port} exited with code {return_code}")

def start_all_servers():
    """Start both servers in parallel"""
    logger.info("Starting dual port solution")
    
    # Start port 5000 in main thread
    thread_5000 = threading.Thread(target=run_on_port, args=(5000,))
    thread_5000.daemon = True
    thread_5000.start()
    
    # Wait 2 seconds for things to stabilize
    time.sleep(2)
    
    # Start port 8080 in second thread
    thread_8080 = threading.Thread(target=run_on_port, args=(8080,))
    thread_8080.daemon = True
    thread_8080.start()
    
    # Keep the main thread alive
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("Shutdown requested... terminating processes")

def signal_handler(sig, frame):
    """Handle signals gracefully"""
    print("Signal received, exiting...")
    for process in processes:
        if process.poll() is None:  # If process is still running
            process.terminate()
    sys.exit(0)

if __name__ == "__main__":
    # Set up signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Start the dual port solution
    start_all_servers()