#!/usr/bin/env python3
"""
Run application with dual port binding for Replit.
This script:
1. Starts main application on port 5000 using Gunicorn (via main:app)
2. Starts a proxy server on port 8080 that forwards to port 5000

This ensures the application is accessible both internally (port 5000)
and externally via Replit's expected port (8080).
"""
import http.server
import logging
import os
import signal
import socketserver
import subprocess
import sys
import threading
import time
import urllib.request

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('run_with_proxy')

def start_main_application():
    """Start the main Flask application using Gunicorn on port 5000"""
    logger.info("Starting main application on port 5000 with Gunicorn")
    
    # Use Gunicorn to start the application
    cmd = ["gunicorn", "--bind", "0.0.0.0:5000", "--reuse-port", "--reload", "main:app"]
    
    # Start as a subprocess
    process = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        universal_newlines=True,
        bufsize=1
    )
    
    # Log process output in a separate thread
    def log_output():
        for line in process.stdout:
            logger.info(f"GUNICORN: {line.strip()}")
    
    thread = threading.Thread(target=log_output, daemon=True)
    thread.start()
    
    return process

def wait_for_port(port, max_wait=30):
    """Wait for port to become available"""
    logger.info(f"Waiting for port {port} to become available...")
    for i in range(max_wait):
        try:
            with urllib.request.urlopen(f'http://localhost:{port}/health_check') as response:
                if response.status == 200:
                    logger.info(f"Port {port} is available")
                    return True
        except Exception as e:
            if i == 0 or i == max_wait - 1:
                logger.info(f"Port {port} not available yet ({i+1}/{max_wait}): {str(e)}")
            time.sleep(1)
    
    logger.error(f"Port {port} did not become available after {max_wait} seconds")
    return False

def run_proxy_server():
    """Run a proxy server on port 8080 that forwards to port 5000"""
    class ProxyHandler(http.server.BaseHTTPRequestHandler):
        def do_GET(self):
            self.proxy_request('GET')

        def do_POST(self):
            self.proxy_request('POST')

        def do_PUT(self):
            self.proxy_request('PUT')

        def do_DELETE(self):
            self.proxy_request('DELETE')
            
        def do_HEAD(self):
            self.proxy_request('HEAD')

        def proxy_request(self, method):
            try:
                # Create URL for the proxied server
                url = f'http://localhost:5000{self.path}'
                
                # Parse headers from the original request
                headers = {}
                for header in self.headers:
                    headers[header] = self.headers[header]

                # Read request body for POST/PUT requests
                content_length = int(self.headers.get('Content-Length', 0))
                body = self.rfile.read(content_length) if content_length > 0 else None

                # Create and send the request
                req = urllib.request.Request(
                    url, 
                    data=body,
                    headers=headers, 
                    method=method
                )

                # Get the response
                with urllib.request.urlopen(req) as response:
                    # Set response code
                    self.send_response(response.status)
                    
                    # Set response headers
                    for header in response.headers:
                        if header.lower() != 'transfer-encoding':  # Skip chunked encoding
                            self.send_header(header, response.headers[header])
                    self.end_headers()
                    
                    # Send response body (skip for HEAD)
                    if method != 'HEAD':
                        self.wfile.write(response.read())

            except Exception as e:
                logger.error(f"Error proxying request: {str(e)}")
                # Send error response
                self.send_response(500)
                self.send_header('Content-type', 'text/plain')
                self.end_headers()
                self.wfile.write(f"Proxy error: {str(e)}".encode('utf-8'))

        def log_message(self, format, *args):
            """Override the default logging to use our logger"""
            logger.info(f"8080: {self.client_address[0]} - {format % args}")

    # Create server
    logger.info("Starting proxy server on port 8080")
    server = socketserver.ThreadingTCPServer(('0.0.0.0', 8080), ProxyHandler)
    server.daemon_threads = True

    return server

def main():
    """Start the application with dual port binding"""
    try:
        # Start the main application
        app_process = start_main_application()
        
        # Wait for the main application to be ready
        if wait_for_port(5000):
            # Start the proxy server
            server = run_proxy_server()
            
            # Start the proxy server in a new thread
            proxy_thread = threading.Thread(target=server.serve_forever)
            proxy_thread.daemon = True
            proxy_thread.start()
            
            logger.info("Server is ready and listening on ports 5000 and 8080")
            print("Server is ready and listening on ports 5000 and 8080")
            
            # Wait for the main application to exit
            app_process.wait()
        else:
            logger.error("Main application did not start properly")
            sys.exit(1)
    
    except KeyboardInterrupt:
        logger.info("Shutdown requested")
    finally:
        logger.info("Shutting down")
        
        # Kill the main application if it's still running
        if 'app_process' in locals() and app_process.poll() is None:
            logger.info("Terminating main application")
            app_process.terminate()

def signal_handler(sig, frame):
    """Handle signals gracefully"""
    logger.info(f"Received signal {sig}. Shutting down.")
    sys.exit(0)

if __name__ == "__main__":
    # Register signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Start the application
    main()