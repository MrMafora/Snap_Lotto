"""
Dual-port configuration for Replit with immediate port opening.

This script implements a special dual-port configuration:
1. Opens port 5000 immediately (configured with externalPort = 80 in .replit)
   - This is essential for meeting Replit's 20-second detection window
   - Shows a "loading" page while the main application starts
2. Runs the actual Flask app on port 8080 internally
   - This isolates the actual application server
3. Proxies requests between the ports
   - All external traffic comes in via port 80 -> port 5000 internally
   - Then forwarded to the application running on port 8080

Usage: python start_direct.py
"""
import socket
import threading
import time
import os
import sys
import http.server
import socketserver
from http.server import BaseHTTPRequestHandler
import signal
import subprocess
import importlib
import queue
# No longer need direct flask import since we use gunicorn

# Configuration
EXTERNAL_PORT = 4999  # Just below port 5000 to avoid conflicts with workflow
INTERNAL_PORT = 8080  # Port where the actual Flask app will run
APP_TIMEOUT = 30  # How long to wait for the app to start (seconds)

# Global variables
app_ready = False
app_queue = queue.Queue()  # Queue for request handling if needed

def signal_handler(sig, frame):
    """Handle Ctrl+C gracefully"""
    print("Shutting down...")
    sys.exit(0)

# Register signal handler
signal.signal(signal.SIGINT, signal_handler)

class ProxyHandler(BaseHTTPRequestHandler):
    """HTTP handler that either shows a loading page or forwards to the app"""
    def log_message(self, format, *args):
        """Silence logging for better performance"""
        return
    
    def do_GET(self):
        """Handle GET requests"""
        global app_ready
        
        if not app_ready:
            # App still starting, show loading page
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            self.wfile.write(b"""
            <html>
            <head>
                <title>Lottery App Starting</title>
                <style>
                    body { font-family: Arial, sans-serif; background-color: #f5f5f5; text-align: center; padding-top: 100px; }
                    .loader { border: 8px solid #f3f3f3; border-top: 8px solid #3498db; border-radius: 50%; width: 50px; height: 50px; animation: spin 1s linear infinite; margin: 0 auto; }
                    @keyframes spin { 0% { transform: rotate(0deg); } 100% { transform: rotate(360deg); } }
                    h1 { color: #333; }
                </style>
                <meta http-equiv="refresh" content="2">
            </head>
            <body>
                <h1>Application is starting...</h1>
                <p>This may take up to 30 seconds. Thank you for your patience.</p>
                <div class="loader"></div>
            </body>
            </html>
            """)
        else:
            # App is ready, handle the request using the Flask app
            self.handle_app_request()
    
    def do_POST(self):
        """Handle POST requests"""
        global app_ready
        
        if not app_ready:
            # App not ready yet
            self.send_response(503)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            self.wfile.write(b"<h1>Application is starting...</h1><p>Please try again shortly.</p>")
        else:
            # App is ready, handle the request using the Flask app
            self.handle_app_request()
    
    def handle_app_request(self):
        """Forward the request to the gunicorn app running on the internal port"""
        try:
            import urllib.request
            import urllib.error
            import urllib.parse
            from io import BytesIO
            import http.client
            
            # Read request body if present
            content_length = int(self.headers.get('Content-Length', 0))
            body = self.rfile.read(content_length) if content_length > 0 else None
            
            # Create the request to the internal port
            url = f"http://localhost:{INTERNAL_PORT}{self.path}"
            
            # Build the request object
            if body and self.command == 'POST':
                req = urllib.request.Request(url, data=body, method=self.command)
            else:
                req = urllib.request.Request(url, method=self.command)
            
            # Copy all headers except host
            for header, value in self.headers.items():
                if header.lower() != 'host':
                    req.add_header(header, value)
            
            # Set correct host header for internal request
            req.add_header('Host', f'localhost:{INTERNAL_PORT}')
            
            try:
                # Make the request to the internal app
                response = urllib.request.urlopen(req, timeout=10)
                
                # Send the response status code
                self.send_response(response.status)
                
                # Send the response headers
                for header in response.getheaders():
                    self.send_header(header[0], header[1])
                self.end_headers()
                
                # Send the response body
                self.wfile.write(response.read())
                
            except urllib.error.HTTPError as e:
                # Handle HTTP errors from the internal server
                self.send_response(e.code)
                
                # Copy error headers
                for header in e.headers.items():
                    self.send_header(header[0], header[1])
                self.end_headers()
                
                # Forward error content
                self.wfile.write(e.read())
                
            except urllib.error.URLError as e:
                # Internal server not responding
                self.send_response(503)
                self.send_header('Content-type', 'text/html')
                self.end_headers()
                error_msg = f"<h1>Service Unavailable</h1><p>The application server is not responding: {str(e)}</p>"
                self.wfile.write(error_msg.encode())
            
        except Exception as e:
            # Unhandled error
            self.send_response(500)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            error_msg = f"<h1>Proxy Error</h1><p>Could not process request: {str(e)}</p>"
            self.wfile.write(error_msg.encode())

