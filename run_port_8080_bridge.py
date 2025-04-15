#!/usr/bin/env python3
"""
Simple HTTP server that listens on port 8080 and redirects all requests to port 5000.
This ensures compatibility with Replit's external access requirements.
"""
import http.server
import socketserver
import threading
import time
import sys
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger('port_bridge')

class RedirectHandler(http.server.BaseHTTPRequestHandler):
    def redirect_request(self):
        """Redirect all requests to the same path on port 5000"""
        try:
            self.send_response(302)
            host = self.headers.get('Host', '')
            # Replace port 8080 with 5000 in the host header
            redirect_host = host.replace(':8080', ':5000') if ':8080' in host else host
            redirect_url = f'https://{redirect_host}{self.path}'
            self.send_header('Location', redirect_url)
            self.end_headers()
            logger.info(f"Redirecting request from {host}{self.path} to {redirect_host}{self.path}")
        except Exception as e:
            logger.error(f"Error during redirect: {str(e)}")
    
    # Handle all HTTP methods
    do_GET = do_POST = do_PUT = do_DELETE = do_HEAD = do_OPTIONS = redirect_request
    
    def log_message(self, format, *args):
        """Override the default logging to use our logger"""
        logger.info(f"8080 Server: {format % args}")

def run_server():
    """Run the HTTP server on port 8080"""
    try:
        logger.info('Starting redirector server on port 8080...')
        with socketserver.TCPServer(('0.0.0.0', 8080), RedirectHandler) as server:
            logger.info('Port 8080 server started successfully. Redirecting all traffic to port 5000.')
            server.serve_forever()
    except Exception as e:
        logger.error(f'Error starting port 8080 server: {e}')
        sys.exit(1)

if __name__ == "__main__":
    run_server()