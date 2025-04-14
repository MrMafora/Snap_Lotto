"""
STANDALONE PORT 8080 SERVER

This is a completely standalone, dependency-free HTTP server 
that runs on port 8080 and forwards all requests to port 5000.

This script is designed to be run in a separate process alongside
the main application. It allows the application to be accessed
via port 8080 without modifying gunicorn's configuration.
"""
import http.server
import socketserver
import threading
import time
import sys
import os
import signal

PORT = 8080
TARGET_PORT = 5000

class ProxyHandler(http.server.BaseHTTPRequestHandler):
    """Simple HTTP request handler that redirects all requests to port 5000"""
    
    def do_GET(self):
        """Handle GET requests by redirecting to the main application"""
        self.send_response(302)  # Temporary redirect
        target_url = f"http://{self.headers.get('Host', 'localhost').split(':')[0]}:{TARGET_PORT}{self.path}"
        self.send_header('Location', target_url)
        self.end_headers()
    
    # Redirect all request types
    do_POST = do_GET
    do_PUT = do_GET
    do_DELETE = do_GET
    do_HEAD = do_GET
    do_OPTIONS = do_GET
    
    # Minimize logs to reduce noise
    def log_message(self, format, *args):
        return

def run_server():
    """Run the HTTP server on port 8080"""
    try:
        # Allow port reuse to prevent "Address already in use" errors
        socketserver.TCPServer.allow_reuse_address = True
        
        # Create and start the server
        with socketserver.TCPServer(("0.0.0.0", PORT), ProxyHandler) as httpd:
            print(f"Port 8080 standalone server is running")
            httpd.serve_forever()
    except Exception as e:
        print(f"Error starting server on port 8080: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    print(f"Starting standalone server on port 8080...")
    try:
        # Start the server in a separate thread
        server_thread = threading.Thread(target=run_server)
        server_thread.daemon = True
        server_thread.start()
        
        # Keep the script running until interrupted
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("Shutting down port 8080 server...")
        sys.exit(0)