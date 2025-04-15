#!/usr/bin/env python3
"""
Final port binding solution for Replit.
Integrates directly with the main.py file to add port 8080 binding.
This simplifies the solution by working within the same process.
"""
import os
import http.server
import socketserver
import threading
import time
import logging
import urllib.request
import sys
import signal

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('port_solution')

def run_proxy_server():
    """Run a proxy server on port 8080 that forwards to port 5000"""
    
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
            target_url = f"http://localhost:5000{self.path}"
            logger.info(f"Forwarding {method} request: {self.path} -> {target_url}")
            
            try:
                # Get headers
                headers = {}
                for key, val in self.headers.items():
                    headers[key] = val
                
                # Get body for POST/PUT
                content_length = int(self.headers.get('Content-Length', 0))
                body = self.rfile.read(content_length) if content_length > 0 else None
                
                # Create request
                req = urllib.request.Request(
                    url=target_url,
                    data=body,
                    headers=headers,
                    method=method
                )
                
                # Send request
                with urllib.request.urlopen(req, timeout=30) as response:
                    # Copy status code
                    self.send_response(response.getcode())
                    
                    # Copy headers
                    for header, value in response.getheaders():
                        if header.lower() != 'transfer-encoding':
                            self.send_header(header, value)
                    self.end_headers()
                    
                    # Copy body
                    self.wfile.write(response.read())
                    
            except Exception as e:
                logger.error(f"Error proxying request: {str(e)}")
                self.send_error(502, f"Proxy error: {str(e)}")
        
        def log_message(self, format, *args):
            logger.info(f"Port 8080: {self.client_address[0]} - {format % args}")
    
    # Create and start server
    try:
        port = 8080
        handler = ProxyHandler
        
        logger.info(f"Starting proxy server on port {port}")
        with socketserver.TCPServer(("0.0.0.0", port), handler) as httpd:
            httpd.allow_reuse_address = True
            print(f"Proxy server running on 0.0.0.0:{port}")
            httpd.serve_forever()
    except Exception as e:
        logger.error(f"Failed to start proxy server: {str(e)}")
        
def wait_for_port(port, max_wait=30):
    """Wait for port to become available"""
    logger.info(f"Waiting for port {port} to become available")
    
    for _ in range(max_wait):
        try:
            with urllib.request.urlopen(f"http://localhost:{port}/", timeout=1) as response:
                if response.getcode() == 200:
                    logger.info(f"Port {port} is now available")
                    return True
        except Exception:
            time.sleep(1)
    
    logger.warning(f"Port {port} did not become available after {max_wait} seconds")
    return False

def start_proxy():
    """Start the proxy server in a new thread"""
    # Wait for the main application to be up
    if not wait_for_port(5000, max_wait=10):
        logger.warning("Main application not detected on port 5000, but continuing anyway")
    
    # Start the proxy server in a new thread
    proxy_thread = threading.Thread(target=run_proxy_server)
    proxy_thread.daemon = True
    proxy_thread.start()
    logger.info("Proxy server started in background thread")

if __name__ == "__main__":
    # For manual testing
    start_proxy()
    
    # Keep the main thread alive
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("Shutdown requested")
    except Exception:
        print("Other exception caught")
    finally:
        print("Exiting")