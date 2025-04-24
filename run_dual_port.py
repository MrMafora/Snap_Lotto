#!/usr/bin/env python3
"""
Run the application with dual port binding
Binds to both port 5000 (internal) and port 8080 (Replit)
"""
import os
import sys
import subprocess
import threading
import time
import signal
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('dual_port')

def handle_signal(signum, frame):
    """Handle termination signals"""
    logger.info(f"Received signal {signum}. Shutting down...")
    sys.exit(0)

def start_app():
    """Start the gunicorn application on port 5000"""
    cmd = "gunicorn --bind 0.0.0.0:5000 --reuse-port --reload main:app"
    logger.info(f"Starting application with command: {cmd}")
    
    try:
        # Use Popen to start the process and return immediately
        process = subprocess.Popen(cmd, shell=True)
        logger.info(f"Application started with PID {process.pid}")
        return process
    except Exception as e:
        logger.error(f"Failed to start application: {e}")
        return None

def start_port_proxy():
    """Start the port proxy to forward from 8080 to 5000"""
    import http.server
    import socketserver
    import urllib.request
    
    class ProxyHandler(http.server.BaseHTTPRequestHandler):
        def do_GET(self): self._proxy_request('GET')
        def do_POST(self): self._proxy_request('POST')
        def do_HEAD(self): self._proxy_request('HEAD')
        def do_PUT(self): self._proxy_request('PUT')
        def do_DELETE(self): self._proxy_request('DELETE')
        def do_OPTIONS(self): self._proxy_request('OPTIONS')
        def do_PATCH(self): self._proxy_request('PATCH')
        
        def _proxy_request(self, method):
            """Forward request to port 5000"""
            target_url = f'http://localhost:5000{self.path}'
            
            try:
                # Get request body for methods that may have a body
                content_length = int(self.headers.get('Content-Length', 0))
                body = self.rfile.read(content_length) if content_length > 0 else None
                
                # Create request
                req = urllib.request.Request(target_url, data=body, method=method)
                
                # Copy headers
                for header, value in self.headers.items():
                    if header.lower() not in ('host', 'content-length'):
                        req.add_header(header, value)
                
                # Set content type if it exists
                content_type = self.headers.get('Content-Type')
                if content_type and body:
                    req.add_header('Content-Type', content_type)
                
                # Forward request
                response = urllib.request.urlopen(req, timeout=10)
                
                # Set response status
                self.send_response(response.status)
                
                # Forward response headers
                for header, value in response.getheaders():
                    self.send_header(header, value)
                self.end_headers()
                
                # Forward response body
                if method != 'HEAD':
                    self.wfile.write(response.read())
                    
            except Exception as e:
                # Handle error
                logger.error(f"Proxy error: {str(e)}")
                self.send_response(502)
                self.send_header('Content-Type', 'text/html; charset=utf-8')
                self.end_headers()
                
                error_message = f"""
                <html>
                <head><title>Proxy Error</title></head>
                <body>
                    <h1>Proxy Error</h1>
                    <p>The proxy server could not connect to the application server.</p>
                    <p>Error: {str(e)}</p>
                </body>
                </html>
                """
                self.wfile.write(error_message.encode('utf-8'))
        
        def log_message(self, format, *args):
            """Override to use our logger"""
            logger.info("%s - %s", self.address_string(), format % args)
    
    # Use ThreadingTCPServer for better performance
    socketserver.ThreadingTCPServer.allow_reuse_address = True
    httpd = socketserver.ThreadingTCPServer(("", 8080), ProxyHandler)
    
    logger.info("Starting proxy server on port 8080 → 5000")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        logger.info("Proxy server stopped")
    except Exception as e:
        logger.error(f"Proxy server error: {e}")

def main():
    """Main entry point"""
    # Set up signal handlers
    signal.signal(signal.SIGINT, handle_signal)
    signal.signal(signal.SIGTERM, handle_signal)
    
    # Start the application
    app_process = start_app()
    if not app_process:
        logger.error("Failed to start application")
        return 1
    
    # Wait a bit for the app to start
    time.sleep(2)
    
    # Start the port proxy in a separate thread
    proxy_thread = threading.Thread(target=start_port_proxy, daemon=True)
    proxy_thread.start()
    
    logger.info("Started application on port 5000 and proxy on port 8080")
    
    # Keep the main thread alive
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        logger.info("Interrupted by user")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())