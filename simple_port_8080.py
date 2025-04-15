#!/usr/bin/env python3
"""
Simplified port 8080 proxy for Replit.
This script runs a simple HTTP server on port 8080 that forwards requests to the
main application on port 5000. This is a straightforward solution for Replit deployments.
"""
import http.server
import socketserver
import urllib.request
import threading
import logging
import sys
import os
import signal
import time

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('simple_port_8080')

class ProxyHandler(http.server.BaseHTTPRequestHandler):
    """Handler that forwards all requests to the application on port 5000"""
    
    def do_proxy(self):
        """Forward request to port 5000 and return the response"""
        # Construct the target URL
        target_path = self.path
        target_url = f"http://localhost:5000{target_path}"
        
        logger.info(f"Forwarding {self.command} request to {target_url}")
        
        try:
            # Create a request to the target
            req = urllib.request.Request(
                target_url,
                data=self.rfile.read(int(self.headers.get('Content-Length', 0))),
                headers=dict(self.headers),
                method=self.command
            )
            
            # Make the request
            with urllib.request.urlopen(req, timeout=30) as response:
                # Copy response status and headers
                self.send_response(response.status)
                for header, value in response.getheaders():
                    if header.lower() != 'transfer-encoding':
                        self.send_header(header, value)
                self.end_headers()
                
                # Copy response body
                self.wfile.write(response.read())
                
        except Exception as e:
            logger.error(f"Error forwarding request: {str(e)}")
            self.send_error(502, f"Error forwarding request: {str(e)}")
    
    # Handle all HTTP methods using the same logic
    do_GET = do_POST = do_PUT = do_DELETE = do_HEAD = do_OPTIONS = do_proxy
    
    def log_message(self, format, *args):
        """Custom logging for proxy requests"""
        logger.info(f"Port 8080: {args[0]} - {args[1]} {args[2]}")

def run_server():
    """Run the proxy server on port 8080"""
    server_address = ('0.0.0.0', 8080)
    
    # Check if port 5000 is available first
    # We need to make sure our main application is running
    success = False
    for _ in range(5):  # Try for up to 5 seconds
        try:
            response = urllib.request.urlopen("http://localhost:5000/", timeout=1)
            if response.status == 200:
                logger.info("Successfully connected to port 5000, main application is running")
                success = True
                break  # Port 5000 is working
        except Exception as e:
            logger.info(f"Waiting for port 5000 to become available... ({str(e)})")
            time.sleep(1)
    
    if not success:
        logger.warning("Could not verify port 5000, but proceeding anyway...")
        # Continue anyway, as we may have connectivity despite test failure
    
    logger.info(f"Starting proxy server on {server_address[0]}:{server_address[1]}")
    try:
        with socketserver.ThreadingTCPServer(server_address, ProxyHandler) as httpd:
            httpd.allow_reuse_address = True
            logger.info("Server started, waiting for requests...")
            print(f"Proxy server listening on port 8080, forwarding to port 5000")
            httpd.serve_forever()
    except Exception as e:
        logger.error(f"Error running server: {str(e)}")

if __name__ == "__main__":
    # Set up signal handlers
    def signal_handler(sig, frame):
        logger.info(f"Received signal {sig}, shutting down...")
        sys.exit(0)
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    try:
        run_server()
    except Exception as e:
        logger.error(f"Fatal error: {str(e)}")
        sys.exit(1)