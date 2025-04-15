"""
ABSOLUTE MINIMAL PORT 8080 BINDER FOR REPLIT

This is a completely standalone script with NO imports beyond the standard library
that needs to be running alongside the main application to ensure visibility.
"""
import http.server
import socketserver
import threading
import time
import sys
import os

class RedirectHandler(http.server.BaseHTTPRequestHandler):
    """Handler that redirects all requests to port 5000"""
    def redirect_request(self):
        """Send a redirect to the same path on port 5000"""
        try:
            self.send_response(302)
            
            # Get host from request headers or use default
            host = self.headers.get('Host', '')
            
            # Replace port 8080 with 5000 in host if present
            redirect_host = host.replace(':8080', ':5000') if ':8080' in host else host
            
            # Get path from request
            path = self.path
            
            # Build redirect URL
            redirect_url = f"https://{redirect_host}{path}"
            
            # Set redirect location header
            self.send_header('Location', redirect_url)
            self.end_headers()
        except Exception as e:
            print(f"Error in redirect: {e}")
    
    def do_GET(self): self.redirect_request()
    def do_POST(self): self.redirect_request()
    def do_PUT(self): self.redirect_request()
    def do_DELETE(self): self.redirect_request()
    def do_HEAD(self): self.redirect_request() 
    def do_OPTIONS(self): self.redirect_request()
    
    def log_message(self, format, *args):
        """Override to minimize logging"""
        return

def is_port_in_use(port):
    """Check if the specified port is already in use"""
    import socket
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex(('localhost', port)) == 0

def start_server():
    """Start the HTTP server on port 8080"""
    # Check if port 8080 is already in use
    if is_port_in_use(8080):
        print("Port 8080 is already in use")
        return
    
    try:
        # Create and start the server
        server = socketserver.TCPServer(("0.0.0.0", 8080), RedirectHandler)
        server.daemon_threads = True
        server_thread = threading.Thread(target=server.serve_forever)
        server_thread.daemon = True
        server_thread.start()
        print("Server started on port 8080 and redirecting to port 5000")
        
        # Keep the main thread alive
        while True:
            time.sleep(60)
    except KeyboardInterrupt:
        print("Shutting down...")
        sys.exit(0)
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    start_server()