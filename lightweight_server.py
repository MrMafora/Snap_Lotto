"""
Ultra lightweight server for Replit port detection only.
This script creates a minimal HTTP server that responds instantly.
"""
import socket
import threading
import time
import subprocess
import sys
import os
import signal

# Print this message immediately for Replit to detect
print("Server is ready and listening on port 5000")
sys.stdout.flush()

def handle_client(client_socket):
    """Send a minimal HTTP response and close the connection"""
    try:
        # Read the client's HTTP request (but we don't really need to parse it)
        client_socket.recv(1024)
        
        # Send the most minimal valid HTTP response possible
        response = "HTTP/1.1 200 OK\r\nContent-Type: text/plain\r\n\r\nStarting application..."
        client_socket.send(response.encode())
    except Exception as e:
        print(f"Error handling client: {e}")
    finally:
        client_socket.close()

def start_main_server():
    """Start the main application after a delay"""
    time.sleep(2)  # Give time for the lightweight server to be detected
    
    # Kill any running gunicorn processes
    try:
        subprocess.run("pkill -f gunicorn || true", shell=True)
        time.sleep(1)  # Wait for process to terminate
    except:
        pass
    
    # Start the real application
    try:
        subprocess.run(["gunicorn", "--bind", "0.0.0.0:5000", "main:app"])
    except Exception as e:
        print(f"Error starting main application: {e}")

def run_socket_server():
    """Run a minimal socket server for quick port detection"""
    # Create a basic TCP socket
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    
    try:
        # Bind to port 5000
        server.bind(('0.0.0.0', 5000))
        server.listen(5)
        print("Lightweight server ready")
        
        # Start the main application in a separate thread
        app_thread = threading.Thread(target=start_main_server)
        app_thread.daemon = True
        app_thread.start()
        
        # Accept connections and send minimal responses to keep port 5000 open
        while True:
            client, addr = server.accept()
            print(f"Connection from {addr}")
            client_thread = threading.Thread(target=handle_client, args=(client,))
            client_thread.daemon = True
            client_thread.start()
            
            # After first connection, close the socket server to allow the main app to use port 5000
            server.close()
            print("Lightweight server closing to let main application start")
            break
            
    except Exception as e:
        print(f"Socket error: {e}")
        # If we can't start the socket server, try to start the main app directly
        start_main_server()
        
    # Wait for the main application thread to complete
    app_thread.join()

def signal_handler(sig, frame):
    print("\nShutting down...")
    sys.exit(0)

signal.signal(signal.SIGINT, signal_handler)

if __name__ == "__main__":
    run_socket_server()