#!/usr/bin/env python3
"""
Simple HTTP proxy server that forwards requests from port 8080 to port 5000
"""
import os
import http.server
import socketserver
import urllib.request
import urllib.error
import threading
import logging
import socket
import time

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('http_port_proxy')

# Configuration
SOURCE_PORT = 8080
DESTINATION_PORT = 5000
DESTINATION_HOST = "localhost"
PID_FILE = "http_proxy.pid"

def create_pid_file():
    """Create a PID file for the proxy process"""
    with open(PID_FILE, 'w') as f:
        f.write(str(os.getpid()))
    logger.info(f"PID file created with PID {os.getpid()}")

def remove_pid_file():
    """Remove the PID file on exit"""
    try:
        os.remove(PID_FILE)
        logger.info("PID file removed")
    except FileNotFoundError:
        pass

def forward_request(path, method, headers, body=None):
    """Forward an HTTP request to the destination server"""
    destination_url = f"http://{DESTINATION_HOST}:{DESTINATION_PORT}{path}"
    logger.debug(f"Forwarding {method} request to {destination_url}")
    
    try:
        req = urllib.request.Request(destination_url, data=body, method=method)
        
        # Copy headers
        for header, value in headers.items():
            if header.lower() not in ('host', 'content-length'):
                req.add_header(header, value)
        
        with urllib.request.urlopen(req) as response:
            response_data = response.read()
            response_headers = response.info()
            response_code = response.getcode()
            return response_code, response_headers, response_data
    except urllib.error.HTTPError as e:
        return e.code, e.headers, e.read()
    except Exception as e:
        logger.error(f"Error forwarding request: {e}")
        return 502, {}, b"Bad Gateway"

class ProxyHandler(http.server.BaseHTTPRequestHandler):
    """HTTP handler that forwards requests to the destination server"""
    
    def do_GET(self):
        self._forward_request("GET")
    
    def do_POST(self):
        self._forward_request("POST")
    
    def do_PUT(self):
        self._forward_request("PUT")
    
    def do_DELETE(self):
        self._forward_request("DELETE")
    
    def do_HEAD(self):
        self._forward_request("HEAD")
    
    def do_OPTIONS(self):
        self._forward_request("OPTIONS")
    
    def do_PATCH(self):
        self._forward_request("PATCH")
    
    def _forward_request(self, method):
        """Common method to forward any HTTP request"""
        # Get request body for methods that have one
        content_length = int(self.headers.get('Content-Length', 0))
        body = self.rfile.read(content_length) if content_length > 0 else None
        
        # Forward the request
        status_code, response_headers, response_data = forward_request(
            self.path, method, self.headers, body
        )
        
        # Return the response
        self.send_response(status_code)
        
        # Forward response headers
        for header, value in response_headers.items():
            if header.lower() not in ('server', 'date', 'transfer-encoding'):
                self.send_header(header, value)
        
        self.end_headers()
        self.wfile.write(response_data)
    
    def log_message(self, format, *args):
        """Override the default logging to use our logger"""
        logger.info(f"{self.client_address[0]} - - {format % args}")

def check_destination_reachable():
    """Check if the destination server is running"""
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(1)
        result = sock.connect_ex((DESTINATION_HOST, DESTINATION_PORT))
        sock.close()
        return result == 0
    except:
        return False

def wait_for_destination():
    """Wait for the destination server to start"""
    logger.info(f"Waiting for destination server on port {DESTINATION_PORT}...")
    retry_count = 0
    max_retries = 30  # Wait up to 30 seconds
    
    while retry_count < max_retries:
        if check_destination_reachable():
            logger.info(f"Destination server is now running on port {DESTINATION_PORT}")
            return True
        
        time.sleep(1)
        retry_count += 1
    
    logger.error(f"Destination server not available after {max_retries} seconds")
    return False

def start_proxy_server():
    """Start the HTTP proxy server"""
    try:
        # Create a TCP server with our handler
        httpd = socketserver.ThreadingTCPServer(('', SOURCE_PORT), ProxyHandler)
        httpd.allow_reuse_address = True
        
        logger.info(f"Starting HTTP proxy server on port {SOURCE_PORT}")
        create_pid_file()
        
        # Start serving requests
        httpd.serve_forever()
    except KeyboardInterrupt:
        logger.info("Proxy server stopping due to keyboard interrupt")
    except Exception as e:
        logger.error(f"Error in proxy server: {e}")
    finally:
        remove_pid_file()
        logger.info("Proxy server stopped")

if __name__ == "__main__":
    try:
        # Wait for the destination server
        if wait_for_destination():
            # Start the proxy server
            start_proxy_server()
        else:
            logger.error("Cannot start proxy - destination server is not available")
            exit(1)
    except KeyboardInterrupt:
        logger.info("Proxy shutdown requested")
    except Exception as e:
        logger.error(f"Unhandled exception: {e}")
        exit(1)
    finally:
        remove_pid_file()