#!/usr/bin/env python3
"""
Final port binding solution for Replit.
Integrates directly with the main.py file to add port 8080 binding.
This simplifies the solution by working within the same process.
"""
import http.server
import logging
import os
import signal
import socketserver
import sys
import threading
import time
import urllib.error
import urllib.parse
import urllib.request

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('final_port_solution')

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

        def proxy_request(self, method):
            try:
                # Create URL for the proxied server
                url = f'http://localhost:5000{self.path}'
                logger.debug(f"Proxying {method} request to {url}")

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
                        self.send_header(header, response.headers[header])
                    self.end_headers()
                    
                    # Send response body
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
            logger.info(f"{self.client_address[0]} - {format % args}")

    # Create server
    logger.info(f"Starting proxy server on port 8080")
    server = socketserver.ThreadingTCPServer(('0.0.0.0', 8080), ProxyHandler)
    server.daemon_threads = True

    # Run server in thread
    server_thread = threading.Thread(target=server.serve_forever)
    server_thread.daemon = True
    server_thread.start()

    return server

def wait_for_port(port, max_wait=30):
    """Wait for port to become available"""
    for i in range(max_wait):
        try:
            with urllib.request.urlopen(f'http://localhost:{port}/health_check') as response:
                if response.status == 200:
                    logger.info(f"Port {port} is available")
                    return True
        except:
            logger.debug(f"Port {port} not available yet, waiting ({i+1}/{max_wait})...")
            time.sleep(1)
    
    logger.error(f"Port {port} did not become available after {max_wait} seconds")
    return False

def start_proxy():
    """Start the proxy server in a new thread"""
    # Wait for main application to be ready on port 5000
    if wait_for_port(5000):
        # Start the proxy server
        server = run_proxy_server()
        logger.info("Server is ready and listening on ports 5000 and 8080")
        return server
    else:
        logger.error("Failed to start proxy server: Main application not available on port 5000")
        return None

# Signal handler
def signal_handler(sig, frame):
    logger.info(f"Received signal {sig}. Shutting down.")
    sys.exit(0)

if __name__ == "__main__":
    # Register signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Start the proxy
    server = start_proxy()
    
    if server:
        try:
            # Keep the main thread alive
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            logger.info("Shutdown requested")
        finally:
            if server:
                logger.info("Shutting down server")
                server.shutdown()
    else:
        logger.error("Failed to start proxy server")
        sys.exit(1)