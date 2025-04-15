#!/bin/bash
# Combined solution for port binding
# Starts both a gunicorn server on port 5000 and our main application on port 8080

# Ensure this script always runs from the project root directory
cd "$(dirname "$0")"

# Kill any existing processes on port 8080
if netstat -tuln | grep -q ":8080 "; then
    echo "Port 8080 is in use, attempting to free it..."
    lsof -i :8080 | tail -n +2 | awk '{print $2}' | xargs -r kill
fi

# Start the main gunicorn server on port 5000
echo "Starting main application on port 5000 with gunicorn..."
gunicorn --bind 0.0.0.0:5000 --reuse-port --reload main:app &
GUNICORN_PID=$!

# Wait for a moment to ensure gunicorn is started
sleep 2

# Start a simple port 8080 server that delegates to port 5000
echo "Starting port 8080 proxy..."
{
cat << 'EOF' > /tmp/port8080_proxy.py
#!/usr/bin/env python3
import http.server
import socketserver
import urllib.request
import threading
import time

# Define handler
class ProxyHandler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        self.proxy_request('GET')
    
    def do_POST(self):
        self.proxy_request('POST')
    
    def do_PUT(self):
        self.proxy_request('PUT')
    
    def do_DELETE(self):
        self.proxy_request('DELETE')
    
    def proxy_request(self, method):
        try:
            url = f'http://localhost:5000{self.path}'
            
            # Parse headers from the original request
            headers = {}
            for header in self.headers:
                headers[header] = self.headers[header]
            
            # Read request body for POST/PUT requests
            content_length = int(self.headers.get('Content-Length', 0))
            body = self.rfile.read(content_length) if content_length > 0 else None
            
            # Create and send the request
            req = urllib.request.Request(
                url, 
                data=body,
                headers=headers, 
                method=method
            )
            
            # Get the response
            with urllib.request.urlopen(req) as response:
                # Set response code
                self.send_response(response.status)
                
                # Set response headers
                for header in response.headers:
                    if header.lower() != 'transfer-encoding':  # Skip chunked encoding
                        self.send_header(header, response.headers[header])
                self.end_headers()
                
                # Send response body
                self.wfile.write(response.read())
        
        except Exception as e:
            # Send error response
            self.send_response(500)
            self.send_header('Content-type', 'text/plain')
            self.end_headers()
            self.wfile.write(f"Proxy error: {str(e)}".encode('utf-8'))
    
# Run server
httpd = socketserver.ThreadingTCPServer(('0.0.0.0', 8080), ProxyHandler)
print("Server is ready and listening on ports 5000 and 8080")
httpd.serve_forever()
EOF

python /tmp/port8080_proxy.py &
PROXY_PID=$!

# Monitor both processes
echo "Server is ready and listening on ports 5000 and 8080"

# Trap Ctrl+C to kill both servers
trap "kill $GUNICORN_PID $PROXY_PID 2>/dev/null; exit" INT TERM

# Keep the script running
wait $GUNICORN_PID
}