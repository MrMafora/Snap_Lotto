#!/usr/bin/env python3
"""
Dual-port server starter for a Flask application.
This script explicitly starts the Flask application on both port 5000 and port 8080
without relying on gunicorn or other middlewares.
"""
import os
import sys
import threading
import time
import logging
import signal
import subprocess
from multiprocessing import Process
import socket

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(), logging.FileHandler('dual_server.log')]
)
logger = logging.getLogger('dual_server')

def is_port_in_use(port):
    """Check if a port is in use"""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex(('localhost', port)) == 0

def kill_process_on_port(port):
    """Kill any process using the specified port"""
    try:
        # Find process ID using the port
        cmd = f"fuser -k {port}/tcp"
        subprocess.run(cmd, shell=True, stderr=subprocess.DEVNULL)
        logger.info(f"Killed process on port {port}")
        # Give it a moment to release the port
        time.sleep(1)
    except Exception as e:
        logger.error(f"Failed to kill process on port {port}: {str(e)}")

def start_server_on_port(port):
    """Start a Flask server on the specified port"""
    try:
        logger.info(f"Starting Flask server on port {port}")
        
        # Import the Flask app
        import main
        from main import app
        
        # Use a process to run the Flask app
        def run_flask():
            app.run(host="0.0.0.0", port=port, debug=False, use_reloader=False)
        
        process = Process(target=run_flask)
        process.daemon = True
        process.start()
        
        # Check if the server started successfully
        for _ in range(10):  # Wait up to 10 seconds
            if is_port_in_use(port):
                logger.info(f"Server started successfully on port {port}")
                return process
            time.sleep(1)
        
        logger.error(f"Failed to start server on port {port}")
        process.terminate()
        return None
    except Exception as e:
        logger.error(f"Error starting server on port {port}: {str(e)}")
        return None

def start_dual_server():
    """Start servers on both ports 5000 and 8080"""
    # First, make sure no processes are using our ports
    for port in [5000, 8080]:
        if is_port_in_use(port):
            logger.info(f"Port {port} is already in use. Attempting to kill the process.")
            kill_process_on_port(port)
    
    # Start on port 5000
    logger.info("Starting server on port 5000...")
    port_5000_process = start_server_on_port(5000)
    
    if not port_5000_process:
        logger.error("Failed to start server on port 5000. Exiting.")
        return False
    
    # Start on port 8080
    logger.info("Starting server on port 8080...")
    port_8080_process = start_server_on_port(8080)
    
    if not port_8080_process:
        logger.error("Failed to start server on port 8080. Terminating port 5000 server.")
        port_5000_process.terminate()
        return False
    
    logger.info("Both servers started successfully!")
    
    try:
        # Keep the main thread running
        while True:
            time.sleep(1)
            # Check if processes are still running
            if not port_5000_process.is_alive():
                logger.error("Port 5000 process died. Restarting...")
                port_5000_process.terminate()
                port_5000_process = start_server_on_port(5000)
                if not port_5000_process:
                    logger.error("Failed to restart server on port 5000.")
                    port_8080_process.terminate()
                    return False
            
            if not port_8080_process.is_alive():
                logger.error("Port 8080 process died. Restarting...")
                port_8080_process.terminate()
                port_8080_process = start_server_on_port(8080)
                if not port_8080_process:
                    logger.error("Failed to restart server on port 8080.")
                    port_5000_process.terminate()
                    return False
            
    except KeyboardInterrupt:
        logger.info("Received keyboard interrupt. Shutting down...")
    finally:
        # Clean up processes
        for process in [port_5000_process, port_8080_process]:
            if process and process.is_alive():
                process.terminate()
        
        logger.info("Servers shut down.")
    
    return True

if __name__ == "__main__":
    logger.info("Starting dual-port server...")
    
    # Set up signal handlers
    def signal_handler(sig, frame):
        logger.info(f"Received signal {sig}. Shutting down...")
        sys.exit(0)
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    try:
        start_dual_server()
    except Exception as e:
        logger.error(f"Error in dual server: {str(e)}")
        sys.exit(1)