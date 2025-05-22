#!/usr/bin/env python3
"""
Automatically starts the port proxy in the background
This script should be imported in main.py to ensure the proxy is always running
"""
import os
import sys
import time
import atexit
import signal
import logging
import threading
import subprocess

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('auto_proxy')

# Proxy process
proxy_process = None

def start_proxy():
    """Start the port proxy in a separate process"""
    global proxy_process
    
    try:
        logger.info("Starting port proxy on port 8080")
        
        # Configure environment
        env = os.environ.copy()
        env['PORT'] = '8080'
        
        # Kill any existing python processes running the proxy
        try:
            os.system("pkill -f flask_port_proxy.py")
            logger.info("Killed any existing proxy processes")
            time.sleep(1)  # Give processes time to terminate
        except Exception as e:
            logger.warning(f"Error killing existing processes: {e}")
        
        # Start proxy
        cmd = ["python", "flask_port_proxy.py"]
        
        logger.info(f"Executing: {' '.join(cmd)}")
        
        # Start process with higher priority
        proxy_process = subprocess.Popen(
            cmd,
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            # Remove preexec_fn which is causing issues on Replit
        )
        
        # Start a thread to read output from the proxy
        def read_output():
            while proxy_process and proxy_process.poll() is None:
                if proxy_process.stderr:
                    line = proxy_process.stderr.readline()
                    if line:
                        logger.info(f"Proxy: {line.decode('utf-8').strip()}")
                time.sleep(0.1)
        
        threading.Thread(target=read_output, daemon=True).start()
        
        # Log success
        logger.info("Port proxy started successfully")
        
        return True
    except Exception as e:
        logger.error(f"Failed to start port proxy: {e}")
        return False

def stop_proxy():
    """Stop the port proxy process"""
    global proxy_process
    
    if proxy_process:
        logger.info("Stopping port proxy")
        
        try:
            proxy_process.terminate()
            proxy_process.wait(timeout=5)
            logger.info("Port proxy stopped")
        except Exception as e:
            logger.error(f"Error stopping port proxy: {e}")
            
            # Force kill if needed
            try:
                proxy_process.kill()
                logger.info("Port proxy force killed")
            except:
                pass
        
        proxy_process = None

# Register cleanup function
atexit.register(stop_proxy)

# Start the proxy in a separate thread
def delayed_start():
    # Wait for the main app to start
    time.sleep(3)
    
    # Start the proxy
    start_proxy()

threading.Thread(target=delayed_start, daemon=True).start()

# Log startup
logger.info("Auto proxy module loaded and scheduled to start")