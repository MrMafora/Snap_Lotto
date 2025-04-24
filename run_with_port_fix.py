#!/usr/bin/env python3
"""
Run the application with proper port forwarding for Replit
"""
import os
import sys
import subprocess
import threading
import time
import signal
import socket
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('port_fix')

# Configuration
INTERNAL_PORT = 5000  # Flask's default port
REPLIT_PORT = 8080    # The port Replit expects

def is_port_in_use(port):
    """Check if a port is already in use"""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex(('127.0.0.1', port)) == 0

def handle_signal(signum, frame):
    """Handle termination signals"""
    logger.info(f"Received signal {signum}. Shutting down...")
    # Kill the gunicorn process if it's running
    if os.path.exists("gunicorn.pid"):
        try:
            with open("gunicorn.pid", "r") as f:
                pid = int(f.read().strip())
            os.kill(pid, signal.SIGTERM)
            logger.info(f"Sent SIGTERM to gunicorn process {pid}")
        except Exception as e:
            logger.error(f"Failed to terminate gunicorn: {e}")
    sys.exit(0)

def start_app():
    """Start the main application on the internal port"""
    cmd = f"gunicorn --bind 0.0.0.0:{INTERNAL_PORT} --reuse-port --reload --pid gunicorn.pid main:app"
    logger.info(f"Starting application with command: {cmd}")
    
    try:
        process = subprocess.Popen(cmd, shell=True)
        logger.info(f"Application started with PID {process.pid}")
        return process
    except Exception as e:
        logger.error(f"Failed to start application: {e}")
        return None

def wait_for_app():
    """Wait for the application to be ready"""
    logger.info(f"Waiting for application to start on port {INTERNAL_PORT}...")
    max_retries = 10
    retry_count = 0
    
    while retry_count < max_retries:
        if is_port_in_use(INTERNAL_PORT):
            # Try to make an HTTP request to confirm the app is responding
            try:
                import urllib.request
                response = urllib.request.urlopen(f"http://127.0.0.1:{INTERNAL_PORT}/", timeout=5)
                if response.status in (200, 301, 302):
                    logger.info(f"Application is running on port {INTERNAL_PORT}")
                    return True
            except:
                pass
        
        retry_count += 1
        logger.info(f"Waiting for application... ({retry_count}/{max_retries})")
        time.sleep(2)
    
    logger.warning(f"Application not ready after {max_retries} attempts")
    return False

def run_proxy():
    """Run the proxy server to forward requests from REPLIT_PORT to INTERNAL_PORT"""
    from http.server import HTTPServer, BaseHTTPRequestHandler
    import urllib.request
    import urllib.error
    
    class ProxyHandler(BaseHTTPRequestHandler):
        """HTTP request handler that forwards all requests to the target server"""
        
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
        
        def proxy_request(self, method):
            """Forward the request to the target server"""
            target_url = f"http://127.0.0.1:{INTERNAL_PORT}{self.path}"
            
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
                response = urllib.request.urlopen(req, timeout=10)
                
                # Set response status
                self.send_response(response.status)
                
                # Forward response headers
                for header, value in response.getheaders():
                    self.send_header(header, value)
                self.end_headers()
                
                # Forward response body for methods that expect it
                if method != 'HEAD':
                    self.wfile.write(response.read())
                    
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
                </body>
                </html>
                """
                self.wfile.write(error_message.encode('utf-8'))
    
    # Start the proxy server
    server = HTTPServer(('0.0.0.0', REPLIT_PORT), ProxyHandler)
    logger.info(f"Starting proxy server on port {REPLIT_PORT} -> {INTERNAL_PORT}")
    server.serve_forever()

def main():
    """Main entry point"""
    # Set up signal handlers
    signal.signal(signal.SIGINT, handle_signal)
    signal.signal(signal.SIGTERM, handle_signal)
    
    # Check if ports are already in use
    if is_port_in_use(INTERNAL_PORT):
        logger.warning(f"Port {INTERNAL_PORT} is already in use")
    
    if is_port_in_use(REPLIT_PORT):
        logger.warning(f"Port {REPLIT_PORT} is already in use")
        logger.info("Continuing anyway as the existing process might be stopped")
    
    # Start the application
    app_process = start_app()
    if not app_process:
        logger.error("Failed to start application")
        return 1
    
    # Wait for the application to be ready
    if not wait_for_app():
        logger.warning("Application not ready, but continuing with proxy setup")
    
    # Run the proxy in a separate thread
    proxy_thread = threading.Thread(target=run_proxy, daemon=True)
    proxy_thread.start()
    
    logger.info("Application and proxy are running")
    logger.info(f"Internal port: {INTERNAL_PORT}, Replit port: {REPLIT_PORT}")
    
    try:
        # Keep the main thread alive
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        logger.info("Interrupted by user")
    finally:
        handle_signal(signal.SIGTERM, None)
    
    return 0

if __name__ == "__main__":
    sys.exit(main())