def start_proxy_server():
    """Start the proxy server on the external port (4999)"""
    # Create server with address reuse
    socketserver.TCPServer.allow_reuse_address = True
    
    # Try a few times to bind to the port
    max_attempts = 3
    for attempt in range(max_attempts):
        try:
            with socketserver.TCPServer(("0.0.0.0", EXTERNAL_PORT), ProxyHandler) as httpd:
                print(f"PORT {EXTERNAL_PORT} OPEN - Serving HTTP on 0.0.0.0:{EXTERNAL_PORT}")
                print(f"This port will be exposed externally as port 80 (HTTP)")
                sys.stdout.flush()
                
                # Serve requests until the app is ready and a bit longer
                try:
                    httpd.serve_forever()
                except KeyboardInterrupt:
                    pass
                finally:
                    httpd.server_close()
                    
        except OSError as e:
            if "Address already in use" in str(e):
                print(f"Port {EXTERNAL_PORT} already in use (probably by gunicorn): {e}")
                
                # Try to kill any processes using this port
                if attempt < max_attempts - 1:
                    print(f"Attempting to kill processes using port {EXTERNAL_PORT}...")
                    try:
                        # Try different methods to kill the process
                        os.system(f"pkill -9 -f 'gunicorn --bind 0.0.0.0:{EXTERNAL_PORT}'")
                        os.system(f"pkill -9 -f ':{EXTERNAL_PORT}'")
                        # Wait a moment
                        time.sleep(2)
                    except Exception as kill_err:
                        print(f"Error killing processes: {kill_err}")
                else:
                    # Last attempt, try opening a different port
                    print(f"Failed to bind to port {EXTERNAL_PORT} after multiple attempts")
                    # Use an alternative method to open a socket for detection
                    try:
                        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                        sock.bind(('0.0.0.0', EXTERNAL_PORT))
                        sock.listen(5)
                        print(f"Manual socket opened on port {EXTERNAL_PORT}")
                        print(f"This will be forwarded to gunicorn on port {INTERNAL_PORT}")
                        print(f"Server is ready and listening on port {EXTERNAL_PORT}")
                        sys.stdout.flush()
                        
                        # Keep the socket open and handle connections manually
                        while True:
                            client, addr = sock.accept()
                            client.send(b'HTTP/1.1 302 Found\r\nLocation: http://0.0.0.0:8080\r\n\r\n')
                            client.close()
                    except Exception as sock_err:
                        print(f"Failed to open manual socket: {sock_err}")
                        sys.exit(1)
            else:
                # Some other socket error
                print(f"Socket error: {e}")
                sys.exit(1)

def load_flask_app():
    """Load the main Flask application on the internal port"""
    global app_ready
    
    print(f"Loading the Flask application on internal port {INTERNAL_PORT}...")
    sys.stdout.flush()
    
    try:
        # Give some time for proxy server to start
        time.sleep(0.5)
        
        # Instead of importing directly, start gunicorn on the internal port
        cmd = f"gunicorn --bind 0.0.0.0:{INTERNAL_PORT} main:app"
        subprocess.Popen(cmd, shell=True)
        
        # Wait a bit for gunicorn to start
        time.sleep(3)
        
        # Try to connect to the internal port to verify it's running
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.connect(('localhost', INTERNAL_PORT))
            s.close()
            app_ready = True
            print(f"Flask application loaded successfully on port {INTERNAL_PORT}!")
        except:
            print(f"Warning: Could not connect to app on port {INTERNAL_PORT}, but continuing...")
            # Still mark as ready so we can try to proxy requests
            app_ready = True
        
        sys.stdout.flush()
    except Exception as e:
        print(f"Error loading Flask app: {e}")
        sys.stdout.flush()
        # Don't set app_ready, so we keep showing the loading page
    
    # Keep the thread running
    while True:
        time.sleep(1)

if __name__ == "__main__":
    # Print startup banner
    print("\n" + "="*80)
    print(f"Starting Lottery App with dual-port configuration:")
    print(f"  - External port: {EXTERNAL_PORT} (mapped to port 80 externally)")
    print(f"  - Internal app port: {INTERNAL_PORT}")
    print("="*80 + "\n")
    sys.stdout.flush()
    
    # Aggressive cleanup of existing processes first
    print("Performing pre-startup process cleanup...")
    cleanup_commands = [
        f"pkill -9 -f 'gunicorn --bind 0.0.0.0:{EXTERNAL_PORT}'",
        f"pkill -9 -f 'gunicorn --bind 0.0.0.0:{INTERNAL_PORT}'",
        "pkill -9 -f 'python start_direct.py'",
        "pkill -9 -f gunicorn"
    ]
    
    for cmd in cleanup_commands:
        try:
            os.system(cmd + " 2>/dev/null || true")
        except:
            pass
    
    # Sleep briefly to allow processes to terminate
    time.sleep(1)
    print("Process cleanup completed")
    sys.stdout.flush()
    
    try:
        # First start the app loading in a background thread
        print("Starting Flask application thread...")
        app_thread = threading.Thread(target=load_flask_app)
        app_thread.daemon = True
        app_thread.start()
        
        # Then start the proxy server in the main thread
        print("Starting proxy server on external port...")
        start_proxy_server()
    except Exception as e:
        print(f"Critical error during startup: {e}")
        sys.exit(1)