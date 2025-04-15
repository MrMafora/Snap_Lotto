#!/usr/bin/env python3
"""
Simple bridge to forward requests from port 8080 to port 5000.
This ensures the application works with Replit's deployment requirements.
"""

import http.server
import socketserver
import urllib.request
import sys
import os
import threading
import signal
import logging
import time

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('port_bridge')

class BridgeHandler(http.server.BaseHTTPRequestHandler):
    """Handle HTTP requests by forwarding them to the application on port 5000"""
    
    def do_GET(self):
        """Handle GET requests"""
        self.proxy_request('GET')
    
    def do_POST(self):
        """Handle POST requests"""
        self.proxy_request('POST')
    
    def do_PUT(self):
        """Handle PUT requests"""
        self.proxy_request('PUT')
    
    def do_DELETE(self):
        """Handle DELETE requests"""
        self.proxy_request('DELETE')
        
    def do_HEAD(self):
        """Handle HEAD requests"""
        self.proxy_request('HEAD')
        
    def proxy_request(self, method):
        """Forward the request to the application on port 5000"""
        target_url = f"http://localhost:5000{self.path}"
        
        try:
            # Create and send request to the application
            content_length = int(self.headers.get('Content-Length', 0))
            body = self.rfile.read(content_length) if content_length > 0 else None
            
            headers = {k: v for k, v in self.headers.items()}
            
            # Create a Request object
            request = urllib.request.Request(
                target_url, 
                data=body,
                headers=headers,
                method=method
            )
            
            # Forward the request to the application
            response = urllib.request.urlopen(request)
            
            # Send the response back to the client
            self.send_response(response.status)
            
            # Forward response headers
            for header in response.getheaders():
                self.send_header(header[0], header[1])
            self.end_headers()
            
            # Forward response body
            self.wfile.write(response.read())
            
        except Exception as e:
            logger.error(f"Error proxying request: {str(e)}")
            self.send_response(500)
            self.end_headers()
            self.wfile.write(f"Error proxying request: {str(e)}".encode('utf-8'))
    
    def log_message(self, format, *args):
        """Override the default logging"""
        logger.info(f"{self.client_address[0]} - {args[0]}")

def run_bridge():
    """Run the bridge server"""
    port = 8080
    
    # Register signal handler
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    try:
        with socketserver.TCPServer(("0.0.0.0", port), BridgeHandler) as httpd:
            logger.info(f"Starting port bridge on 0.0.0.0:{port}")
            httpd.serve_forever()
    except OSError as e:
        logger.error(f"Could not start server: {str(e)}")
        sys.exit(1)

def signal_handler(sig, frame):
    """Handle signals gracefully"""
    logger.info("Shutting down port bridge")
    sys.exit(0)

if __name__ == "__main__":
    run_bridge()