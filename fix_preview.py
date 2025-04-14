"""
Custom proxy server to enable Replit preview functionality
"""
import socket
import threading
import time
import subprocess
import os
import sys
import signal
from http.server import BaseHTTPRequestHandler, HTTPServer

# Configuration
PROXY_PORT = 5000  # Port Replit expects to be open
APP_PORT = 8080    # Port where actual app will run

def start_main_app():
    """Start the actual Flask app on a different port"""
    os.environ["FLASK_APP"] = "main.py"
    
    # Kill any existing Python processes
    os.system("pkill -f gunicorn || true")
    os.system("pkill -f 'python.*main.py' || true")
    
    # Start the main application
    # Use direct Python command as recommended by Replit support
    print("Starting main application on port", APP_PORT)
    cmd = ["python3", "main.py", "--port", str(APP_PORT)]
    return subprocess.Popen(
        cmd, 
        stdout=sys.stdout, 
        stderr=sys.stderr,
        env=dict(os.environ, PORT=str(APP_PORT))
    )

class ProxyHandler(BaseHTTPRequestHandler):
    """Custom HTTP handler that proxies requests to the real application"""
    
    def log_message(self, format, *args):
        """Silence the default logging"""
        return
    
    def do_GET(self):
        """Handle all GET requests with a proxy to the real app"""
        try:
            # Create a socket to the real application
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.connect(('localhost', APP_PORT))
            
            # Construct request
            request = f"GET {self.path} HTTP/1.1\r\n"
            for header in self.headers:
                request += f"{header}: {self.headers[header]}\r\n"
            request += "\r\n"
            
            # Send request
            sock.sendall(request.encode())
            
            # Get response
            response = b""
            while True:
                data = sock.recv(4096)
                if not data:
                    break
                response += data
                
            # Send back to client
            self.wfile.write(response)
            sock.close()
        except Exception as e:
            # Connection failed, app might not be ready
            self.send_response(307)
            self.send_header('Location', f'http://localhost:{APP_PORT}{self.path}')
            self.end_headers()
            self.wfile.write(f"Redirecting to main application... Please wait. Error: {e}".encode())
    
    def do_POST(self):
        """Handle POST requests with a proxy to the real app"""
        try:
            # Get content length
            content_length = int(self.headers.get('Content-Length', 0))
            post_data = self.rfile.read(content_length)
            
            # Create a socket to the real application
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.connect(('localhost', APP_PORT))
            
            # Construct request
            request = f"POST {self.path} HTTP/1.1\r\n"
            for header in self.headers:
                request += f"{header}: {self.headers[header]}\r\n"
            request += "\r\n"
            
            # Send request and post data
            sock.sendall(request.encode() + post_data)
            
            # Get response
            response = b""
            while True:
                data = sock.recv(4096)
                if not data:
                    break
                response += data
                
            # Send back to client
            self.wfile.write(response)
            sock.close()
        except Exception as e:
            # Connection failed, app might not be ready
            self.send_response(307)
            self.send_header('Location', f'http://localhost:{APP_PORT}{self.path}')
            self.end_headers()
            self.wfile.write(f"Redirecting to main application... Please wait. Error: {e}".encode())

def signal_handler(sig, frame):
    """Handle Ctrl+C gracefully"""
    print("Shutting down...")
    if app_process:
        print("Stopping main application...")
        app_process.terminate()
    sys.exit(0)

def run_proxy_server():
    """Run the proxy server on port 5000"""
    server = HTTPServer(('0.0.0.0', PROXY_PORT), ProxyHandler)
    print(f"Proxy server ready on port {PROXY_PORT}")
    sys.stdout.flush()  # Make sure Replit sees this message immediately
    server.serve_forever()

if __name__ == "__main__":
    # Register signal handler
    signal.signal(signal.SIGINT, signal_handler)
    
    # Start the main app in a separate process
    app_process = start_main_app()
    
    # Start the proxy server
    proxy_thread = threading.Thread(target=run_proxy_server)
    proxy_thread.daemon = True
    proxy_thread.start()
    
    try:
        # Wait for the main app to finish
        app_process.wait()
    except KeyboardInterrupt:
        signal_handler(None, None)