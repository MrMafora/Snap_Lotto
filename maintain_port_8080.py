"""
Port 8080 Supervisor Script

This script continuously checks if a service is running on port 8080.
If not, it starts a simple HTTP server that redirects to port 5000.

It's a critical piece of infrastructure to support the web application feedback tool.
"""
import http.server
import socketserver
import socket
import threading
import time
import os
import sys
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    filename='port_8080.log',
    filemode='a'
)
logger = logging.getLogger(__name__)

# Also log to console
console = logging.StreamHandler()
console.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
console.setFormatter(formatter)
logger.addHandler(console)

class RedirectHandler(http.server.BaseHTTPRequestHandler):
    """Handler that redirects all requests to port 5000"""
    
    def redirect_request(self):
        """Send a redirect to the same path on port 5000"""
        self.send_response(302)
        self.send_header('Location', f'http://localhost:5000{self.path}')
        self.send_header('Connection', 'close')
        self.end_headers()
    
    def do_GET(self): self.redirect_request()
    def do_POST(self): self.redirect_request()
    def do_PUT(self): self.redirect_request()
    def do_DELETE(self): self.redirect_request()
    def do_HEAD(self): self.redirect_request() 
    def do_OPTIONS(self): self.redirect_request()
    
    # Suppress log messages
    def log_message(self, format, *args):
        return

def is_port_in_use(port):
    """Check if the specified port is already in use"""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex(('localhost', port)) == 0

def start_server():
    """Start the HTTP server on port 8080"""
    try:
        logger.info("Starting HTTP server on port 8080")
        with socketserver.TCPServer(("0.0.0.0", 8080), RedirectHandler) as httpd:
            logger.info("Server started on port 8080")
            httpd.serve_forever()
    except Exception as e:
        logger.error(f"Error starting server: {e}")

def server_supervisor():
    """Continuously monitor port 8080 and ensure a server is running"""
    logger.info("Starting port 8080 supervisor")
    
    while True:
        if not is_port_in_use(8080):
            logger.info("Port 8080 is not in use, starting server")
            thread = threading.Thread(target=start_server)
            thread.daemon = True
            thread.start()
        else:
            logger.debug("Port 8080 is already in use")
        
        # Check every 5 seconds
        time.sleep(5)

if __name__ == "__main__":
    logger.info("Starting port 8080 maintenance script")
    server_supervisor()