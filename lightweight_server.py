"""
Ultra lightweight server for Replit port detection only.
This script creates a minimal HTTP server that responds instantly.
"""
import socket
import threading
import time
import subprocess
import signal
import sys
import os

# Print this exact line to help Replit port detection
print("Server is ready and listening on port 5000")

def handle_client(client_socket):
    """Send a minimal HTTP response and close the connection"""
    response = "HTTP/1.1 200 OK\r\nContent-Length: 20\r\n\r\nLottery App Starting"
    client_socket.send(response.encode())
    client_socket.close()

def start_main_server():
    """Start the main application after a delay"""
    time.sleep(3)
    print("Starting main application...")
    
    # Kill any existing gunicorn processes
    try:
        subprocess.run("pkill -f gunicorn || true", shell=True)
        time.sleep(1)
    except:
        pass
    
    # Start the main application on port 8080 to avoid conflicts
    try:
        subprocess.Popen(["gunicorn", "--bind", "0.0.0.0:8080", "main:app"])
        print("Main application started on port 8080")
        
        # Create a redirect page on port 5000
        with open('redirect.html', 'w') as f:
            f.write("""<!DOCTYPE html>
<html>
<head>
    <title>Redirecting to Lottery App</title>
    <meta http-equiv="refresh" content="0;url=http://localhost:8080/">
</head>
<body>
    <p>Redirecting to the lottery application...</p>
</body>
</html>""")
        
        # Wait for the main app to start
        time.sleep(2)
        
        # Start a simple HTTP server to serve the redirect page
        subprocess.Popen(["python", "-m", "http.server", "5000", "--bind", "0.0.0.0"])
        print("Redirect server started on port 5000")
        
    except Exception as e:
        print(f"Error starting application: {e}")

def run_socket_server():
    """Run a minimal socket server for quick port detection"""
    # Create socket
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    
    try:
        # Bind to port 5000
        server.bind(('0.0.0.0', 5000))
        server.listen(5)
        
        # Start a thread to launch the main application
        app_thread = threading.Thread(target=start_main_server)
        app_thread.daemon = True
        app_thread.start()
        
        # Accept only one connection then exit
        client, addr = server.accept()
        print(f"Connection from {addr}")
        handle_client(client)
        
    except Exception as e:
        print(f"Socket error: {e}")
    finally:
        server.close()

# Handle Ctrl+C gracefully
def signal_handler(sig, frame):
    print("Shutting down...")
    sys.exit(0)

signal.signal(signal.SIGINT, signal_handler)

if __name__ == "__main__":
    run_socket_server()