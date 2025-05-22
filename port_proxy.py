#!/usr/bin/env python3
"""
Simple HTTP proxy server to forward requests between ports

This proxy forwards requests from port 8080 to port 5000
to ensure compatibility with Replit's expected port configuration.
"""
import os
import sys
import http.server
import socketserver
import threading
import urllib.request
import urllib.error
import socket
import time
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("port_proxy")

# Define constants
SOURCE_PORT = 8080
DESTINATION_PORT = 5000
DESTINATION_HOST = "localhost"
PID_FILE = "proxy.pid"
MAX_RETRIES = 30  # Wait up to 30 seconds for server to start

def create_pid_file():
    """Create a PID file for the proxy process"""
    with open(PID_FILE, 'w') as f:
        f.write(str(os.getpid()))
    logger.info(f"PID file created with PID {os.getpid()}")

def remove_pid_file():
    """Remove the PID file on exit"""
    if os.path.exists(PID_FILE):
        os.remove(PID_FILE)
        logger.info("PID file removed")

class ProxyHandler(http.server.BaseHTTPRequestHandler):
    """HTTP request handler to forward requests"""
    
    def do_GET(self):
        self._forward_request('GET')
        
    def do_POST(self):
        self._forward_request('POST')
        
    def do_PUT(self):
        self._forward_request('PUT')
        
    def do_DELETE(self):
        self._forward_request('DELETE')
        
    def do_HEAD(self):
        self._forward_request('HEAD')
    
    def do_OPTIONS(self):
        self._forward_request('OPTIONS')
        
    def do_PATCH(self):
        self._forward_request('PATCH')
        
    def _forward_request(self, method):
        """Forward requests to destination server"""
        destination_url = f"http://{DESTINATION_HOST}:{DESTINATION_PORT}{self.path}"
        logger.debug(f"Forwarding {method} request to {destination_url}")
        
        # Get content length for methods that send data
        content_length = int(self.headers.get('Content-Length', 0))
        body = self.rfile.read(content_length) if content_length > 0 else None
        
        # Forward request
        try:
            req = urllib.request.Request(destination_url, data=body, method=method)
            
            # Copy request headers
            for header, value in self.headers.items():
                if header.lower() not in ('host', 'content-length'):
                    req.add_header(header, value)
            
            # Get response
            with urllib.request.urlopen(req) as response:
                response_data = response.read()
                response_headers = response.info()
                response_code = response.getcode()
            
            # Send response back to client
            self.send_response(response_code)
            
            # Forward response headers
            for header, value in response_headers.items():
                if header.lower() not in ('server', 'date', 'transfer-encoding'):
                    self.send_header(header, value)
            
            self.end_headers()
            self.wfile.write(response_data)
            
        except urllib.error.HTTPError as e:
            # Forward HTTP errors
            self.send_response(e.code)
            
            for header, value in e.headers.items():
                if header.lower() not in ('server', 'date', 'transfer-encoding'):
                    self.send_header(header, value)
            
            self.end_headers()
            self.wfile.write(e.read())
            
        except Exception as e:
            # Handle other errors
            logger.error(f"Error forwarding request: {e}")
            self.send_response(502)
            self.send_header('Content-Type', 'text/plain')
            self.end_headers()
            self.wfile.write(b"Bad Gateway")
    
    def log_message(self, format, *args):
        """Override default logging to use our logger"""
        logger.info(f"{self.client_address[0]} - {format % args}")

def check_destination_server():
    """Check if destination server is running"""
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(1)
        result = sock.connect_ex((DESTINATION_HOST, DESTINATION_PORT))
        sock.close()
        return result == 0
    except:
        return False

def wait_for_destination_server():
    """Wait for destination server to start"""
    logger.info(f"Waiting for destination server on port {DESTINATION_PORT}...")
    
    for i in range(MAX_RETRIES):
        if check_destination_server():
            logger.info(f"Destination server is running on port {DESTINATION_PORT}")
            return True
        
        time.sleep(1)
    
    logger.error(f"Destination server not available after {MAX_RETRIES} seconds")
    return False

def start_proxy():
    """Start the proxy server"""
    try:
        # Wait for destination server
        if not wait_for_destination_server():
            logger.error("Cannot start proxy - destination server is not available")
            sys.exit(1)
            
        # Create TCP server
        httpd = socketserver.ThreadingTCPServer(('', SOURCE_PORT), ProxyHandler)
        httpd.allow_reuse_address = True
        
        # Record PID
        create_pid_file()
        
        # Start serving
        logger.info(f"Starting proxy server on port {SOURCE_PORT} forwarding to port {DESTINATION_PORT}")
        httpd.serve_forever()
        
    except KeyboardInterrupt:
        logger.info("Stopping proxy server due to keyboard interrupt")
    except Exception as e:
        logger.error(f"Error in proxy server: {e}")
    finally:
        remove_pid_file()
        logger.info("Proxy server stopped")

if __name__ == "__main__":
    logger.info("Starting port proxy")
    start_proxy()