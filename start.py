"""
Fast startup script for lottery application.

This script:
1. Binds to port 5000 immediately (for Replit detection)
2. Starts gunicorn as a background process

Usage: python start.py
"""
import socket
import subprocess
import os
import time
import sys
import threading
import signal
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def bind_socket():
    """Bind to port 5000 immediately to satisfy Replit's detection."""
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    
    try:
        # Bind to port 5000 immediately
        server_socket.bind(('0.0.0.0', 5000))
        server_socket.listen(5)
        logger.info("Socket bound successfully to port 5000")
        return server_socket
    except Exception as e:
        logger.error(f"Error binding socket: {str(e)}")
        raise

def start_gunicorn():
    """Start gunicorn as a background process."""
    try:
        # Command to start gunicorn
        cmd = ["gunicorn", "--bind", "0.0.0.0:5000", "--reuse-port", "--reload", "main:app"]
        
        # Start the process
        logger.info(f"Starting gunicorn with command: {' '.join(cmd)}")
        process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        
        return process
    except Exception as e:
        logger.error(f"Error starting gunicorn: {str(e)}")
        raise

def handle_signals(server_socket, gunicorn_process):
    """Handle signals to properly shut down."""
    def signal_handler(sig, frame):
        logger.info(f"Received signal {sig}, shutting down...")
        
        # Close the socket
        try:
            server_socket.close()
            logger.info("Socket closed")
        except Exception as e:
            logger.error(f"Error closing socket: {str(e)}")
        
        # Terminate gunicorn
        try:
            gunicorn_process.terminate()
            logger.info("Gunicorn terminated")
        except Exception as e:
            logger.error(f"Error terminating gunicorn: {str(e)}")
        
        sys.exit(0)
    
    # Register signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

def answer_dummy_requests():
    """
    Keep answering requests on port 5000 with a simple response.
    This keeps the socket open for Replit detection.
    """
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    
    try:
        # Bind to port 5000
        server_socket.bind(('0.0.0.0', 5000))
        server_socket.listen(5)
        logger.info("Dummy server started on port 5000")
        
        # Keep accepting connections for 30 seconds (Replit needs 20s)
        server_socket.settimeout(1.0)  # 1 second timeout for accept()
        start_time = time.time()
        
        while time.time() - start_time < 30:
            try:
                # Accept a connection
                client_socket, addr = server_socket.accept()
                logger.info(f"Accepted connection from {addr}")
                
                # Send a simple HTTP response
                response = "HTTP/1.1 200 OK\r\nContent-Type: text/plain\r\n\r\nStarting lottery application, please wait..."
                client_socket.sendall(response.encode('utf-8'))
                client_socket.close()
            except socket.timeout:
                # Just keep trying
                pass
            except Exception as e:
                logger.error(f"Error handling connection: {str(e)}")
    finally:
        # Close the socket when done
        server_socket.close()
        logger.info("Dummy server stopped")
        
def main():
    """Main function."""
    try:
        # Step 1: Start dummy server in a separate thread for Replit detection
        dummy_thread = threading.Thread(target=answer_dummy_requests)
        dummy_thread.daemon = True
        dummy_thread.start()
        logger.info("Started dummy server thread")
        
        # Give the dummy server a moment to start
        time.sleep(1)
        
        # Step 2: Start gunicorn in parallel
        gunicorn_process = start_gunicorn()
        logger.info("Started gunicorn process")
        
        # Step 3: Wait for gunicorn to exit
        while True:
            return_code = gunicorn_process.poll()
            if return_code is not None:
                logger.info(f"Gunicorn exited with code {return_code}")
                break
            time.sleep(1)
            
    except Exception as e:
        logger.error(f"Error in main function: {str(e)}")
        return 1
        
    return 0

if __name__ == "__main__":
    sys.exit(main())