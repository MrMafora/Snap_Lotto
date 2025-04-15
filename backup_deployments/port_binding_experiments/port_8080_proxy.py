"""
Port 8080 Proxy Server

This is a lightweight HTTP server that runs on port 8080 and
redirects all requests to the main application on port 5000.
It uses only standard library modules to ensure reliability.
"""
import http.server
import socketserver
import socket
import threading
import time
import sys
import os

class ProxyHandler(http.server.BaseHTTPRequestHandler):
    """HTTP handler that redirects all requests to port 5000"""
    
    def do_GET(self):
        """Handle GET requests with redirection"""
        self.send_response(302)
        host = self.headers.get('Host', 'localhost')
        if ':' in host:
            host = host.split(':')[0]  # Remove port if present
        redirect_url = f"http://{host}:5000{self.path}"
        self.send_header('Location', redirect_url)
        self.end_headers()
    
    # Apply the same handler to all HTTP methods
    do_POST = do_GET
    do_PUT = do_GET
    do_DELETE = do_GET
    do_HEAD = do_GET
    do_OPTIONS = do_GET
    
    # Suppress logging for cleaner output
    def log_message(self, format, *args):
        return

def is_port_available(port):
    """Check if a port is available for binding"""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        try:
            s.bind(('0.0.0.0', port))
            return True
        except socket.error:
            return False

def run_proxy_server():
    """Run the HTTP proxy server on port 8080"""
    try:
        # Check if the port is available
        if not is_port_available(8080):
            print(f"Port 8080 is already in use. Cannot start proxy server.")
            return
        
        # Enable address reuse to prevent "Address already in use" errors
        socketserver.TCPServer.allow_reuse_address = True
        
        # Create and start the server
        with socketserver.TCPServer(("0.0.0.0", 8080), ProxyHandler) as httpd:
            print(f"Port 8080 proxy server started successfully")
            httpd.serve_forever()
    except Exception as e:
        print(f"Error starting proxy server: {e}")

if __name__ == "__main__":
    print("Starting port 8080 proxy server...")
    
    # Start the server in a thread
    server_thread = threading.Thread(target=run_proxy_server, daemon=True)
    server_thread.start()
    
    try:
        # Keep the script running
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("Shutting down proxy server...")
        sys.exit(0)