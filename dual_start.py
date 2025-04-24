#!/usr/bin/env python3
"""
Start script for the South African Lottery application with dual port binding.
This script starts both the main application on port 5000 and a proxy on port 8080.
"""
import subprocess
import os
import sys
import time
import signal
import threading
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('dual_start')

# Process handle for the main application
main_app_process = None
proxy_process = None

def handle_signal(signum, frame):
    """Handle termination signals by cleaning up child processes"""
    global main_app_process, proxy_process
    
    logger.info(f"Received signal {signum}, shutting down...")
    
    # Terminate the main app process if it exists
    if main_app_process:
        logger.info(f"Terminating main application (PID: {main_app_process.pid})")
        try:
            main_app_process.terminate()
            # Give it a moment to terminate gracefully
            time.sleep(1)
            # Force kill if still running
            if main_app_process.poll() is None:
                main_app_process.kill()
        except Exception as e:
            logger.error(f"Error terminating main app: {e}")
    
    # Terminate the proxy process if it exists
    if proxy_process:
        logger.info(f"Terminating proxy (PID: {proxy_process.pid})")
        try:
            proxy_process.terminate()
            # Give it a moment to terminate gracefully
            time.sleep(1)
            # Force kill if still running
            if proxy_process.poll() is None:
                proxy_process.kill()
        except Exception as e:
            logger.error(f"Error terminating proxy: {e}")
    
    # Exit cleanly
    sys.exit(0)

def start_main_app():
    """Start the main Flask application on port 5000"""
    global main_app_process
    
    cmd = "gunicorn --bind 0.0.0.0:5000 --reuse-port --reload main:app"
    logger.info(f"Starting main application: {cmd}")
    
    try:
        main_app_process = subprocess.Popen(
            cmd,
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            universal_newlines=True
        )
        logger.info(f"Main application started with PID {main_app_process.pid}")
        
        # Start a thread to monitor the output
        def monitor_output():
            for line in main_app_process.stdout:
                logger.info(f"[MAIN APP] {line.strip()}")
        
        threading.Thread(target=monitor_output, daemon=True).start()
        
        return True
    except Exception as e:
        logger.error(f"Failed to start main application: {e}")
        return False

def start_proxy():
    """Start the HTTP proxy server on port 8080"""
    global proxy_process
    
    try:
        # Start the dual_port_server.py script as a separate process
        cmd = "python dual_port_server.py"
        logger.info(f"Starting proxy server: {cmd}")
        
        proxy_process = subprocess.Popen(
            cmd,
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            universal_newlines=True
        )
        logger.info(f"Proxy server started with PID {proxy_process.pid}")
        
        # Start a thread to monitor the output
        def monitor_output():
            for line in proxy_process.stdout:
                logger.info(f"[PROXY] {line.strip()}")
        
        threading.Thread(target=monitor_output, daemon=True).start()
        
        return True
    except Exception as e:
        logger.error(f"Failed to start proxy server: {e}")
        return False

def wait_for_port(port, max_wait=30):
    """Wait for a port to become available"""
    import socket
    
    logger.info(f"Waiting for port {port} to become available...")
    
    start_time = time.time()
    while time.time() - start_time < max_wait:
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.settimeout(1)
                s.connect(('localhost', port))
                logger.info(f"Port {port} is now available")
                return True
        except (socket.timeout, ConnectionRefusedError):
            time.sleep(1)
    
    logger.warning(f"Timed out waiting for port {port}")
    return False

def main():
    """Main entry point"""
    # Set up signal handlers for graceful shutdown
    signal.signal(signal.SIGINT, handle_signal)
    signal.signal(signal.SIGTERM, handle_signal)
    
    logger.info("Starting South African Lottery application with dual port binding")
    
    # Start the main application
    if not start_main_app():
        logger.error("Failed to start main application, exiting")
        return 1
    
    # Wait for the main application to start
    if not wait_for_port(5000):
        logger.warning("Main application may not have started correctly")
    
    # Start the proxy server
    if not start_proxy():
        logger.error("Failed to start proxy server, exiting")
        return 1
    
    # Wait for the proxy server to start
    if not wait_for_port(8080):
        logger.warning("Proxy server may not have started correctly")
    
    logger.info("South African Lottery application is now running")
    logger.info("Main application available on port 5000")
    logger.info("Proxy server available on port 8080")
    
    # Monitor child processes and keep the script running
    try:
        while True:
            # Check if main app is still running
            if main_app_process and main_app_process.poll() is not None:
                logger.error("Main application has terminated unexpectedly")
                logger.info("Attempting to restart main application...")
                if not start_main_app():
                    logger.error("Failed to restart main application")
                    break
            
            # Check if proxy is still running
            if proxy_process and proxy_process.poll() is not None:
                logger.error("Proxy server has terminated unexpectedly")
                logger.info("Attempting to restart proxy server...")
                if not start_proxy():
                    logger.error("Failed to restart proxy server")
                    break
            
            # Sleep for a bit before checking again
            time.sleep(5)
    except KeyboardInterrupt:
        logger.info("Interrupted by user")
        handle_signal(signal.SIGINT, None)
    
    return 0

if __name__ == "__main__":
    sys.exit(main())