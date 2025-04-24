#!/bin/bash
# Script to start the application on port 8080 for Replit
# This script starts the main application on port 5000 and a proxy on port 8080

# Kill any existing processes that might be using our ports
pkill -f gunicorn || true
pkill -f "python.*proxy" || true
pkill -f "python.*dual_port" || true

# Create a log directory if it doesn't exist
mkdir -p logs

# Start the main application on port 5000 in the background
echo "Starting main application on port 5000..."
gunicorn --bind 0.0.0.0:5000 --reuse-port --reload main:app > logs/gunicorn.log 2>&1 &
MAIN_PID=$!
echo "Main application started with PID $MAIN_PID"

# Wait for the application to start (3 seconds should be enough)
echo "Waiting for the application to start..."
sleep 3

# Start the proxy server to forward requests from port 8080 to port 5000
echo "Starting proxy server on port 8080..."
python3 -c "
import http.server
import socketserver
import urllib.request
import urllib.error
import logging
import threading
import time
import signal
import sys

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    filename='logs/proxy.log',
    filemode='a'
)
logger = logging.getLogger('proxy')

# Also log to console
console = logging.StreamHandler()
console.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
console.setFormatter(formatter)
logger.addHandler(console)

# Handle signals
def handle_signal(signum, frame):
    logger.info(f'Received signal {signum}, shutting down proxy...')
    sys.exit(0)

signal.signal(signal.SIGINT, handle_signal)
signal.signal(signal.SIGTERM, handle_signal)

class ProxyHandler(http.server.BaseHTTPRequestHandler):
    def do_GET(self): self._proxy_request('GET')
    def do_POST(self): self._proxy_request('POST')
    def do_HEAD(self): self._proxy_request('HEAD')
    def do_PUT(self): self._proxy_request('PUT')
    def do_DELETE(self): self._proxy_request('DELETE')
    def do_OPTIONS(self): self._proxy_request('OPTIONS')
    def do_PATCH(self): self._proxy_request('PATCH')
    
    def _proxy_request(self, method):
        \"\"\"Forward request to port 5000\"\"\"
        target_url = f'http://localhost:5000{self.path}'
        logger.info(f'Forwarding {method} request to {target_url}')
        
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
            
            # Set content type if it exists
            content_type = self.headers.get('Content-Type')
            if content_type and body:
                req.add_header('Content-Type', content_type)
            
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
            logger.error(f'Proxy error: {str(e)}')
            self.send_response(502)
            self.send_header('Content-Type', 'text/html; charset=utf-8')
            self.end_headers()
            
            error_message = f'''
            <html>
            <head><title>Proxy Error</title></head>
            <body>
                <h1>Proxy Error</h1>
                <p>The proxy server could not connect to the application server.</p>
                <p>Error: {str(e)}</p>
            </body>
            </html>
            '''
            self.wfile.write(error_message.encode('utf-8'))
    
    def log_message(self, format, *args):
        \"\"\"Override to use our logger\"\"\"
        logger.info('%s - %s', self.address_string(), format % args)

# Use ThreadingTCPServer for better performance
socketserver.ThreadingTCPServer.allow_reuse_address = True
httpd = socketserver.ThreadingTCPServer(('', 8080), ProxyHandler)

logger.info('Starting proxy server on port 8080 → 5000')
httpd.serve_forever()
" > logs/proxy_stderr.log 2>&1 &
PROXY_PID=$!
echo "Proxy server started with PID $PROXY_PID"

# Wait for the proxy server to start (2 seconds should be enough)
echo "Waiting for the proxy server to start..."
sleep 2

# Check if the proxy server is running
if ! ps -p $PROXY_PID > /dev/null; then
    echo "Error: Proxy server failed to start!"
    cat logs/proxy_stderr.log
    exit 1
fi

echo "Application is now running on port 8080 (via proxy) and port 5000 (directly)"
echo "Main application PID: $MAIN_PID"
echo "Proxy server PID: $PROXY_PID"

# Create a PID file for cleanup
echo "$MAIN_PID $PROXY_PID" > .app_pids

# Keep the script running until it's killed
while true; do
    # Check if either process has died
    if ! ps -p $MAIN_PID > /dev/null; then
        echo "Error: Main application process died!"
        exit 1
    fi
    if ! ps -p $PROXY_PID > /dev/null; then
        echo "Error: Proxy server process died!"
        exit 1
    fi
    
    # Sleep for a bit to avoid consuming too much CPU
    sleep 5
done