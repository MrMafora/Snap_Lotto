#!/usr/bin/env python3
"""
Script to run the main application and port proxy together
"""
import os
import sys
import time
import signal
import subprocess
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('run_with_proxy')

# Process handles
main_app_process = None
proxy_process = None

def signal_handler(sig, frame):
    """Handle termination signals"""
    logger.info("Shutting down services...")
    
    if proxy_process:
        logger.info("Terminating proxy process")
        proxy_process.terminate()
        proxy_process.wait()
    
    if main_app_process:
        logger.info("Terminating main application process")
        main_app_process.terminate()
        main_app_process.wait()
    
    logger.info("All processes terminated")
    sys.exit(0)

def start_main_app():
    """Start the main application"""
    logger.info("Starting main application on port 5000")
    
    # Configure environment
    env = os.environ.copy()
    env['PORT'] = '5000'
    
    # Start Gunicorn
    cmd = [
        "gunicorn",
        "--bind", "0.0.0.0:5000",
        "--worker-class", "gthread",
        "--workers", "2",
        "main:app"
    ]
    
    logger.info(f"Executing: {' '.join(cmd)}")
    
    # Start process
    return subprocess.Popen(
        cmd,
        env=env,
        stdout=sys.stdout,
        stderr=sys.stderr
    )

def start_port_proxy():
    """Start the port proxy"""
    logger.info("Starting port proxy on port 8080")
    
    # Configure environment
    env = os.environ.copy()
    env['PORT'] = '8080'
    
    # Start proxy
    cmd = ["python", "flask_port_proxy.py"]
    
    logger.info(f"Executing: {' '.join(cmd)}")
    
    # Start process
    return subprocess.Popen(
        cmd,
        env=env,
        stdout=sys.stdout,
        stderr=sys.stderr
    )

if __name__ == "__main__":
    # Register signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    try:
        # Start main application
        main_app_process = start_main_app()
        
        # Wait a few seconds for the main app to start
        logger.info("Waiting for main app to initialize...")
        time.sleep(3)
        
        # Start port proxy
        proxy_process = start_port_proxy()
        
        # Print message
        logger.info("""
==========================================================
RUNNING APPLICATION WITH PORT PROXY
==========================================================
Main application: http://localhost:5000 (internal)
Port proxy: http://localhost:8080 (public)
==========================================================
""")
        
        # Wait for processes to exit
        main_exit_code = main_app_process.wait()
        logger.error(f"Main application exited with code {main_exit_code}")
        
        # If we get here, terminate the proxy as well
        if proxy_process:
            logger.info("Terminating proxy process after main app exit")
            proxy_process.terminate()
            proxy_process.wait()
    
    except Exception as e:
        logger.error(f"Error: {e}")
        signal_handler(None, None)  # Cleanup