"""
Replit Port Integration Module

This module integrates with Replit's expected port (8080) while running the 
Flask application on its native port (5000).

Features:
- Automatically starts a port forwarding proxy when imported
- Handles threading to avoid blocking the main application
- Provides health check endpoints for both ports
"""

import threading
import logging
import time
import http.server
import socketserver
import urllib.request
import urllib.error
import os
import atexit

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("replit_port_integration")

# Constants
SOURCE_PORT = 8080  # Replit's expected port
DESTINATION_PORT = 5000  # Flask's default port

class ProxyHandler(http.server.BaseHTTPRequestHandler):
    """HTTP handler that forwards requests from port 8080 to port 5000"""
    
    def do_GET(self): self._forward_request('GET')
    def do_POST(self): self._forward_request('POST')
    def do_HEAD(self): self._forward_request('HEAD')
    def do_PUT(self): self._forward_request('PUT')
    def do_DELETE(self): self._forward_request('DELETE')
    def do_OPTIONS(self): self._forward_request('OPTIONS')
    def do_PATCH(self): self._forward_request('PATCH')
    
    def _forward_request(self, method):
        """Forward request to port 5000"""
        target_url = f'http://localhost:{DESTINATION_PORT}{self.path}'
        
        try:
            # Get request body if any
            content_length = int(self.headers.get('Content-Length', 0))
            body = self.rfile.read(content_length) if content_length > 0 else None
            
            # Create request
            req = urllib.request.Request(target_url, data=body, method=method)
            
            # Copy headers
            for header, value in self.headers.items():
                if header.lower() not in ('host', 'content-length'):
                    req.add_header(header, value)
            
            # Forward request
            with urllib.request.urlopen(req, timeout=30) as response:
                # Copy response status
                self.send_response(response.status)
                
                # Copy response headers
                for header, value in response.getheaders():
                    if header.lower() != 'transfer-encoding':
                        self.send_header(header, value)
                self.end_headers()
                
                # Copy response body
                if method != 'HEAD':
                    self.wfile.write(response.read())
                    
        except Exception as e:
            logger.error(f'Error forwarding request to {target_url}: {e}')
            self.send_response(502)
            self.send_header('Content-Type', 'text/html; charset=utf-8')
            self.end_headers()
            
            error_message = f"""
            <html>
            <head><title>Proxy Error</title></head>
            <body>
                <h1>Proxy Error</h1>
                <p>Error: {str(e)}</p>
                <p>The application may still be starting up. Please try again in a moment.</p>
            </body>
            </html>
            """
            self.wfile.write(error_message.encode('utf-8'))
    
    def log_message(self, format, *args):
        """Override to use our logger"""
        logger.info('%s - %s', self.address_string(), format % args)

# Global httpd server reference for shutdown
httpd = None

def shutdown_proxy():
    """Shutdown the proxy server if it's running"""
    global httpd
    if httpd:
        logger.info('Shutting down proxy server')
        httpd.shutdown()
        httpd = None

def run_proxy_server():
    """Run the proxy server in a separate thread"""
    global httpd
    
    # Register shutdown function
    atexit.register(shutdown_proxy)
    
    # Allow port reuse
    socketserver.TCPServer.allow_reuse_address = True
    
    while True:
        try:
            # Create and start the server
            httpd = socketserver.ThreadingTCPServer(('0.0.0.0', SOURCE_PORT), ProxyHandler)
            logger.info(f'Starting proxy server on port {SOURCE_PORT} forwarding to port {DESTINATION_PORT}')
            httpd.serve_forever()
        except OSError as e:
            if e.errno == 98:  # Address already in use
                logger.error(f"Port {SOURCE_PORT} is already in use. Waiting to retry...")
                time.sleep(5)
                continue
            else:
                logger.error(f"Socket error: {e}")
                break
        except Exception as e:
            logger.error(f'Error in proxy server: {e}')
            # Avoid rapid restarts on persistent errors
            time.sleep(5)
            continue

# Wait for Flask to be ready before starting proxy
def wait_for_flask():
    """Wait for Flask to be ready before starting the proxy"""
    max_attempts = 30
    for attempt in range(max_attempts):
        try:
            with urllib.request.urlopen(f'http://localhost:{DESTINATION_PORT}/health_port_check', timeout=1) as response:
                if response.status == 200:
                    logger.info(f"Flask application is ready on port {DESTINATION_PORT}")
                    return True
        except Exception:
            pass
        
        logger.info(f"Waiting for Flask to start... ({attempt+1}/{max_attempts})")
        time.sleep(1)
    
    logger.warning(f"Flask application not responding on port {DESTINATION_PORT} after {max_attempts} attempts")
    return False

# Initialize the proxy
def initialize():
    """Initialize the proxy server"""
    thread = threading.Thread(target=run_proxy_server, daemon=True)
    thread.start()
    logger.info("Replit port integration initialized")

# Register Flask blueprint with health check endpoint
def register_health_endpoints(app):
    """Register health check endpoints with Flask app"""
    @app.route('/health_port_check', methods=['GET'])
    def health_check():
        """Simple endpoint to check if the server is running"""
        return "OK", 200

# Start the proxy server automatically when imported
threading.Thread(target=lambda: (time.sleep(1), wait_for_flask(), initialize()), daemon=True).start()