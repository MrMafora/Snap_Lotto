#!/usr/bin/env python3
"""
Direct port proxy that runs completely separately from the main application
"""
import sys
import http.server
import socketserver
import urllib.request
import urllib.error
import time

SOURCE_PORT = 8080
DESTINATION_PORT = 5000
HOSTNAME = "0.0.0.0"

def print_log(message):
    """Print log message to stderr"""
    print(f"[PORT PROXY] {message}", file=sys.stderr)

class ProxyHandler(http.server.BaseHTTPRequestHandler):
    """Handler that forwards all requests to the destination port"""
    def do_GET(self):
        self._forward_request("GET")
    
    def do_POST(self):
        content_length = int(self.headers.get('Content-Length', 0))
        body = self.rfile.read(content_length) if content_length > 0 else None
        self._forward_request("POST", body)
    
    def do_PUT(self):
        content_length = int(self.headers.get('Content-Length', 0))
        body = self.rfile.read(content_length) if content_length > 0 else None
        self._forward_request("PUT", body)
    
    def do_DELETE(self):
        self._forward_request("DELETE")
    
    def do_OPTIONS(self):
        self._forward_request("OPTIONS")
    
    def _forward_request(self, method, body=None):
        """Forward a request to the destination port"""
        destination_url = f"http://localhost:{DESTINATION_PORT}{self.path}"
        
        try:
            # Create request
            req = urllib.request.Request(
                destination_url,
                data=body,
                headers={k: v for k, v in self.headers.items() if k.lower() != 'host'},
                method=method
            )
            
            # Send request
            with urllib.request.urlopen(req) as response:
                # Copy status code
                self.send_response(response.status)
                
                # Copy headers
                for header, value in response.getheaders():
                    if header.lower() not in ('transfer-encoding', 'content-length'):
                        self.send_header(header, value)
                
                # Send response
                self.end_headers()
                self.wfile.write(response.read())
                
        except urllib.error.HTTPError as e:
            # Forward HTTP errors
            self.send_response(e.code)
            for header, value in e.headers.items():
                if header.lower() not in ('transfer-encoding', 'content-length'):
                    self.send_header(header, value)
            self.end_headers()
            self.wfile.write(e.read())
            
        except Exception as e:
            # Log the error and return a 502 Bad Gateway
            print_log(f"Error forwarding request: {e}")
            self.send_response(502)
            self.send_header('Content-Type', 'text/plain')
            self.end_headers()
            self.wfile.write(f"Error forwarding request: {e}".encode())
    
    def log_message(self, format, *args):
        """Override default logging"""
        print_log(f"{self.client_address[0]} - {args[0]}")

def wait_for_destination():
    """Wait for the destination server to become available"""
    print_log(f"Waiting for destination server at port {DESTINATION_PORT}...")
    max_attempts = 30
    attempt = 0
    
    while attempt < max_attempts:
        try:
            with urllib.request.urlopen(f"http://localhost:{DESTINATION_PORT}/health_port_check") as response:
                if response.status == 200:
                    print_log(f"Destination server is ready on port {DESTINATION_PORT}")
                    return True
        except Exception:
            pass
            
        attempt += 1
        time.sleep(1)
        
        # Print progress every 5 seconds
        if attempt % 5 == 0:
            print_log(f"Still waiting for destination server... ({attempt}/{max_attempts})")
    
    print_log(f"Destination server did not become available after {max_attempts} attempts")
    return False

def run_proxy():
    """Run the proxy server"""
    # Wait for the destination server
    wait_for_destination()
    
    print_log(f"Starting proxy server on port {SOURCE_PORT}, forwarding to port {DESTINATION_PORT}")
    
    # Create and start the server
    with socketserver.TCPServer((HOSTNAME, SOURCE_PORT), ProxyHandler) as httpd:
        try:
            print_log(f"Proxy server is running at http://{HOSTNAME}:{SOURCE_PORT}/")
            httpd.serve_forever()
        except KeyboardInterrupt:
            print_log("Stopping proxy server")
            httpd.server_close()

if __name__ == "__main__":
    # Try to run the proxy
    try:
        run_proxy()
    except Exception as e:
        print_log(f"Error starting proxy: {e}")
        sys.exit(1)