"""
SIMPLE PORT 8080 SERVER

A minimal server that binds to port 8080 and redirects to port 5000.
This script uses only standard library modules and requires no dependencies.
"""
import http.server
import socketserver
import threading
import time
import sys

class RedirectHandler(http.server.BaseHTTPRequestHandler):
    """HTTP handler that redirects requests to port 5000"""
    def redirect_request(self):
        """Send a redirect to port 5000"""
        self.send_response(302)
        host = self.headers.get('Host', '')
        redirect_host = host.replace(':8080', ':5000') if ':8080' in host else host
        self.send_header('Location', f'https://{redirect_host}{self.path}')
        self.end_headers()
    
    do_GET = do_POST = do_PUT = do_DELETE = do_HEAD = do_OPTIONS = redirect_request
    
    def log_message(self, format, *args):
        """Minimize logging"""
        pass

print("Starting server on port 8080...")
try:
    # Create and start the server
    server = socketserver.TCPServer(("0.0.0.0", 8080), RedirectHandler)
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