#!/usr/bin/env python3
import socketserver
import http.server
import urllib.request

# Configuration
SOURCE_PORT = 8080
TARGET_PORT = 5000

class ProxyHandler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        self.proxy_request("GET")

    def do_POST(self):
        self.proxy_request("POST")

    def do_HEAD(self):
        self.proxy_request("HEAD")

    def proxy_request(self, method):
        target_url = f"http://localhost:{TARGET_PORT}{self.path}"
        print(f"Forwarding {method} request to {target_url}")

        try:
            # Get request body for POST
            content_length = int(self.headers.get('Content-Length', 0))
            body = self.rfile.read(content_length) if content_length > 0 else None

            # Create request
            req = urllib.request.Request(target_url, data=body, method=method)
            
            # Copy headers
            for header, value in self.headers.items():
                if header.lower() not in ('host', 'content-length'):
                    req.add_header(header, value)

            # Forward request
            response = urllib.request.urlopen(req)
            
            # Set response status
            self.send_response(response.status)
            
            # Forward response headers
            for header, value in response.getheaders():
                self.send_header(header, value)
            self.end_headers()
            
            # Forward response body
            if method != 'HEAD':
                self.wfile.write(response.read())
                
        except Exception as e:
            print(f"Error: {e}")
            self.send_response(500)
            self.end_headers()
            self.wfile.write(f"Proxy error: {str(e)}".encode('utf-8'))

# Start the proxy server
print(f"Starting proxy server on port {SOURCE_PORT} → {TARGET_PORT}")
httpd = socketserver.TCPServer(("", SOURCE_PORT), ProxyHandler)
print("Proxy is running...")
httpd.serve_forever()