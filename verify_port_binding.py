#!/usr/bin/env python3
"""
Port binding verification script.
This script checks if the application is accessible on both port 5000 and port 8080.
"""

import sys
import time
import socket
import logging
import urllib.request
import json
from logger import setup_logger

# Set up logger
logger = setup_logger("port_checker", level=logging.INFO)

def check_port(host, port, path="/port_check", timeout=5):
    """
    Check if the application is responding on the specified port.
    
    Args:
        host (str): Host to check
        port (int): Port to check
        path (str): Path to check
        timeout (int): Connection timeout in seconds
        
    Returns:
        dict: Response data or None if connection failed
    """
    url = f"http://{host}:{port}{path}"
    logger.info(f"Checking connection to {url}")
    
    try:
        # First check if the port is open
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(timeout)
        result = sock.connect_ex((host, port))
        sock.close()
        
        if result != 0:
            logger.warning(f"Port {port} is not open")
            return None
        
        # If port is open, try to access the API endpoint
        request = urllib.request.Request(url)
        response = urllib.request.urlopen(request, timeout=timeout)
        
        if response.getcode() == 200:
            data = json.loads(response.read().decode('utf-8'))
            logger.info(f"Successfully connected to port {port}")
            return data
        else:
            logger.warning(f"Received status code {response.getcode()} from port {port}")
            return None
            
    except Exception as e:
        logger.warning(f"Error connecting to port {port}: {str(e)}")
        return None

def main():
    """Main function to check ports"""
    logger.info("Starting port binding verification")
    
    # Check localhost on port 5000
    port_5000_data = check_port("localhost", 5000)
    
    # Check localhost on port 8080
    port_8080_data = check_port("localhost", 8080)
    
    # Print results
    logger.info("=== PORT BINDING VERIFICATION RESULTS ===")
    
    if port_5000_data:
        logger.info(f"✅ Port 5000: Connection SUCCESSFUL")
        logger.info(f"  Response: {json.dumps(port_5000_data, indent=2)}")
    else:
        logger.info(f"❌ Port 5000: Connection FAILED")
    
    if port_8080_data:
        logger.info(f"✅ Port 8080: Connection SUCCESSFUL")
        logger.info(f"  Response: {json.dumps(port_8080_data, indent=2)}")
    else:
        logger.info(f"❌ Port 8080: Connection FAILED")
    
    logger.info("======================================")
    
    # Provide recommendations
    if port_5000_data and not port_8080_data:
        logger.info("RECOMMENDATION: The application is only accessible on port 5000.")
        logger.info("Try one of the following solutions:")
        logger.info("1. Run 'python final_direct_port_solution.py' to start on port 8080")
        logger.info("2. Run 'sh final_port_solution.sh' for a shell-based solution")
    elif port_8080_data and not port_5000_data:
        logger.info("SUCCESS: The application is properly configured for Replit deployment!")
        logger.info("The application is accessible on port 8080 for external access.")
    elif port_5000_data and port_8080_data:
        logger.info("SUCCESS: The application is accessible on both ports!")
        logger.info("Both internal (5000) and external (8080) access is working.")
    else:
        logger.info("WARNING: The application is not accessible on either port.")
        logger.info("Check if the application is running and try again.")

if __name__ == "__main__":
    main()