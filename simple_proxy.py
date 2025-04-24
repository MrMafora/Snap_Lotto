#!/usr/bin/env python3
"""
Enhanced HTTP proxy server for Replit environment
Forwards all requests from port 8080 to the internally running application on port 5000
Handles all HTTP methods and includes improved error handling
"""
import socketserver
import http.server
import urllib.request
import urllib.error
import socket
import sys
import time
import logging
import os
import signal

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('proxy_server')

# Configuration
SOURCE_PORT = 8080  # The port Replit expects
TARGET_PORT = 5000  # Flask's default port
MAX_RETRIES = 5     # Maximum number of retries to connect to target
RETRY_DELAY = 2     # Seconds to wait between retries

class ProxyHandler(http.server.BaseHTTPRequestHandler):
    """HTTP request handler that forwards all requests to the target server"""
    
    # Support all common HTTP methods
    def do_GET(self):
        self.proxy_request("GET")

    def do_POST(self):
        self.proxy_request("POST")

    def do_HEAD(self):
        self.proxy_request("HEAD")
        
    def do_PUT(self):
        self.proxy_request("PUT")
        
    def do_DELETE(self):
        self.proxy_request("DELETE")
        
    def do_OPTIONS(self):
        self.proxy_request("OPTIONS")
        
    def do_PATCH(self):
        self.proxy_request("PATCH")
    
    def log_message(self, format, *args):
        """Override the default logging to use our logger"""
        logger.info("%s - %s", self.address_string(), format % args)

    def proxy_request(self, method):
        """Forward the request to the target server"""
        target_url = f"http://127.0.0.1:{TARGET_PORT}{self.path}"
        logger.info(f"Forwarding {method} request to {target_url}")

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

            # Forward request with error handling and retries
            response = None
            retry_count = 0
            last_error = None
            
            while retry_count < MAX_RETRIES:
                try:
                    response = urllib.request.urlopen(req, timeout=10)
                    break
                except (urllib.error.URLError, socket.error) as e:
                    last_error = e
                    retry_count += 1
                    if retry_count < MAX_RETRIES:
                        logger.warning(f"Retry {retry_count}/{MAX_RETRIES}: {str(e)}")
                        time.sleep(RETRY_DELAY)
                    else:
                        logger.error(f"Max retries reached: {str(e)}")
            
            if response:
                # Set response status
                self.send_response(response.status)
                
                # Forward response headers
                for header, value in response.getheaders():
                    self.send_header(header, value)
                self.end_headers()
                
                # Forward response body for methods that expect it
                if method != 'HEAD':
                    self.wfile.write(response.read())
            else:
                raise last_error or Exception("Failed to connect to target server")
                
        except Exception as e:
            logger.error(f"Proxy error: {str(e)}")
            self.send_response(502)  # Bad Gateway
            self.send_header('Content-Type', 'text/html; charset=utf-8')
            self.end_headers()
            
            error_message = f"""
            <html>
            <head><title>Proxy Error</title></head>
            <body>
                <h1>Proxy Error</h1>
                <p>The proxy server could not connect to the application server.</p>
                <p>Error: {str(e)}</p>
                <p>This usually means the application is still starting up or has crashed.</p>
            </body>
            </html>
            """
            self.wfile.write(error_message.encode('utf-8'))

def wait_for_target():
    """Wait for the target application to be ready"""
    logger.info(f"Checking if target application is running on port {TARGET_PORT}...")
    retry_count = 0
    
    while retry_count < MAX_RETRIES:
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.settimeout(2)
                result = s.connect_ex(('127.0.0.1', TARGET_PORT))
                if result == 0:
                    # Try to make an HTTP request to confirm the app is responding
                    try:
                        response = urllib.request.urlopen(f"http://127.0.0.1:{TARGET_PORT}/", timeout=5)
                        if response.status in (200, 301, 302):
                            logger.info(f"Target application is running on port {TARGET_PORT}")
                            return True
                    except:
                        logger.warning(f"Port {TARGET_PORT} is open but not responding to HTTP yet")
                        
            retry_count += 1
            logger.info(f"Waiting for target application... ({retry_count}/{MAX_RETRIES})")
            time.sleep(RETRY_DELAY)
        except Exception as e:
            logger.error(f"Error checking target: {str(e)}")
            retry_count += 1
            time.sleep(RETRY_DELAY)
    
    logger.warning(f"Target application not ready after {MAX_RETRIES} attempts, starting proxy anyway")
    return False

def handle_signal(signum, frame):
    """Handle termination signals"""
    logger.info(f"Received signal {signum}. Shutting down proxy...")
    sys.exit(0)

def create_pid_file():
    """Create a PID file to track this proxy process"""
    pid = os.getpid()
    with open('proxy.pid', 'w') as f:
        f.write(str(pid))
    logger.info(f"Created PID file with process ID {pid}")

def start_proxy_server():
    """Start the HTTP proxy server"""
    # Set up signal handlers
    signal.signal(signal.SIGINT, handle_signal)
    signal.signal(signal.SIGTERM, handle_signal)
    
    # Create PID file
    create_pid_file()
    
    # Wait for target application
    wait_for_target()
    
    try:
        # Use ThreadingTCPServer for better performance with multiple connections
        socketserver.ThreadingTCPServer.allow_reuse_address = True
        httpd = socketserver.ThreadingTCPServer(("0.0.0.0", SOURCE_PORT), ProxyHandler)
        
        logger.info(f"Starting proxy server on port {SOURCE_PORT} → {TARGET_PORT}")
        logger.info("Proxy is running...")
        
        # Start the server
        httpd.serve_forever()
    except OSError as e:
        if e.errno == 98:  # Address already in use
            logger.error(f"Port {SOURCE_PORT} is already in use. The proxy may already be running.")
        else:
            logger.error(f"Failed to start proxy server: {str(e)}")
        sys.exit(1)
    except KeyboardInterrupt:
        logger.info("Proxy server stopped by user")
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    start_proxy_server()