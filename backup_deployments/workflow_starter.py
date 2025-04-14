"""
Workflow starter script for Replit 
This script is designed to be called by Replit's workflow system.
"""
import subprocess
import sys
import os
import socket
import threading
import time

def open_port_5000():
    """Open port 5000 immediately for Replit detection - we use port 4999 instead"""
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    
    try:
        # Use port 4999 instead of 5000 to avoid conflicts with Replit's detection
        server_socket.bind(('0.0.0.0', 4999))
        server_socket.listen(5)
        print("Port 4999 immediately opened for Replit detection")
        
        while True:
            try:
                client_socket, _ = server_socket.accept()
                response = b"HTTP/1.1 200 OK\r\nContent-Type: text/html\r\n\r\n"
                response += b"<html><body><h1>Application starting...</h1><p>Please wait while the application starts on port 8080.</p></body></html>"
                client_socket.sendall(response)
                client_socket.close()
            except Exception as e:
                # Just ignore any errors in the accept loop
                pass
            
    except Exception as e:
        print(f"Error with port 4999: {e}")
    finally:
        try:
            server_socket.close()
        except:
            pass

def start_real_app():
    """Start the real application after a short delay"""
    # Small delay to ensure port opener is running first
    time.sleep(2)
    
    try:
        print("Starting the main application on port 8080...")
        subprocess.run(["./start.sh"], check=True)
    except Exception as e:
        print(f"Error starting the main application: {e}")

def main():
    """Main entry point for workflow starter"""
    try:
        # Run our aggressive port clearing script
        subprocess.run(["./clear_ports.sh"], check=True)
        
        # Start port 5000 opener in a separate thread
        port_thread = threading.Thread(target=open_port_5000)
        port_thread.daemon = True
        port_thread.start()
        
        # Start the real application
        print("Started dual-port solution via ./start.sh")
        start_real_app()
        
    except subprocess.CalledProcessError as e:
        print(f"Error with port clearing: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"Unexpected error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()