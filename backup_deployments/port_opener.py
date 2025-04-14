"""
Minimal port opener for Replit detection
"""
import socket
import time
import threading
import subprocess
import signal
import sys
import os

def signal_handler(sig, frame):
    """Handle Ctrl+C gracefully"""
    print("Shutting down port opener...")
    sys.exit(0)

def open_port_5000():
    """Open port 5000 immediately for Replit detection"""
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    
    try:
        server_socket.bind(('0.0.0.0', 5000))
        server_socket.listen(5)
        print("Port 5000 opened for Replit detection")
        
        while True:
            client_socket, _ = server_socket.accept()
            response = b"HTTP/1.1 200 OK\r\nContent-Type: text/html\r\n\r\n"
            response += b"<html><body><h1>Application starting...</h1><p>Please wait while the application starts on port 8080.</p></body></html>"
            client_socket.sendall(response)
            client_socket.close()
            
    except (OSError, KeyboardInterrupt):
        print("Port 5000 already in use or interrupted")
    finally:
        server_socket.close()

def start_real_app():
    """Start the real application after a delay"""
    # Small delay to ensure port opener is running first
    time.sleep(2)
    print("Starting the main application on port 8080...")
    subprocess.run(["./start.sh"], check=True)

if __name__ == "__main__":
    # Set up signal handler
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Start port opener in a separate thread
    port_opener_thread = threading.Thread(target=open_port_5000)
    port_opener_thread.daemon = True
    port_opener_thread.start()
    
    # Start the real application in the main thread
    start_real_app()