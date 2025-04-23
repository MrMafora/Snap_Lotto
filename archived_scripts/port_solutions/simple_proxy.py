#!/usr/bin/env python3
"""
Very simple HTTP proxy for port forwarding.
Forwards all requests from port 8080 to port 5000.
"""

import http.server
import socketserver
import urllib.request
import urllib.error
import sys
import os
from urllib.parse import urljoin

# Configuration
SOURCE_PORT = 8080
TARGET_PORT = 5000
TARGET_SERVER = f"http://localhost:{TARGET_PORT}"


class SimpleProxyHandler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        """Handle GET requests by forwarding them to the target server."""
        self.proxy_request('GET')
        
    def do_POST(self):
        """Handle POST requests by forwarding them to the target server."""
        self.proxy_request('POST')
        
    def do_HEAD(self):
        """Handle HEAD requests by forwarding them to the target server."""
        self.proxy_request('HEAD')
    
    def proxy_request(self, method):
        """Forward any request to the target server."""
        target_url = urljoin(TARGET_SERVER, self.path)
        print(f"Forwarding {method} request to {target_url}")
        
        try:
            # Read request body for POST requests
            content_length = int(self.headers.get('Content-Length', 0))
            body = self.rfile.read(content_length) if content_length > 0 else None
            
            # Create request
            req = urllib.request.Request(
                url=target_url,
                data=body,
                method=method
            )
            
            # Copy headers
            for header in self.headers:
                if header.lower() not in ('host', 'content-length'):
                    req.add_header(header, self.headers[header])
            
            # Send request to target server
            try:
                with urllib.request.urlopen(req) as response:
                    # Copy response status and headers
                    self.send_response(response.status)
                    for header in response.headers:
                        self.send_header(header, response.headers[header])
                    self.end_headers()
                    
                    # Copy response body (except for HEAD requests)
                    if method != 'HEAD':
                        self.wfile.write(response.read())
                        
            except urllib.error.HTTPError as e:
                self.send_response(e.code)
                for header in e.headers:
                    self.send_header(header, e.headers[header])
                self.end_headers()
                
                if method != 'HEAD':
                    self.wfile.write(e.read())
                    
        except Exception as e:
            print(f"Error: {e}")
            self.send_response(500)
            self.end_headers()
            self.wfile.write(f"Proxy error: {e}".encode())
            
    def log_message(self, format, *args):
        """Override to provide better logging."""
        message = f"{self.client_address[0]} - {format % args}"
        print(message)


def run_proxy_server():
    """Run the proxy server."""
    server_address = ('', SOURCE_PORT)
    httpd = socketserver.ThreadingTCPServer(server_address, SimpleProxyHandler)
    print(f"Starting proxy server on port {SOURCE_PORT}, forwarding to {TARGET_SERVER}")
    
    # Write PID to file for easier management
    with open("proxy.pid", "w") as f:
        f.write(str(os.getpid()))
        
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("Stopping proxy server")
        httpd.server_close()


if __name__ == "__main__":
    run_proxy_server()