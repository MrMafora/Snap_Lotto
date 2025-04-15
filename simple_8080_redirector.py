#!/usr/bin/env python3
"""
Simple HTTP server that listens on port 8080 and redirects all requests to port 5000.
This version is specifically optimized for Replit's environment.
"""
import http.server
import socketserver
import logging
import os
import sys

# Configure logging to both console and file
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('simple_8080.log')
    ]
)
logger = logging.getLogger('port_bridge')

class RedirectHandler(http.server.BaseHTTPRequestHandler):
    """Handler to redirect requests from port 8080 to port 5000"""
    
    def redirect_request(self):
        """Redirect all requests to port 5000"""
        try:
            # Send 302 redirect
            self.send_response(302)
            
            # Get current host and replace port if needed
            host = self.headers.get('Host', '')
            if ':8080' in host:
                redirect_host = host.replace(':8080', ':5000')
            else:
                # If no port in host, make sure we redirect to port 5000
                redirect_host = host
                
            # Construct full redirect URL
            redirect_url = f'https://{redirect_host}{self.path}'
            
            # Set redirect location header
            self.send_header('Location', redirect_url)
            self.end_headers()
            
            logger.info(f"Redirected: {host}{self.path} -> {redirect_host}{self.path}")
        except Exception as e:
            logger.error(f"Error during redirect: {str(e)}")

    # Handle all HTTP methods
    do_GET = do_POST = do_PUT = do_DELETE = do_HEAD = do_OPTIONS = redirect_request
    
    def log_message(self, format, *args):
        """Custom logging for requests"""
        logger.info(f"8080 Server: {format % args}")

def main():
    """Start the redirect server on port 8080"""
    try:
        # Create server instance, enabling reuse of the address
        server_address = ('0.0.0.0', 8080)
        httpd = socketserver.TCPServer(server_address, RedirectHandler)
        httpd.allow_reuse_address = True
        
        logger.info(f'Starting port redirector on {server_address[0]}:{server_address[1]}')
        logger.info('Redirecting all traffic to port 5000')
        
        # Start server
        httpd.serve_forever()
    except Exception as e:
        logger.error(f'Error in port 8080 redirector: {str(e)}')
        sys.exit(1)

if __name__ == "__main__":
    # Handle KeyboardInterrupt gracefully
    try:
        main()
    except KeyboardInterrupt:
        logger.info("Shutting down port 8080 redirector")
        sys.exit(0)