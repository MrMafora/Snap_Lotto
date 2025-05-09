import requests
import logging
import time

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')
logger = logging.getLogger('test_access')

def test_app_access(port=5000):
    """Test if the application is accessible on the specified port"""
    url = f"http://localhost:{port}/"
    
    logger.info(f"Testing access to application on port {port}...")
    try:
        response = requests.get(url, timeout=5)
        if response.status_code == 200:
            logger.info(f"SUCCESS: App is accessible on port {port}!")
            return True
        else:
            logger.error(f"FAILED: App responded with status code {response.status_code}")
            return False
    except requests.exceptions.RequestException as e:
        logger.error(f"FAILED: Couldn't connect to app on port {port}. Error: {e}")
        return False

def main():
    """Run tests for both ports"""
    # Test port 5000 first (where the app should be running)
    if test_app_access(5000):
        logger.info("Application is running correctly on port 5000")
    else:
        logger.error("Application is not accessible on port 5000!")
    
    # Small delay
    time.sleep(1)
    
    # Test port 8080 (where the proxy should be running)
    if test_app_access(8080):
        logger.info("Application is accessible through proxy on port 8080")
    else:
        logger.error("Application is not accessible through port 8080!")
        logger.info("Will try to start standalone proxy...")
        
        # Try to start the standalone proxy
        import subprocess
        import sys
        import os
        
        logger.info("Starting standalone port proxy...")
        try:
            # Run in background
            subprocess.Popen([sys.executable, "standalone_port_proxy.py"], 
                            stdout=open("proxy_output.log", "w"),
                            stderr=subprocess.STDOUT)
            logger.info("Proxy started. Waiting 5 seconds before testing again...")
            time.sleep(5)
            
            # Test again
            if test_app_access(8080):
                logger.info("SUCCESS: Application is now accessible through proxy on port 8080!")
            else:
                logger.error("FAILED: Still can't access application through port 8080")
        except Exception as e:
            logger.error(f"Error starting proxy: {e}")

if __name__ == "__main__":
    main()