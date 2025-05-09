#!/usr/bin/env python3
"""
Auto-start proxy script that checks if port 8080 is accessible
and starts the proxy if needed.
"""
import socket
import subprocess
import time
import logging
import sys
import os

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler("auto_proxy.log")
    ]
)
logger = logging.getLogger("auto_proxy")

def is_port_in_use(port):
    """Check if the port is in use"""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex(('localhost', port)) == 0

def is_process_running(process_name):
    """Check if a process with the given name is running"""
    try:
        # This works on both Unix and Windows
        output = subprocess.check_output(['ps', 'aux'], text=True)
        return process_name in output
    except:
        return False

def start_proxy():
    """Start the simple proxy server"""
    logger.info("Starting proxy server...")
    try:
        subprocess.Popen(['python', 'simple_proxy.py'], 
                          stdout=open('proxy_output.log', 'a'),
                          stderr=subprocess.STDOUT)
        logger.info("Proxy server started in background")
        return True
    except Exception as e:
        logger.error(f"Failed to start proxy: {e}")
        return False

def check_and_start_proxy():
    """Check if proxy is needed and start it if not running"""
    # If port 8080 is not in use and the proxy is not running, start it
    if not is_port_in_use(8080) and not is_process_running('simple_proxy.py'):
        logger.info("Port 8080 is not accessible, starting proxy...")
        return start_proxy()
    elif is_port_in_use(8080):
        logger.info("Port 8080 is already in use, no action needed")
        return True
    else:
        logger.info("simple_proxy.py appears to be running but port 8080 is not accessible")
        return False

def main():
    """Main function to run auto proxy starter"""
    # Wait for port 5000 to become available
    retries = 30
    while retries > 0:
        if is_port_in_use(5000):
            break
        logger.info("Waiting for port 5000 to become available...")
        time.sleep(1)
        retries -= 1
    
    if retries <= 0:
        logger.error("Timed out waiting for port 5000")
        return False
    
    # Start the proxy if needed
    if check_and_start_proxy():
        logger.info("Auto-proxy startup completed successfully")
        return True
    else:
        logger.error("Failed to ensure proxy is running")
        return False

if __name__ == "__main__":
    main()