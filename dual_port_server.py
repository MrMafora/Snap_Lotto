#!/usr/bin/env python3
"""
Dual port server that runs the main Flask application on port 5000
and also provides an HTTP server on port 8080 that forwards to port 5000.
"""
import threading
import time
import logging
import http.server
import socketserver
import urllib.request
import urllib.error
import os
import sys
from urllib.parse import urlparse

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('dual_port')

def start_port_proxy():
    """Start a proxy server on port 8080 that forwards to port 5000"""
    
    class ProxyHandler(http.server.BaseHTTPRequestHandler):
        def do_GET(self): self._proxy_request('GET')
        def do_POST(self): self._proxy_request('POST')
        def do_HEAD(self): self._proxy_request('HEAD')
        def do_PUT(self): self._proxy_request('PUT')
        def do_DELETE(self): self._proxy_request('DELETE')
        def do_OPTIONS(self): self._proxy_request('OPTIONS')
        def do_PATCH(self): self._proxy_request('PATCH')
        
        def _proxy_request(self, method):
            """Forward request to internal port 5000"""
            target_url = f'http://localhost:5000{self.path}'
            logger.info(f"Forwarding {method} request from port 8080 to {target_url}")
            
            try:
                # Get request body for methods that may have a body
                content_length = int(self.headers.get('Content-Length', 0))
                body = self.rfile.read(content_length) if content_length > 0 else None
                
                # Create request
                req = urllib.request.Request(target_url, data=body, method=method)
                
                # Copy all headers except those that might cause issues
                for header, value in self.headers.items():
                    if header.lower() not in ('host', 'content-length'):
                        req.add_header(header, value)
                
                # Forward request
                response = urllib.request.urlopen(req, timeout=30)
                
                # Set response status
                self.send_response(response.status)
                
                # Forward response headers
                for header, value in response.getheaders():
                    if header.lower() != 'transfer-encoding':  # Skip chunked encoding
                        self.send_header(header, value)
                self.end_headers()
                
                # Forward response body for methods that expect it
                if method != 'HEAD':
                    self.wfile.write(response.read())
            except Exception as e:
                logger.error(f"Proxy error: {str(e)}")
                self.send_response(502)
                self.send_header('Content-Type', 'text/html; charset=utf-8')
                self.end_headers()
                
                error_message = f"""
                <html>
                <head><title>Proxy Error</title></head>
                <body>
                    <h1>Proxy Error</h1>
                    <p>The proxy server could not complete your request.</p>
                    <p>Error: {str(e)}</p>
                    <p>Please try refreshing the page or contact support if the problem persists.</p>
                </body>
                </html>
                """
                self.wfile.write(error_message.encode('utf-8'))
        
        def log_message(self, format, *args):
            """Override to use our logger"""
            logger.info("%s - %s", self.address_string(), format % args)
    
    # Allow reuse of the socket address in case it's in TIME_WAIT state
    socketserver.TCPServer.allow_reuse_address = True
    
    # Create the HTTP server on port 8080
    try:
        with socketserver.ThreadingTCPServer(("", 8080), ProxyHandler) as httpd:
            logger.info("Port proxy server started on port 8080")
            httpd.serve_forever()
    except Exception as e:
        logger.error(f"Error starting port proxy: {e}")

# Start the proxy server in a background thread
proxy_thread = threading.Thread(target=start_port_proxy, daemon=True)
proxy_thread.start()
logger.info("Started proxy thread to forward requests from port 8080 to 5000")

# Log success message
logger.info("Dual port server successfully initialized")
logger.info("Application running on port 5000")
logger.info("Proxy running on port 8080")

# Keep the script alive
try:
    while True:
        time.sleep(1)
except KeyboardInterrupt:
    logger.info("Dual port server shutting down")
    sys.exit(0)