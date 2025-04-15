import http.server
import socketserver
import threading
import time
import sys

class RedirectHandler(http.server.BaseHTTPRequestHandler):
    def redirect_request(self):
        self.send_response(302)
        host = self.headers.get('Host', '')
        redirect_host = host.replace(':8080', ':5000') if ':8080' in host else host
        self.send_header('Location', f'https://{redirect_host}{self.path}')
        self.end_headers()
    
    do_GET = do_POST = do_PUT = do_DELETE = do_HEAD = do_OPTIONS = redirect_request
    
    def log_message(self, format, *args):
        print(f"8080 Server: {format % args}")

try:
    print('Starting server on port 8080...')
    server = socketserver.TCPServer(('0.0.0.0', 8080), RedirectHandler)
    print('Port 8080 server started and redirecting to port 5000')
    server.serve_forever()
except Exception as e:
    print(f'Error starting port 8080 server: {e}')
    sys.exit(1)
