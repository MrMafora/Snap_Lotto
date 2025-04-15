#!/usr/bin/env python3
"""
Simple port 8080 forwarding script for the lottery application.
This script listens on port 8080 and forwards all requests to port 5000.
"""
import http.server
import socketserver
import urllib.request
import urllib.error
import logging
import time
import threading
import os
import signal
import sys

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('port8080')

# Configuration
SOURCE_PORT = 8080
TARGET_PORT = 5000
HOST = "0.0.0.0"
LOCAL_HOST = "127.0.0.1"

class ForwardingHandler(http.server.BaseHTTPRequestHandler):
    """HTTP request handler to forward requests to another port"""
    
    def do_GET(self):
        self.forward_request('GET')
    
    def do_POST(self):
        self.forward_request('POST')
    
    def do_PUT(self):
        self.forward_request('PUT')
    
    def do_DELETE(self):
        self.forward_request('DELETE')
    
    def do_HEAD(self):
        self.forward_request('HEAD')
    
    def do_OPTIONS(self):
        self.forward_request('OPTIONS')
    
    def do_PATCH(self):
        self.forward_request('PATCH')
    
    def forward_request(self, method):
        """Forward request to target port"""
        target_url = f'http://{LOCAL_HOST}:{TARGET_PORT}{self.path}'
        
        # Read request body if present
        content_length = int(self.headers.get('Content-Length', 0))
        body = self.rfile.read(content_length) if content_length > 0 else None
        
        # Create request
        request = urllib.request.Request(
            url=target_url,
            data=body,
            method=method
        )
        
        # Copy headers
        for header, value in self.headers.items():
            if header.lower() not in ('content-length', 'host'):
                request.add_header(header, value)
        
        try:
            # Forward request
            response = urllib.request.urlopen(request)
            
            # Copy response status
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
            if e.fp:
                self.wfile.write(e.fp.read())
        except Exception as e:
            # Handle other errors
            logger.error(f"Error forwarding request: {str(e)}")
            self.send_error(502, f"Error forwarding request: {str(e)}")
    
    def log_message(self, format, *args):
        """Override default logging"""
        logger.info(f"{self.client_address[0]} - {format % args}")

def wait_for_target():
    """Wait for target port to become available"""
    max_attempts = 10
    for attempt in range(max_attempts):
        try:
            # Try to connect to target port
            with urllib.request.urlopen(f'http://{LOCAL_HOST}:{TARGET_PORT}/health_check', timeout=1) as response:
                if response.status == 200:
                    logger.info(f"Target port {TARGET_PORT} is ready")
                    return True
        except Exception:
            # If connection failed, wait and retry
            if attempt < max_attempts - 1:
                logger.info(f"Waiting for target port {TARGET_PORT}... (attempt {attempt+1}/{max_attempts})")
                time.sleep(2)
    
    logger.error(f"Target port {TARGET_PORT} is not available after {max_attempts} attempts")
    return False

def start_server():
    """Start the forwarding server"""
    logger.info(f"Starting port forwarding from {SOURCE_PORT} to {TARGET_PORT}...")
    
    try:
        # Create server
        handler = ForwardingHandler
        server = socketserver.ThreadingTCPServer((HOST, SOURCE_PORT), handler)
        
        # Set up graceful shutdown on termination signals
        def signal_handler(sig, frame):
            logger.info(f"Received signal {sig}, shutting down...")
            server.shutdown()
            sys.exit(0)
        
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
        
        # Run the server in a separate thread
        server_thread = threading.Thread(target=server.serve_forever)
        server_thread.daemon = True
        server_thread.start()
        
        logger.info(f"Server started on port {SOURCE_PORT}, forwarding to port {TARGET_PORT}")
        
        # Keep the main thread alive
        while True:
            time.sleep(1)
    
    except Exception as e:
        logger.error(f"Error starting server: {str(e)}")
        return False
    
    return True

if __name__ == "__main__":
    logger.info("=== Simple Port 8080 Forwarding ===")
    
    # Wait for target port
    if wait_for_target():
        # Start forwarding server
        start_server()
    else:
        logger.error("Aborting due to target port unavailability")
        sys.exit(1)