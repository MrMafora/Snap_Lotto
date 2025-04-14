"""
Ultra-minimal port binding script for Replit workflow detection.
Binds to port 5000 immediately, then hands off to gunicorn.

No Flask dependencies, no database connections.
Just raw socket binding for fastest possible startup.
"""
import socket
import subprocess
import sys
import os
import signal
import time
import logging

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def main():
    """Main entry point"""
    # Create socket
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

    try:
        # Bind immediately to port 5000
        logger.info("Binding to port 5000")
        s.bind(('0.0.0.0', 5000))
        s.listen(1)
        s.settimeout(0.5)  # Short timeout for accept()
        
        logger.info("Successfully bound to port 5000")
        
        # Start accepting connections in a loop to keep port active
        start_time = time.time()
        
        # Wait for incoming connections
        try:
            while time.time() - start_time < 30:  # Wait for 30 seconds
                try:
                    conn, addr = s.accept()
                    logger.info(f"Connection from {addr}")
                    
                    # Send minimal HTTP response
                    conn.sendall(b"HTTP/1.1 200 OK\r\nContent-Type: text/plain\r\n\r\nStarting lottery application, please wait...")
                    conn.close()
                except socket.timeout:
                    # Expected timeout, just continue
                    pass
        except KeyboardInterrupt:
            logger.info("Interrupted by user")
            
        logger.info("Socket binding period complete")
            
        # Close socket (will release port for gunicorn)
        s.close()
        logger.info("Socket closed")
        
        # Execute gunicorn as a new process
        logger.info("Starting gunicorn")
        cmd = ["gunicorn", "--bind", "0.0.0.0:5000", "--reload", "main:app"]
        subprocess.Popen(cmd)
        
        # Exit this script
        logger.info("Exiting quick_bind.py")
        return 0
        
    except Exception as e:
        logger.error(f"Error: {str(e)}")
        return 1

if __name__ == "__main__":
    sys.exit(main())