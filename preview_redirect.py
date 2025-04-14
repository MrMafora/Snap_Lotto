"""
Dual-port solution for Replit preview
- Uses port 5000 for Replit detection
- Uses port 8080 for the actual application
- Redirects users from port 5000 to port 8080
"""
import socket
import threading
import time
import subprocess
import sys
import signal
import os

# Magic message for Replit
print("Server is ready and listening on port 5000")
sys.stdout.flush()

# Configuration
APP_PORT = 8080
PROXY_PORT = 5000

def signal_handler(sig, frame):
    print("\nShutting down...")
    sys.exit(0)

signal.signal(signal.SIGINT, signal_handler)

def start_app():
    """Start the actual application on a different port"""
    try:
        # Kill any existing gunicorn processes first
        subprocess.run("pkill -f gunicorn || true", shell=True)
        time.sleep(1)  # Wait for processes to terminate
        
        # Start the real application on a different port
        cmd = f"gunicorn --bind 0.0.0.0:{APP_PORT} main:app"
        subprocess.Popen(cmd, shell=True)
        
        print(f"Started main application on port {APP_PORT}")
    except Exception as e:
        print(f"Error starting application: {e}")

def handle_client(client_socket):
    """Send a redirect response to the client"""
    try:
        # Read the client's HTTP request (but we don't really need to parse it)
        client_socket.recv(1024)
        
        # Determine the host for redirection
        host = os.environ.get('REPL_SLUG', 'localhost')
        if '.replit.dev' in host:
            redirect_url = f"https://{host}.replit.dev"
        else:
            redirect_url = f"http://localhost:{APP_PORT}"
        
        # Send redirect response
        response = f"""HTTP/1.1 302 Found
Location: {redirect_url}
Content-Type: text/html
Connection: close

<html>
<head>
    <title>Redirecting...</title>
    <meta http-equiv="refresh" content="0;url={redirect_url}">
</head>
<body>
    <h1>Redirecting to main application...</h1>
    <p>Click <a href="{redirect_url}">here</a> if you are not redirected automatically.</p>
</body>
</html>
"""
        client_socket.send(response.encode())
    except Exception as e:
        print(f"Error handling client: {e}")
    finally:
        client_socket.close()

def run_socket_server():
    """Run a minimal socket server for Replit port detection"""
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    
    try:
        server.bind(('0.0.0.0', PROXY_PORT))
        server.listen(5)
        print(f"Proxy server listening on port {PROXY_PORT}")
        
        while True:
            client, addr = server.accept()
            print(f"Accepted connection from {addr}")
            client_thread = threading.Thread(target=handle_client, args=(client,))
            client_thread.daemon = True
            client_thread.start()
    except Exception as e:
        print(f"Server error: {e}")
    finally:
        server.close()

if __name__ == "__main__":
    # Start the real application in a separate thread
    app_thread = threading.Thread(target=start_app)
    app_thread.daemon = True
    app_thread.start()
    
    # Give the app time to start
    time.sleep(2)
    
    # Run the socket server in the main thread
    run_socket_server()