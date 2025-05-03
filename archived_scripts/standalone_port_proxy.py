#!/usr/bin/env python3
"""
Standalone HTTP port proxy that binds directly to port 8080
and forwards all requests to the main application on port 5000.
"""
import os
import sys
import time
import socket
import logging
import http.server
import socketserver
import urllib.request
import urllib.error
from urllib.parse import urlparse

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('standalone_port_proxy')

# Target service details
TARGET_HOST = "localhost"
TARGET_PORT = 5000
TARGET_URL = f"http://{TARGET_HOST}:{TARGET_PORT}"
PROXY_PORT = int(os.environ.get('PORT', 8080))

def is_service_ready(host, port, timeout=1):
    """Check if the target service is running"""
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(timeout)
        result = sock.connect_ex((host, port))
        sock.close()
        return result == 0
    except socket.error:
        return False

def wait_for_service():
    """Wait for the target service to become available"""
    max_retries = 30
    retry_count = 0
    
    logger.info(f"Waiting for service at {TARGET_HOST}:{TARGET_PORT}...")
    
    while retry_count < max_retries:
        if is_service_ready(TARGET_HOST, TARGET_PORT):
            logger.info(f"Service at {TARGET_HOST}:{TARGET_PORT} is ready")
            return True
        
        retry_count += 1
        time.sleep(1)
    
    logger.error(f"Service at {TARGET_HOST}:{TARGET_PORT} did not become available after {max_retries} seconds")
    return False

class ProxyHTTPRequestHandler(http.server.BaseHTTPRequestHandler):
    """Handler for HTTP requests that forwards them to the target service"""
    
    def do_GET(self):
        """Handle GET requests"""
        self._forward_request('GET')
    
    def do_POST(self):
        """Handle POST requests"""
        content_length = int(self.headers.get('Content-Length', 0))
        post_data = self.rfile.read(content_length) if content_length else None
        self._forward_request('POST', post_data)
    
    def do_PUT(self):
        """Handle PUT requests"""
        content_length = int(self.headers.get('Content-Length', 0))
        put_data = self.rfile.read(content_length) if content_length else None
        self._forward_request('PUT', put_data)
    
    def do_DELETE(self):
        """Handle DELETE requests"""
        self._forward_request('DELETE')
    
    def do_OPTIONS(self):
        """Handle OPTIONS requests"""
        self._forward_request('OPTIONS')
    
    def do_HEAD(self):
        """Handle HEAD requests"""
        self._forward_request('HEAD')
    
    def _forward_request(self, method, body=None):
        """Forward the request to the target service"""
        target_url = f"{TARGET_URL}{self.path}"
        
        try:
            # Create request with headers
            req = urllib.request.Request(
                url=target_url,
                data=body,
                method=method
            )
            
            # Copy headers from original request
            for header, value in self.headers.items():
                if header.lower() != 'host':  # Skip host header
                    req.add_header(header, value)
            
            # Add forwarded headers
            req.add_header('X-Forwarded-For', self.client_address[0])
            req.add_header('X-Forwarded-Host', self.headers.get('Host', ''))
            req.add_header('X-Forwarded-Proto', 'http')
            
            # Send the request to the target service
            with urllib.request.urlopen(req, timeout=30) as response:
                # Set response status code
                self.send_response(response.status)
                
                # Copy response headers
                for header, value in response.getheaders():
                    self.send_header(header, value)
                self.end_headers()
                
                # Copy response body
                self.wfile.write(response.read())
        
        except urllib.error.HTTPError as e:
            # Forward HTTP errors
            self.send_response(e.code)
            for header, value in e.headers.items():
                self.send_header(header, value)
            self.end_headers()
            self.wfile.write(e.read())
        
        except Exception as e:
            # Handle other errors
            logger.error(f"Error forwarding request: {e}")
            self.send_response(502)  # Bad Gateway
            self.send_header('Content-Type', 'text/plain')
            self.end_headers()
            self.wfile.write(f"Error forwarding request: {e}".encode())
    
    def log_message(self, format, *args):
        """Override logging to use our logger"""
        logger.info(f"{self.client_address[0]} - {format % args}")

def run_proxy():
    """Run the proxy server"""
    try:
        with socketserver.TCPServer(("", PROXY_PORT), ProxyHTTPRequestHandler) as httpd:
            logger.info(f"Starting proxy server on port {PROXY_PORT}")
            httpd.serve_forever()
    except KeyboardInterrupt:
        logger.info("Proxy server stopped by user")
    except Exception as e:
        logger.error(f"Error running proxy server: {e}")
        return False
    return True

if __name__ == "__main__":
    # Wait for the target service to be ready
    if not wait_for_service():
        sys.exit(1)
    
    # Start the proxy server
    if not run_proxy():
        sys.exit(1)