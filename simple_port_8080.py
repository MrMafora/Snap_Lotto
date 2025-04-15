#!/usr/bin/env python3
"""
Simple HTTP server that listens on port 8080 and forwards all requests to port 5000.
This script solves the Replit external access requirement without modifying the main application.
"""
import http.server
import socketserver
import urllib.request
import urllib.error
import logging
import signal
import sys
import threading
import time

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    filename='simple_8080.log',
    filemode='a'
)
logger = logging.getLogger('port8080')

# Also log to console
console = logging.StreamHandler()
console.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
console.setFormatter(formatter)
logger.addHandler(console)

class ForwardingHandler(http.server.BaseHTTPRequestHandler):
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
    
    def forward_request(self, method):
        target_url = f"http://localhost:5000{self.path}"
        
        try:
            # Get headers from the incoming request
            headers = {}
            for key, val in self.headers.items():
                # Skip hop-by-hop headers
                if key.lower() not in ('connection', 'keep-alive', 'proxy-authenticate', 
                                      'proxy-authorization', 'te', 'trailers', 
                                      'transfer-encoding', 'upgrade'):
                    headers[key] = val
            
            # Get content length for request body
            content_length = int(self.headers.get('Content-Length', 0))
            body = None
            if content_length > 0:
                body = self.rfile.read(content_length)
            
            # Create and send request to port 5000
            req = urllib.request.Request(
                url=target_url,
                data=body,
                headers=headers,
                method=method
            )
            
            try:
                # Send the request to port 5000
                with urllib.request.urlopen(req, timeout=30) as response:
                    # Copy status code
                    self.send_response(response.getcode())
                    
                    # Copy headers
                    for header, value in response.getheaders():
                        if header.lower() != 'transfer-encoding':
                            self.send_header(header, value)
                    self.end_headers()
                    
                    # Copy body
                    self.wfile.write(response.read())
                    
                logger.info(f"Forwarded {method} {self.path} to port 5000, status: {response.getcode()}")
                
            except urllib.error.HTTPError as e:
                # Forward HTTP errors from port 5000
                self.send_response(e.code)
                for header, value in e.headers.items():
                    if header.lower() != 'transfer-encoding':
                        self.send_header(header, value)
                self.end_headers()
                self.wfile.write(e.read())
                logger.warning(f"Forwarded HTTP error {e.code} for {method} {self.path}")
                
            except urllib.error.URLError as e:
                # Handle connection errors
                self.send_error(502, f"Error connecting to port 5000: {str(e)}")
                logger.error(f"URLError forwarding {method} {self.path}: {str(e)}")
                
        except Exception as e:
            # Handle any other errors
            self.send_error(500, f"Internal Server Error: {str(e)}")
            logger.error(f"Error forwarding {method} {self.path}: {str(e)}")
            
    def log_message(self, format, *args):
        # Override default logging to use our logger
        logger.info(f"{self.client_address[0]} - {format % args}")

def wait_for_port_5000():
    """Wait for the main application to start on port 5000"""
    logger.info("Waiting for main application to start on port 5000...")
    
    for attempt in range(5):  # 5 second timeout - shorter to avoid blocking
        try:
            with urllib.request.urlopen("http://localhost:5000/", timeout=1) as response:
                if response.getcode() == 200:
                    logger.info("Main application is running on port 5000")
                    return True
        except Exception as e:
            logger.warning(f"Connection attempt {attempt+1} failed: {str(e)}")
            time.sleep(1)
    
    # Continue anyway since Replit app might already be running
    logger.warning("Continuing without confirming port 5000 is available")
    return True  # Return True to continue even if port 5000 isn't immediately available

def run_server():
    """Run the HTTP server on port 8080"""
    # Skip port 5000 check - we know it's running
    logger.info("Skipping port 5000 check and starting 8080 server immediately")
    
    try:
        # Create the HTTP server
        handler = ForwardingHandler
        # Set allow_reuse_address before creating the server
        socketserver.TCPServer.allow_reuse_address = True
        httpd = socketserver.TCPServer(("0.0.0.0", 8080), handler)
        
        logger.info("Starting HTTP server on port 8080")
        print(f"Server running on 0.0.0.0:8080, forwarding to port 5000")
        
        # Define signal handler for clean shutdown
        def signal_handler(sig, frame):
            logger.info("Shutdown signal received, stopping server")
            httpd.shutdown()
            sys.exit(0)
        
        # Register signal handlers
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
        
        # Start the server
        httpd.serve_forever()
        
    except Exception as e:
        logger.error(f"Error starting server: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    logger.info("Starting port 8080 forwarding service")
    run_server()