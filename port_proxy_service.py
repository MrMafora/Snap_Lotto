#!/usr/bin/env python3
"""
Port Proxy Service for Snap Lotto Application

This script creates a permanent proxy between port 8080 and port 5000
to ensure the application is accessible via Replit's expected port.
"""
import http.server
import socketserver
import urllib.request
import urllib.error
import socket
import time
import logging
import sys
import os
import signal

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("proxy_service.log")
    ]
)
logger = logging.getLogger("port_proxy_service")

# Configuration
SOURCE_PORT = 8080  # Replit expects this port
DEST_PORT = 5000    # Flask/Gunicorn runs on this port
DEST_HOST = "localhost"
PID_FILE = "proxy.pid"

def create_pid_file():
    """Create a PID file to track this process"""
    with open(PID_FILE, 'w') as f:
        f.write(str(os.getpid()))
    logger.info(f"Created PID file with PID {os.getpid()}")

def cleanup():
    """Clean up resources when shutting down"""
    if os.path.exists(PID_FILE):
        os.remove(PID_FILE)
    logger.info("Proxy service shutting down")

def signal_handler(sig, frame):
    """Handle termination signals"""
    logger.info(f"Received signal {sig}, shutting down")
    cleanup()
    sys.exit(0)

class ProxyRequestHandler(http.server.BaseHTTPRequestHandler):
    """HTTP request handler to forward requests between ports"""
    
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
        """Forward any HTTP request to the destination server"""
        target_url = f"http://{DEST_HOST}:{DEST_PORT}{self.path}"
        logger.debug(f"Forwarding {method} request to {target_url}")
        
        # Get content length for methods that send data
        content_length = int(self.headers.get('Content-Length', 0))
        body = self.rfile.read(content_length) if content_length > 0 else None
        
        try:
            # Prepare request
            req = urllib.request.Request(target_url, data=body, method=method)
            
            # Copy headers
            for header, value in self.headers.items():
                if header.lower() not in ('host', 'content-length'):
                    req.add_header(header, value)
            
            # Forward request and get response
            with urllib.request.urlopen(req) as response:
                # Get response details
                response_body = response.read()
                status_code = response.getcode()
                response_headers = response.info()
            
            # Send response to client
            self.send_response(status_code)
            
            # Copy response headers
            for header, value in response_headers.items():
                if header.lower() not in ('server', 'date', 'transfer-encoding'):
                    self.send_header(header, value)
            
            self.end_headers()
            self.wfile.write(response_body)
            
        except urllib.error.HTTPError as e:
            # Forward HTTP errors
            self.send_response(e.code)
            
            for header, value in e.headers.items():
                if header.lower() not in ('server', 'date', 'transfer-encoding'):
                    self.send_header(header, value)
            
            self.end_headers()
            self.wfile.write(e.read())
            
        except Exception as e:
            # General error handling
            logger.error(f"Error forwarding request: {e}")
            self.send_response(502)  # Bad Gateway
            self.send_header('Content-Type', 'text/plain')
            self.end_headers()
            self.wfile.write(f"Proxy Error: {str(e)}".encode())
    
    def log_message(self, format, *args):
        """Override default logging to use our logger"""
        logger.info(f"{self.client_address[0]} - {format % args}")

def is_port_in_use(port):
    """Check if a port is already in use"""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex(('127.0.0.1', port)) == 0

def wait_for_destination():
    """Wait for the destination server to be ready"""
    max_retries = 30
    retry_count = 0
    
    logger.info(f"Waiting for destination server on port {DEST_PORT}...")
    
    while retry_count < max_retries:
        if is_port_in_use(DEST_PORT):
            logger.info(f"Destination server is running on port {DEST_PORT}")
            return True
        
        retry_count += 1
        time.sleep(1)
    
    logger.error(f"Destination server not available after {max_retries} seconds")
    return False

def start_proxy_server():
    """Start the HTTP proxy server"""
    
    # Set up signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Create PID file
    create_pid_file()
    
    # Wait for destination server
    if not wait_for_destination():
        logger.error("Cannot start proxy - destination server not available")
        cleanup()
        return 1
    
    # Start server
    try:
        # Allow port reuse to handle server restarts
        socketserver.TCPServer.allow_reuse_address = True
        
        with socketserver.ThreadingTCPServer(("", SOURCE_PORT), ProxyRequestHandler) as httpd:
            logger.info(f"Starting proxy server on port {SOURCE_PORT} forwarding to port {DEST_PORT}")
            httpd.serve_forever()
    except Exception as e:
        logger.error(f"Error starting proxy server: {e}")
        cleanup()
        return 1
    finally:
        cleanup()
    
    return 0

if __name__ == "__main__":
    logger.info("Starting port proxy service")
    sys.exit(start_proxy_server())