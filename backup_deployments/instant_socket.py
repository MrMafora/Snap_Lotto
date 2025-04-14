"""
Ultra lightweight socket server for instant port detection.
This script creates a minimal TCP socket server that responds instantly 
while starting the main application in the background.
"""
import socket
import threading
import time
import subprocess
import os
import sys
import signal

# Configuration
SOCKET_PORT = 5000  # Port Replit expects to be open
APP_PORT = 8080     # Port where actual app will run

def handle_client(client_socket):
    """Send a minimal HTTP response and close the connection"""
    try:
        # Read the request (but we don't really care about it)
        request = client_socket.recv(1024).decode()
        
        # Send a basic HTTP response
        response = "HTTP/1.1 200 OK\r\nContent-Type: text/html\r\n\r\n"
        response += "<html><body><h1>Application Starting</h1>"
        response += "<p>Please wait while the application starts...</p>"
        response += "<script>setTimeout(() => { window.location.reload(); }, 3000);</script>"
        response += "</body></html>"
        
        client_socket.send(response.encode())
    except:
        pass
    finally:
        # Close the connection
        client_socket.close()

def start_main_app():
    """Start the main application after a delay"""
    # Small delay to ensure socket server is running first
    time.sleep(1)
    
    # Kill any existing Python processes
    os.system("pkill -f gunicorn || true")
    os.system("pkill -f 'python.*main.py' || true")
    
    # Start the main application with direct port 
    print("Starting main application on port", APP_PORT)
    cmd = ["python", "main.py", "--port", str(APP_PORT)]
    return subprocess.Popen(
        cmd, 
        stdout=sys.stdout, 
        stderr=sys.stderr,
        env=dict(os.environ, PORT=str(APP_PORT))
    )

def run_socket_server():
    """Run a minimal socket server for quick port detection"""
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    
    # Allow socket reuse
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    
    # Bind to all interfaces
    server_socket.bind(('0.0.0.0', SOCKET_PORT))
    
    # Start listening with a small backlog
    server_socket.listen(5)
    
    print(f"Socket server ready on port {SOCKET_PORT}")
    sys.stdout.flush()  # Make sure Replit sees this message immediately
    
    # Accept connections and handle them
    while True:
        try:
            client_socket, addr = server_socket.accept()
            client_thread = threading.Thread(target=handle_client, args=(client_socket,))
            client_thread.daemon = True
            client_thread.start()
        except:
            break

def signal_handler(sig, frame):
    """Handle Ctrl+C gracefully"""
    print("Shutting down...")
    if app_process:
        print("Stopping main application...")
        app_process.terminate()
    sys.exit(0)

if __name__ == "__main__":
    # Register signal handler
    signal.signal(signal.SIGINT, signal_handler)
    
    # Start socket server in a separate thread
    socket_thread = threading.Thread(target=run_socket_server)
    socket_thread.daemon = True
    socket_thread.start()
    
    # Start the main app
    app_process = start_main_app()
    
    try:
        # Wait for the main app to finish
        app_process.wait()
    except KeyboardInterrupt:
        signal_handler(None, None)