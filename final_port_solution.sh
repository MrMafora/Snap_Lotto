#!/bin/bash

# FINAL PORT SOLUTION FOR REPLIT
# This script handles starting the application on both port 5000 and 8080

echo "Starting port 8080 server..."
python -c "
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
        pass

try:
    server = socketserver.TCPServer(('0.0.0.0', 8080), RedirectHandler)
    server_thread = threading.Thread(target=server.serve_forever)
    server_thread.daemon = True
    server_thread.start()
    print('Port 8080 server started and redirecting to port 5000')
except Exception as e:
    print(f'Error starting port 8080 server: {e}')
    sys.exit(1)
" &

# Give the port 8080 server time to start
sleep 2

# Now start the main application
echo "Starting main application on port 5000..."
gunicorn --bind 0.0.0.0:5000 --reuse-port --reload main:app