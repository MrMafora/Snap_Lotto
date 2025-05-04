#!/usr/bin/env python3
"""
Simple Port Forwarder for Replit Compatibility

This script creates a very simple HTTP server that listens on port 8080
and forwards all requests to the main application on port 5000.

Run this script alongside the main application to make it accessible on
both port 5000 (directly) and port 8080 (via this proxy).
"""

from http.server import BaseHTTPRequestHandler, HTTPServer
import urllib.request
import logging
import sys

# Configure logging
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('port_forward')

class ProxyHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        try:
            # Create a URL for the proxy request
            target_url = f"http://localhost:5000{self.path}"
            logger.info(f"Forwarding request to: {target_url}")
            
            # Forward the request to the main application
            response = urllib.request.urlopen(target_url)
            
            # Send response status code
            self.send_response(response.status)
            
            # Send headers
            for header in response.getheaders():
                self.send_header(header[0], header[1])
            self.end_headers()
            
            # Send body
            self.wfile.write(response.read())
            
        except Exception as e:
            logger.error(f"Error forwarding request: {e}")
            self.send_response(502)  # Bad Gateway
            self.send_header('Content-type', 'text/plain')
            self.end_headers()
            self.wfile.write(f"Error: {str(e)}".encode())
    
    # Also handle POST requests
    def do_POST(self):
        try:
            # Get the content length
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            
            # Create a URL for the proxy request
            target_url = f"http://localhost:5000{self.path}"
            logger.info(f"Forwarding POST request to: {target_url}")
            
            # Set up the request with the same headers and body
            headers = {}
            for header in self.headers:
                headers[header] = self.headers[header]
            
            # Create the request
            req = urllib.request.Request(
                target_url, 
                data=post_data,
                headers=headers,
                method='POST'
            )
            
            # Forward the request to the main application
            response = urllib.request.urlopen(req)
            
            # Send response status code
            self.send_response(response.status)
            
            # Send headers
            for header in response.getheaders():
                self.send_header(header[0], header[1])
            self.end_headers()
            
            # Send body
            self.wfile.write(response.read())
            
        except Exception as e:
            logger.error(f"Error forwarding POST request: {e}")
            self.send_response(502)  # Bad Gateway
            self.send_header('Content-type', 'text/plain')
            self.end_headers()
            self.wfile.write(f"Error: {str(e)}".encode())
    
    # Minimize logging output to keep the console clean
    def log_message(self, format, *args):
        # Only log errors
        if args[1].startswith('5') or args[1].startswith('4'):
            logger.warning(f"{args[0]} - {args[1]} - {args[2]}")
        return

def run_proxy(port=8080):
    """Run the proxy server on the specified port"""
    server_address = ('', port)
    httpd = HTTPServer(server_address, ProxyHandler)
    logger.info(f"Starting proxy server on port {port}")
    logger.info(f"Forwarding to main application on port 5000")
    httpd.serve_forever()

if __name__ == "__main__":
    # Run the proxy server on port 8080
    run_proxy()