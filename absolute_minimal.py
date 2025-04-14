"""
ABSOLUTE MINIMAL PORT BINDER FOR REPLIT

This is the most extreme solution possible to satisfy Replit's port detection.
It's a completely standalone script with NO imports beyond the standard library.
"""
import http.server
import socketserver
import threading
import subprocess
import time
import sys
import os

def delayed_app_start():
    """
    Start the main application with a delay to allow the minimal server to establish first.
    This ensures that Replit detects the port binding before the main app starts.
    """
    print("Waiting 3 seconds before starting main application...")
    time.sleep(3)
    
    try:
        # Use subprocess to start gunicorn without blocking
        print("Starting main application via gunicorn...")
        subprocess.Popen(
            ["gunicorn", "--bind", "0.0.0.0:5000", "--reuse-port", "--reload", "main:app"],
            stdout=sys.stdout,
            stderr=sys.stderr
        )
        print("Main application started successfully")
    except Exception as e:
        print(f"Error starting main application: {e}")

def handle_socket(socket_obj, port):
    """
    Handle an incoming socket connection and send a simple HTTP redirect response.
    """
    try:
        # Receive request data (not strictly needed for the response)
        data = socket_obj.recv(1024)
        
        # Send HTTP redirect to port 5000
        response = (
            "HTTP/1.1 302 Found\r\n"
            "Location: https://same-host:5000/\r\n"
            "Connection: close\r\n"
            "\r\n"
        )
        socket_obj.sendall(response.encode())
    except Exception as e:
        print(f"Socket error: {e}")
    finally:
        # Always close the socket
        socket_obj.close()

# Main execution starts here
if __name__ == "__main__":
    import socket
    
    # Start the main application in a separate thread with a delay
    app_thread = threading.Thread(target=delayed_app_start)
    app_thread.daemon = True
    app_thread.start()
    
    # Set up the minimal socket server on port 8080
    PORT = 8080
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    
    # Enable port reuse
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    
    try:
        # Bind to the port
        server_socket.bind(('0.0.0.0', PORT))
        server_socket.listen(5)
        print(f"Minimal server listening on port {PORT}...")
        
        # Main server loop
        while True:
            try:
                # Accept incoming connections
                client_socket, addr = server_socket.accept()
                print(f"Connection from {addr}")
                
                # Handle the connection in a separate thread
                client_thread = threading.Thread(
                    target=handle_socket,
                    args=(client_socket, PORT)
                )
                client_thread.daemon = True
                client_thread.start()
            except Exception as e:
                print(f"Error accepting connection: {e}")
    except Exception as e:
        print(f"Server error: {e}")
    finally:
        server_socket.close()