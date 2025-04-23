#!/usr/bin/env python3
"""
Proxy Server for Snap Lotto Application

This script creates a simple proxy that listens on port 8080 and forwards
all requests to the main application running on port 5000.

This allows the feedback tool to connect to port 8080 while our actual
application runs on port 5000.
"""

import logging
import http.server
import socketserver
import urllib.request
import sys

# Set up logging
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('proxy_only')

def run_proxy_on_port_8080():
    """Start a proxy server on port 8080 that forwards to port 5000"""
    try:
        logger.info("Starting proxy on port 8080")
        
        # Using a simple Python HTTP server to handle connections on port 8080
        # and forward them to port 5000
        
        class ProxyHandler(http.server.BaseHTTPRequestHandler):
            def do_GET(self):
                self.proxy_request('GET')
                
            def do_POST(self):
                self.proxy_request('POST')
                
            def do_HEAD(self):
                self.proxy_request('HEAD')
                
            def proxy_request(self, method):
                try:
                    # Forward the request to port 5000
                    url = f"http://localhost:5000{self.path}"
                    logger.info(f"Forwarding {method} request to: {url}")
                    
                    # Read body for POST requests
                    content_length = int(self.headers.get('Content-Length', 0))
                    body = self.rfile.read(content_length) if content_length > 0 else None
                    
                    # Create request
                    req = urllib.request.Request(
                        url=url,
                        data=body,
                        method=method
                    )
                    
                    # Copy headers
                    for header in self.headers:
                        if header.lower() not in ('host', 'content-length'):
                            req.add_header(header, self.headers[header])
                    
                    # Send request
                    with urllib.request.urlopen(req) as response:
                        # Copy response status and headers
                        self.send_response(response.status)
                        for header in response.headers:
                            self.send_header(header, response.headers[header])
                        self.end_headers()
                        
                        # Copy response body (except for HEAD requests)
                        if method != 'HEAD':
                            self.wfile.write(response.read())
                except Exception as e:
                    logger.error(f"Error forwarding request: {e}")
                    self.send_response(502)
                    self.send_header('Content-type', 'text/plain')
                    self.end_headers()
                    self.wfile.write(f"Error: {str(e)}".encode())
            
            # Prevent logging every request to keep the console clean
            def log_message(self, format, *args):
                pass
        
        with socketserver.TCPServer(("0.0.0.0", 8080), ProxyHandler) as httpd:
            logger.info("Proxy server running on port 8080")
            httpd.serve_forever()
    except Exception as e:
        logger.error(f"Error running proxy on port 8080: {e}")

if __name__ == "__main__":
    logger.info("Starting proxy-only setup")
    run_proxy_on_port_8080()