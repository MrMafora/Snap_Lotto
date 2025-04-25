#!/usr/bin/env python3
"""
Simple HTTP port forwarding script that forwards all traffic
from port 8080 to port 5000 for Replit compatibility
"""
import http.server
import socketserver
import urllib.request
import urllib.error
import socket
import time
import threading
import os
import logging
import sys

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler("proxy_output.log")
    ]
)
logger = logging.getLogger("simple_proxy")

SOURCE_PORT = 8080
DEST_PORT = 5000
DEST_HOST = "localhost"

class ProxyHandler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        self._proxy_request("GET")
        
    def do_POST(self):
        self._proxy_request("POST")
        
    def do_PUT(self):
        self._proxy_request("PUT")
        
    def do_DELETE(self):
        self._proxy_request("DELETE")
        
    def do_HEAD(self):
        self._proxy_request("HEAD")
        
    def do_OPTIONS(self):
        self._proxy_request("OPTIONS")
        
    def do_PATCH(self):
        self._proxy_request("PATCH")
    
    def _proxy_request(self, method):
        logger.info(f"Forwarding {method} request: {self.path}")
        target_url = f"http://{DEST_HOST}:{DEST_PORT}{self.path}"
        
        # Get content length for methods that send data
        content_length = int(self.headers.get('Content-Length', 0))
        body = self.rfile.read(content_length) if content_length > 0 else None
        
        try:
            # Build request
            req = urllib.request.Request(
                target_url,
                data=body,
                method=method
            )
            
            # Copy request headers
            for header, value in self.headers.items():
                if header.lower() not in ('host', 'content-length'):
                    req.add_header(header, value)
            
            # Send request to destination
            with urllib.request.urlopen(req) as response:
                # Get response details
                response_body = response.read()
                status_code = response.getcode()
                response_headers = response.info()
            
            # Send response back to client
            self.send_response(status_code)
            
            # Forward response headers
            for header, value in response_headers.items():
                if header.lower() not in ('server', 'date', 'transfer-encoding'):
                    self.send_header(header, value)
            
            self.end_headers()
            self.wfile.write(response_body)
            
        except urllib.error.HTTPError as e:
            logger.error(f"HTTPError: {e.code} - {e.reason}")
            self.send_response(e.code)
            
            for header, value in e.headers.items():
                if header.lower() not in ('server', 'date', 'transfer-encoding'):
                    self.send_header(header, value)
            
            self.end_headers()
            self.wfile.write(e.read())
            
        except Exception as e:
            logger.error(f"Error proxying request: {e}")
            self.send_response(502)  # Bad Gateway
            self.send_header('Content-Type', 'text/plain')
            self.end_headers()
            self.wfile.write(f"Proxy Error: {str(e)}".encode('utf-8'))
    
    def log_message(self, format, *args):
        logger.info(f"{self.client_address[0]} - {format % args}")

def is_port_available(port):
    """Check if a port is available"""
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    result = sock.connect_ex(('127.0.0.1', port))
    sock.close()
    return result != 0

def wait_for_destination():
    """Wait for destination port 5000 to be ready"""
    logger.info(f"Waiting for service on port {DEST_PORT}...")
    max_attempts = 30
    for attempt in range(max_attempts):
        is_open = not is_port_available(DEST_PORT)
        if is_open:
            logger.info(f"Service on port {DEST_PORT} is ready!")
            return True
        time.sleep(1)
    logger.error(f"Service on port {DEST_PORT} not available after {max_attempts} seconds")
    return False

def run_proxy_server():
    """Run the proxy server on port 8080"""
    if not wait_for_destination():
        return

    # Ensure port 8080 is available
    if not is_port_available(SOURCE_PORT):
        logger.warning(f"Port {SOURCE_PORT} is already in use, attempting to reuse")
    
    try:
        with socketserver.ThreadingTCPServer(("", SOURCE_PORT), ProxyHandler) as httpd:
            httpd.allow_reuse_address = True
            logger.info(f"Proxy server started on port {SOURCE_PORT} -> {DEST_PORT}")
            httpd.serve_forever()
    except KeyboardInterrupt:
        logger.info("Proxy server stopped by user")
    except Exception as e:
        logger.error(f"Error running proxy server: {e}")

if __name__ == "__main__":
    logger.info("Starting proxy server")
    run_proxy_server()