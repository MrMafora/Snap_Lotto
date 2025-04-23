#!/usr/bin/env python3
"""
Dual Port Server for Snap Lotto Application

This script creates a simple Flask application that listens on both
port 5000 (for the main application) and port 8080 (for the feedback tool).

This allows the feedback tool to connect to port 8080 while our actual
application runs on port 5000.
"""

import logging
import os
import sys
import threading
import time

# Set up logging
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('both_ports')

def run_on_port_5000():
    """Start the main Flask application on port 5000"""
    try:
        logger.info("Starting main application on port 5000")
        os.system("gunicorn --bind 0.0.0.0:5000 --workers=2 --worker-class=gthread --threads=2 --timeout=60 --reload main:app")
    except Exception as e:
        logger.error(f"Error running on port 5000: {e}")

def run_proxy_on_port_8080():
    """Start a proxy server on port 8080 that forwards to port 5000"""
    try:
        logger.info("Starting proxy on port 8080")
        
        # Using a simple Python HTTP server to handle connections on port 8080
        # and forward them to port 5000
        import http.server
        import socketserver
        import urllib.request

        class ProxyHandler(http.server.BaseHTTPRequestHandler):
            def do_GET(self):
                try:
                    # Forward the request to port 5000
                    url = f"http://localhost:5000{self.path}"
                    response = urllib.request.urlopen(url)
                    
                    # Copy the response
                    self.send_response(response.status)
                    for header in response.getheaders():
                        self.send_header(header[0], header[1])
                    self.end_headers()
                    self.wfile.write(response.read())
                except Exception as e:
                    logger.error(f"Error forwarding request: {e}")
                    self.send_response(502)
                    self.send_header('Content-type', 'text/plain')
                    self.end_headers()
                    self.wfile.write(f"Error: {str(e)}".encode())
            
            # Prevent logging every request to keep the console clean
            def log_message(self, format, *args):
                if args[1] == '404':
                    logger.warning(f"404 error: {args[0]} - {args[2]}")
                return
        
        with socketserver.TCPServer(("0.0.0.0", 8080), ProxyHandler) as httpd:
            logger.info("Proxy server running on port 8080")
            httpd.serve_forever()
    except Exception as e:
        logger.error(f"Error running proxy on port 8080: {e}")

if __name__ == "__main__":
    logger.info("Starting dual-port setup")
    
    # Start the main application on port 5000 in a separate thread
    app_thread = threading.Thread(target=run_on_port_5000)
    app_thread.daemon = True
    app_thread.start()
    
    # Give the main application time to start
    time.sleep(5)
    
    # Start the proxy on port 8080 (in this thread)
    run_proxy_on_port_8080()