#!/usr/bin/env python3
"""
Replit Proxy - A Simplified HTTP Proxy for Replit
Forwards all requests from port 8080 to port 5000
"""
import os
import sys
import http.server
import socketserver
import urllib.request
import urllib.error
import logging
import signal
import time
import threading

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("replit_proxy.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('replit_proxy')

# Path for the PID file
PID_FILE = 'replit_proxy.pid'

def create_pid_file():
    """Create a PID file for the proxy process"""
    with open(PID_FILE, 'w') as f:
        f.write(str(os.getpid()))
    logger.info(f"PID file created at {PID_FILE} with PID {os.getpid()}")

def remove_pid_file():
    """Remove the PID file on exit"""
    try:
        if os.path.exists(PID_FILE):
            os.remove(PID_FILE)
            logger.info(f"PID file {PID_FILE} removed")
    except Exception as e:
        logger.error(f"Failed to remove PID file: {e}")

class ProxyHandler(http.server.BaseHTTPRequestHandler):
    """HTTP handler that forwards requests to the destination server"""
    
    def do_GET(self):
        self._forward_request('GET')
        
    def do_POST(self):
        self._forward_request('POST')
        
    def do_HEAD(self):
        self._forward_request('HEAD')
        
    def do_PUT(self):
        self._forward_request('PUT')
        
    def do_DELETE(self):
        self._forward_request('DELETE')
        
    def do_OPTIONS(self):
        self._forward_request('OPTIONS')
        
    def do_PATCH(self):
        self._forward_request('PATCH')
    
    def _forward_request(self, method):
        """Common method to forward any HTTP request"""
        target_url = f'http://localhost:5000{self.path}'
        
        try:
            # Get the request body if any
            content_length = int(self.headers.get('Content-Length', 0))
            body = self.rfile.read(content_length) if content_length > 0 else None
            
            # Forward the request to port 5000
            request = urllib.request.Request(
                url=target_url,
                data=body,
                method=method
            )
            
            # Copy request headers
            for header, value in self.headers.items():
                if header.lower() not in ('host', 'content-length'):
                    request.add_header(header, value)
            
            # Send the request
            with urllib.request.urlopen(request, timeout=30) as response:
                # Send the response status code
                self.send_response(response.status)
                
                # Send the response headers
                for header, value in response.getheaders():
                    # Avoid issues with chunked encoding
                    if header.lower() != 'transfer-encoding':
                        self.send_header(header, value)
                
                self.end_headers()
                
                # Send the response body for non-HEAD requests
                if method != 'HEAD':
                    self.wfile.write(response.read())
        
        except Exception as e:
            logger.error(f"Error forwarding request to {target_url}: {e}")
            self.send_response(502)
            self.send_header('Content-Type', 'text/html; charset=utf-8')
            self.end_headers()
            
            # Send an error page
            error_message = f"""
            <html>
            <head><title>Proxy Error</title></head>
            <body>
                <h1>Proxy Error</h1>
                <p>Error: {str(e)}</p>
                <p>The application may be starting up. Please try again in a moment.</p>
            </body>
            </html>
            """
            self.wfile.write(error_message.encode('utf-8'))
    
    def log_message(self, format, *args):
        """Override the default logging to use our logger"""
        logger.info("%s - %s", self.address_string(), format % args)

def wait_for_destination():
    """Wait for the destination server to start"""
    max_attempts = 30
    attempt = 0
    
    while attempt < max_attempts:
        try:
            with urllib.request.urlopen('http://localhost:5000/health_port_check', timeout=1) as response:
                if response.status == 200:
                    logger.info("Destination server is ready")
                    return True
        except Exception:
            pass
        
        attempt += 1
        logger.info(f"Waiting for destination server... ({attempt}/{max_attempts})")
        time.sleep(1)
    
    logger.warning("Destination server not responding after maximum attempts")
    return False

def signal_handler(sig, frame):
    """Handle termination signals"""
    logger.info(f"Received signal {sig}, shutting down")
    remove_pid_file()
    sys.exit(0)

def start_proxy_server():
    """Start the HTTP proxy server"""
    
    # Register signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Create PID file
    create_pid_file()
    
    # Wait for the destination server to start
    wait_for_destination()
    
    # Configure server
    socketserver.TCPServer.allow_reuse_address = True
    
    try:
        # Use ThreadingTCPServer for better performance
        with socketserver.ThreadingTCPServer(('0.0.0.0', 8080), ProxyHandler) as httpd:
            logger.info('Starting proxy server on port 8080 forwarding to port 5000')
            # Run the server until interrupted
            httpd.serve_forever()
    except Exception as e:
        logger.error(f"Error starting proxy server: {e}")
        return 1
    finally:
        remove_pid_file()
    
    return 0

if __name__ == '__main__':
    sys.exit(start_proxy_server())