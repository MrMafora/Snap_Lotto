"""
Direct Flask server starter with immediate port opening.

This script:
1. Opens port 5000 immediately to satisfy Replit's detection requirement
2. Shows a "loading" page while the main application starts
3. Initializes the Flask application in the background
4. Forwards requests to the Flask app once it's ready

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
import flask

# Configuration
PORT = 5000  # Port Replit expects to be open
APP_TIMEOUT = 30  # How long to wait for the app to start (seconds)

# Global variables
app_ready = False
app_queue = queue.Queue()  # Queue for sending requests to the main app
flask_app = None  # Will hold the actual Flask app instance

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
        """Forward the request to the Flask app"""
        try:
            # Import the main app module
            from main import app
            
            # Create a test client for the Flask app
            client = app.test_client()
            
            # Read request body if present
            content_length = int(self.headers.get('Content-Length', 0))
            body = self.rfile.read(content_length) if content_length > 0 else None
            
            # Forward the request to the Flask app
            environ = {
                'PATH_INFO': self.path,
                'REQUEST_METHOD': self.command,
                'wsgi.input': body if body else b'',
                'CONTENT_LENGTH': str(content_length),
                'CONTENT_TYPE': self.headers.get('Content-Type', ''),
            }
            
            # Add any other headers needed
            for key, value in self.headers.items():
                environ[f'HTTP_{key.upper().replace("-", "_")}'] = value
            
            # Make the request to the Flask app
            if self.command == 'GET':
                response = client.get(self.path, headers=dict(self.headers))
            elif self.command == 'POST':
                response = client.post(self.path, data=body, headers=dict(self.headers))
            else:
                # Default fallback
                response = client.open(self.path, method=self.command, data=body, headers=dict(self.headers))
            
            # Send the response status
            self.send_response(response.status_code)
            
            # Send response headers
            for header, value in response.headers:
                self.send_header(header, value)
            self.end_headers()
            
            # Send the response body
            self.wfile.write(response.data)
            
        except Exception as e:
            self.send_response(500)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            error_msg = f"<h1>Error</h1><p>Could not process request: {str(e)}</p>"
            self.wfile.write(error_msg.encode())

def start_proxy_server():
    """Start the proxy server on port 5000"""
    # Create server with address reuse
    socketserver.TCPServer.allow_reuse_address = True
    with socketserver.TCPServer(("0.0.0.0", PORT), ProxyHandler) as httpd:
        print(f"PORT {PORT} OPEN - Serving HTTP on 0.0.0.0:{PORT}")
        sys.stdout.flush()
        
        # Serve requests until the app is ready and a bit longer
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            pass
        finally:
            httpd.server_close()

def load_flask_app():
    """Load the main Flask application"""
    global app_ready
    
    print("Loading the Flask application...")
    sys.stdout.flush()
    
    try:
        # Give some time for proxy server to start
        time.sleep(0.5)
        
        # Import the app 
        import main
        
        # Mark the application as ready
        app_ready = True
        print("Flask application loaded successfully!")
        sys.stdout.flush()
    except Exception as e:
        print(f"Error loading Flask app: {e}")
        sys.stdout.flush()
        # Don't set app_ready, so we keep showing the loading page
    
    # Keep the thread running
    while True:
        time.sleep(1)

if __name__ == "__main__":
    # Clear any existing processes
    os.system("pkill -f gunicorn || true")
    
    # First start the app loading in a background thread
    app_thread = threading.Thread(target=load_flask_app)
    app_thread.daemon = True
    app_thread.start()
    
    # Then start the proxy server in the main thread
    start_proxy_server()