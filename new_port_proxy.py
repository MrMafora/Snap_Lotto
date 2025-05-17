#!/usr/bin/env python3
import http.server
import socketserver
import urllib.request
import urllib.error
import sys
import os

# Port configuration
LISTEN_PORT = 8080
TARGET_PORT = 5000

class ProxyHandler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        self.proxy_request('GET')
        
    def do_POST(self):
        self.proxy_request('POST')
        
    def do_HEAD(self):
        self.proxy_request('HEAD')
        
    def proxy_request(self, method):
        target_url = f"http://localhost:{TARGET_PORT}{self.path}"
        print(f"Forwarding {method} request to {target_url}")
        
        try:
            # Get the original request body for POST
            content_length = int(self.headers.get('Content-Length', 0))
            body = self.rfile.read(content_length) if content_length > 0 else None
            
            # Create the request with the same headers and body
            req = urllib.request.Request(target_url, data=body, method=method)
            
            # Copy all headers from the original request
            for header, value in self.headers.items():
                if header.lower() not in ('host', 'content-length'):
                    req.add_header(header, value)
                    
            # Forward the request to the target server
            try:
                response = urllib.request.urlopen(req)
                
                # Set the response status code
                self.send_response(response.status)
                
                # Forward the response headers
                for header, value in response.getheaders():
                    self.send_header(header, value)
                self.end_headers()
                
                # Forward the response body
                if method != 'HEAD':
                    self.wfile.write(response.read())
                    
            except urllib.error.HTTPError as e:
                self.send_response(e.code)
                
                # Forward the error response headers
                for header, value in e.headers.items():
                    self.send_header(header, value)
                self.end_headers()
                
                # Forward the error response body
                if method != 'HEAD':
                    self.wfile.write(e.read())
                    
        except Exception as e:
            print(f"Error: {e}")
            self.send_response(500)
            self.end_headers()
            if method != 'HEAD':
                self.wfile.write(f"Proxy error: {str(e)}".encode('utf-8'))
    
    def log_message(self, format, *args):
        """Log messages to stderr"""
        sys.stderr.write("%s - - [%s] %s\n" %
                         (self.client_address[0],
                          self.log_date_time_string(),
                          format % args))

if __name__ == "__main__":
    print(f"Starting proxy server on port {LISTEN_PORT} forwarding to port {TARGET_PORT}...")
    
    # Create the server
    try:
        with socketserver.TCPServer(("", LISTEN_PORT), ProxyHandler) as httpd:
            print(f"Proxy server running at http://localhost:{LISTEN_PORT}/")
            # Write PID to file for easier management
            with open("proxy.pid", "w") as f:
                f.write(str(os.getpid()))
            # Start serving requests
            httpd.serve_forever()
    except KeyboardInterrupt:
        print("Proxy server stopped by user")
    except Exception as e:
        print(f"Error starting proxy server: {str(e)}")
        sys.exit(1)