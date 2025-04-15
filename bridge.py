#!/usr/bin/env python3
"""
Simple port 8080 to 5000 bridge for Replit.
"""
import http.server
import socketserver
import requests
import logging
import sys
import signal

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger('bridge')

class BridgeHandler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        self.proxy_request('GET')
        
    def do_POST(self):
        self.proxy_request('POST')
        
    def do_PUT(self):
        self.proxy_request('PUT')
        
    def do_DELETE(self):
        self.proxy_request('DELETE')
        
    def do_HEAD(self):
        self.proxy_request('HEAD')
        
    def proxy_request(self, method):
        target_url = f"http://localhost:5000{self.path}"
        logger.info(f"Forwarding {method} request: {self.path} -> {target_url}")
        
        try:
            # Get request body for POST/PUT
            content_length = int(self.headers.get('Content-Length', 0))
            body = self.rfile.read(content_length) if content_length > 0 else None
            
            # Forward headers
            headers = {key: val for key, val in self.headers.items()}
            
            # Make request to target
            response = requests.request(
                method=method,
                url=target_url,
                headers=headers,
                data=body,
                timeout=10,
                allow_redirects=False,
            )
            
            # Send response status code
            self.send_response(response.status_code)
            
            # Send headers
            for header, value in response.headers.items():
                if header.lower() != 'transfer-encoding':
                    self.send_header(header, value)
            self.end_headers()
            
            # Send body
            self.wfile.write(response.content)
            
        except Exception as e:
            logger.error(f"Error forwarding request: {str(e)}")
            self.send_error(502, f"Error forwarding to port 5000: {str(e)}")
    
    def log_message(self, format, *args):
        logger.info(f"Port 8080: {self.client_address[0]} - {args[0]} {args[1]}")

def run_bridge():
    port = 8080
    server_address = ('0.0.0.0', port)
    
    logger.info(f"Starting bridge on port {port}")
    
    try:
        with socketserver.ThreadingTCPServer(server_address, BridgeHandler) as httpd:
            httpd.allow_reuse_address = True
            print(f"Bridge running on port {port}, forwarding to port 5000")
            httpd.serve_forever()
    except Exception as e:
        logger.error(f"Failed to start bridge: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    # Set up signal handlers
    def signal_handler(sig, frame):
        logger.info(f"Received signal {sig}, shutting down...")
        sys.exit(0)
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    run_bridge()