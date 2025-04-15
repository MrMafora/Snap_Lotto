#!/usr/bin/env python3
"""
Simple port 8080 redirector for Replit deployment.
This script provides a minimal HTTP server that listens on port 8080 
and forwards all requests to the main application on port 5000.
"""
import http.server
import socketserver
import urllib.request
import urllib.error
import os
import sys
import time
import threading
import signal
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('port8080_redirector')

# Constants
PORT_8080 = 8080
PORT_5000 = 5000
HOST = "0.0.0.0"
LOCAL_HOST = "127.0.0.1"

class RedirectorHandler(http.server.BaseHTTPRequestHandler):
    """HTTP handler that redirects all requests to port 5000"""
    
    def do_GET(self):
        self.redirect_request("GET")
    
    def do_POST(self):
        self.redirect_request("POST")
    
    def do_PUT(self):
        self.redirect_request("PUT")
    
    def do_DELETE(self):
        self.redirect_request("DELETE")
    
    def do_HEAD(self):
        self.redirect_request("HEAD")
    
    def do_OPTIONS(self):
        self.redirect_request("OPTIONS")
    
    def do_PATCH(self):
        self.redirect_request("PATCH")
    
    def redirect_request(self, method):
        """Forward all requests to port 5000"""
        target_url = f"http://{LOCAL_HOST}:{PORT_5000}{self.path}"
        
        try:
            # Get request body (if any)
            content_length = int(self.headers.get('Content-Length', 0))
            body_data = None
            if content_length > 0:
                body_data = self.rfile.read(content_length)
            
            # Create request to forward
            req = urllib.request.Request(
                url=target_url,
                data=body_data,
                method=method
            )
            
            # Copy request headers
            for header, value in self.headers.items():
                if header.lower() not in ('content-length', 'host'):
                    req.add_header(header, value)
            
            # Send the request
            with urllib.request.urlopen(req, timeout=10) as response:
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
            
            # Copy error headers
            for header, value in e.headers.items():
                self.send_header(header, value)
            self.end_headers()
            
            # Copy error body
            if e.fp:
                self.wfile.write(e.fp.read())
                
        except Exception as e:
            # Handle other errors
            logger.error(f"Error forwarding request: {str(e)}")
            self.send_error(502, f"Error forwarding request: {str(e)}")
    
    def log_message(self, format, *args):
        """Override to use our logger"""
        logger.info(f"{self.client_address[0]} - {format % args}")

class ThreadingHTTPServer(socketserver.ThreadingMixIn, http.server.HTTPServer):
    """Use threading to handle requests in separate threads"""
    daemon_threads = True

def check_target_app():
    """Check if the target application is running"""
    logger.info(f"Checking if target application is running on port {PORT_5000}...")
    
    try:
        with urllib.request.urlopen(f"http://{LOCAL_HOST}:{PORT_5000}/health_check", timeout=2) as response:
            if response.status == 200:
                logger.info(f"Target application is running on port {PORT_5000}")
                return True
    except Exception as e:
        logger.warning(f"Target application check failed: {str(e)}")
    
    return False

def wait_for_target_app(max_attempts=30, delay=2):
    """Wait for target application to become available"""
    logger.info(f"Waiting for target application on port {PORT_5000}...")
    
    for attempt in range(max_attempts):
        if check_target_app():
            return True
        
        if attempt < max_attempts - 1:
            logger.info(f"Attempt {attempt+1}/{max_attempts}: Target application not ready. Waiting {delay} seconds...")
            time.sleep(delay)
    
    logger.error(f"Target application did not become available after {max_attempts} attempts")
    return False

def run_redirector():
    """Start the redirector on port 8080"""
    # Check if port 8080 is already in use
    try:
        test_socket = socketserver.TCPServer((HOST, PORT_8080), http.server.BaseHTTPRequestHandler)
        test_socket.server_close()
    except OSError as e:
        logger.error(f"Port {PORT_8080} is already in use: {str(e)}")
        logger.error("Please free up port 8080 before running this script")
        return False
    
    # Start the server
    try:
        server = ThreadingHTTPServer((HOST, PORT_8080), RedirectorHandler)
        
        def signal_handler(sig, frame):
            logger.info(f"Received signal {sig}, shutting down...")
            server.shutdown()
            sys.exit(0)
        
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
        
        logger.info(f"Starting HTTP redirector on {HOST}:{PORT_8080} -> {LOCAL_HOST}:{PORT_5000}")
        server.serve_forever()
    except Exception as e:
        logger.error(f"Failed to start redirector: {str(e)}")
        return False
    
    return True

if __name__ == "__main__":
    logger.info("=== Simple Port 8080 Redirector ===")
    
    # First check if target application is available
    if not check_target_app():
        # Wait for target application to start
        if not wait_for_target_app():
            logger.error("Target application is not available. Exiting.")
            sys.exit(1)
    
    # Run the redirector
    success = run_redirector()
    sys.exit(0 if success else 1)