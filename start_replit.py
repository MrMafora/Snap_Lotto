"""
Replit-optimized starter script with socket prewarming.

This script:
1. Opens port 5000 immediately to satisfy Replit's detection requirement
2. Shows a "loading" page while the main application starts
3. Launches gunicorn on port 8080 (internal)
4. Proxies requests from port 5000 to the actual application
"""
import socket
import threading
import subprocess
import time
import os
import sys
import http.server
import socketserver
import urllib.request
from http.server import BaseHTTPRequestHandler
import urllib.error
import signal

# Configure ports
EXTERNAL_PORT = 5000  # Port Replit expects to be open
INTERNAL_PORT = 8080  # Port where the actual app will run

# Flag to track if the main app is ready
app_ready = False

def signal_handler(sig, frame):
    """Handle Ctrl+C gracefully"""
    print("Shutting down...")
    # Kill any running gunicorn processes
    os.system("pkill -f gunicorn || true")
    sys.exit(0)

# Set up signal handler
signal.signal(signal.SIGINT, signal_handler)

class ProxyHandler(BaseHTTPRequestHandler):
    """
    HTTP handler that either shows a loading page or proxies to the real app
    depending on whether the app is ready
    """
    def log_message(self, format, *args):
        """Silence default logging to reduce noise"""
        return
    
    def do_GET(self):
        """Handle GET requests"""
        global app_ready
        
        if not app_ready:
            # Check if the app is ready yet
            try:
                # Check if the internal app is responding
                urllib.request.urlopen(f"http://localhost:{INTERNAL_PORT}/", timeout=0.1)
                app_ready = True
            except (urllib.error.URLError, socket.timeout):
                # App still not ready, show loading page
                self.send_response(200)
                self.send_header('Content-type', 'text/html')
                self.end_headers()
                self.wfile.write(b"""
                <html>
                <head>
                    <title>Application Starting</title>
                    <style>
                        body { font-family: Arial, sans-serif; background-color: #f5f5f5; text-align: center; padding-top: 100px; }
                        .loader { border: 8px solid #f3f3f3; border-top: 8px solid #3498db; border-radius: 50%; width: 50px; height: 50px; animation: spin 1s linear infinite; margin: 0 auto; }
                        @keyframes spin { 0% { transform: rotate(0deg); } 100% { transform: rotate(360deg); } }
                        h1 { color: #333; }
                    </style>
                    <meta http-equiv="refresh" content="2">
                </head>
                <body>
                    <h1>Application is starting...</h1>
                    <p>This may take up to 30 seconds. Thank you for your patience.</p>
                    <div class="loader"></div>
                </body>
                </html>
                """)
                return
        
        # If we get here, either the app was ready or just became ready
        # Proxy the request to the real application
        try:
            # Forward the request to the internal port
            url = f"http://localhost:{INTERNAL_PORT}{self.path}"
            response = urllib.request.urlopen(url)
            
            # Send the response status code
            self.send_response(response.status)
            
            # Send all headers
            for header in response.getheaders():
                self.send_header(header[0], header[1])
            self.end_headers()
            
            # Send the response body
            self.wfile.write(response.read())
            
        except Exception as e:
            self.send_response(500)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            self.wfile.write(f"<h1>Error</h1><p>{str(e)}</p>".encode())

    def do_POST(self):
        """Handle POST requests (proxy them to the real app)"""
        global app_ready
        
        if not app_ready:
            self.send_response(503)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            self.wfile.write(b"<h1>Application is starting...</h1><p>Please try again shortly.</p>")
            return
            
        try:
            # Get the request body
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            
            # Forward the request to the internal port
            url = f"http://localhost:{INTERNAL_PORT}{self.path}"
            req = urllib.request.Request(url, data=post_data, method='POST')
            
            # Copy all headers
            for header in self.headers:
                if header.lower() not in ('content-length', 'host'):
                    req.add_header(header, self.headers[header])
            
            response = urllib.request.urlopen(req)
            
            # Send the response status code
            self.send_response(response.status)
            
            # Send all headers
            for header in response.getheaders():
                self.send_header(header[0], header[1])
            self.end_headers()
            
            # Send the response body
            self.wfile.write(response.read())
            
        except Exception as e:
            self.send_response(500)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            self.wfile.write(f"<h1>Error</h1><p>{str(e)}</p>".encode())

def start_proxy_server():
    """
    Start the proxy server on the external port.
    This is what Replit will detect.
    """
    server = socketserver.TCPServer(("0.0.0.0", EXTERNAL_PORT), ProxyHandler)
    print(f"Proxy server started on port {EXTERNAL_PORT}")
    sys.stdout.flush()
    server.serve_forever()

def start_main_app():
    """Start the actual Flask app on the internal port"""
    # Kill any existing processes to avoid conflicts
    os.system("pkill -f gunicorn || true")
    
    print(f"Starting main application on port {INTERNAL_PORT}...")
    sys.stdout.flush()
    
    # Start gunicorn on the internal port
    cmd = ["gunicorn", "--bind", f"0.0.0.0:{INTERNAL_PORT}", "main:app"]
    subprocess.Popen(cmd)

# Main execution
if __name__ == "__main__":
    # Start the main app in a separate thread
    app_thread = threading.Thread(target=start_main_app)
    app_thread.daemon = True
    app_thread.start()
    
    # Start the proxy server in the main thread
    try:
        start_proxy_server()
    except KeyboardInterrupt:
        signal_handler(None, None)