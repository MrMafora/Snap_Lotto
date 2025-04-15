#!/usr/bin/env python3
"""
Simple port 8080 bridge for the main application.
This script creates a dedicated reverse proxy server that listens on port 8080
and forwards all requests to the main application running on port 5000.
"""
import http.server
import socketserver
import threading
import urllib.request
import urllib.error
import time
import logging
import sys
import signal

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('port_bridge')

class ProxyHandler(http.server.BaseHTTPRequestHandler):
    """Request handler that forwards requests from port 8080 to 5000"""
    
    def do_GET(self):
        self.proxy_request('GET')
    
    def do_POST(self):
        self.proxy_request('POST')
    
    def do_PUT(self):
        self.proxy_request('PUT')
    
    def do_DELETE(self):
        self.proxy_request('DELETE')
    
    def proxy_request(self, method):
        """Forward request to the main application"""
        target_url = f"http://localhost:5000{self.path}"
        
        try:
            # Build headers
            headers = {}
            for key, val in self.headers.items():
                if key.lower() not in ('host', 'connection'):
                    headers[key] = val
            
            # Get request body if needed
            content_length = int(self.headers.get('Content-Length', 0))
            body = self.rfile.read(content_length) if content_length > 0 else None
            
            # Create and send request
            req = urllib.request.Request(
                url=target_url,
                data=body,
                headers=headers,
                method=method
            )
            
            with urllib.request.urlopen(req, timeout=30) as response:
                # Copy response status
                self.send_response(response.getcode())
                
                # Copy response headers
                for header, value in response.getheaders():
                    if header.lower() not in ('connection', 'transfer-encoding'):
                        self.send_header(header, value)
                self.end_headers()
                
                # Copy response body
                self.wfile.write(response.read())
                
        except urllib.error.HTTPError as e:
            self.send_response(e.code)
            self.send_header('Content-Type', 'text/plain')
            self.end_headers()
            self.wfile.write(f"Error: {str(e)}".encode('utf-8'))
            
        except Exception as e:
            logger.error(f"Error proxying request to {target_url}: {str(e)}")
            self.send_response(502)
            self.send_header('Content-Type', 'text/plain')
            self.end_headers()
            self.wfile.write(f"Proxy Error: {str(e)}".encode('utf-8'))
    
    def log_message(self, format, *args):
        """Override default logging"""
        logger.info(f"{self.client_address[0]} - {format % args}")


def run_proxy_server():
    """Run the proxy server on port 8080"""
    port = 8080
    retries = 3
    
    for attempt in range(retries):
        try:
            logger.info(f"Starting proxy server on port {port} (attempt {attempt+1}/{retries})")
            
            # Close any existing connections on this port
            import socket
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            sock.bind(("0.0.0.0", port))
            sock.close()
            
            # Now try to start the server
            httpd = socketserver.TCPServer(("0.0.0.0", port), ProxyHandler, bind_and_activate=False)
            httpd.allow_reuse_address = True
            httpd.server_bind()
            httpd.server_activate()
            print(f"Port bridge running on port {port}")
            httpd.serve_forever()
            return  # Success
        except Exception as e:
            logger.error(f"Failed to start proxy server (attempt {attempt+1}): {str(e)}")
            time.sleep(2)
    
    # If we get here, all attempts failed
    logger.error(f"Failed to start proxy server after {retries} attempts")
    sys.exit(1)


if __name__ == "__main__":
    # Handle graceful shutdown
    def signal_handler(sig, frame):
        logger.info("Shutting down port bridge")
        sys.exit(0)
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Wait for main application to start
    main_port = 5000
    logger.info(f"Checking if main application is available on port {main_port}")
    
    try:
        with urllib.request.urlopen(f"http://localhost:{main_port}/", timeout=2) as response:
            if response.getcode() == 200:
                logger.info(f"Main application available on port {main_port}")
    except Exception as e:
        logger.warning(f"Error connecting to main application: {str(e)}")
        logger.warning(f"Will attempt to start proxy anyway")
    
    # Start the proxy server
    run_proxy_server()