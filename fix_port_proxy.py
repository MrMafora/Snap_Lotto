"""
Direct port proxy fixer that ensures the Flask app is accessible
via port 8080 and fixes any connection issues.
"""
import os
import subprocess
import sys
import time
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('fix_port_proxy')

def kill_existing_proxies():
    """Kill any existing port proxy processes"""
    logger.info("Killing any existing proxy processes")
    try:
        # Find and kill any existing Python processes containing 'port_proxy'
        os.system("pkill -f 'port_proxy'")
        time.sleep(1)  # Give processes time to shut down
    except Exception as e:
        logger.error(f"Error killing proxy processes: {e}")

def start_proxy():
    """Start a new port proxy"""
    logger.info("Starting new port proxy")
    try:
        # Start the port proxy in a new process
        proxy_process = subprocess.Popen(
            ["python", "flask_port_proxy.py"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        
        # Wait a moment for it to start
        time.sleep(2)
        
        if proxy_process.poll() is not None:
            # Process has already exited
            stdout, stderr = proxy_process.communicate()
            logger.error(f"Proxy process failed to start. Stdout: {stdout.decode()}, Stderr: {stderr.decode()}")
            return False
        
        logger.info("Port proxy started successfully")
        return True
    except Exception as e:
        logger.error(f"Error starting port proxy: {e}")
        return False

def main():
    """Main function to fix port proxy"""
    # Kill any existing proxies
    kill_existing_proxies()
    
    # Start a new proxy
    if start_proxy():
        logger.info("Port proxy fixed successfully")
        return 0
    else:
        logger.error("Failed to fix port proxy")
        return 1

if __name__ == "__main__":
    sys.exit(main())