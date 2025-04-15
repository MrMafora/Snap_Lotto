"""
PORT BINDING SOLUTION FOR REPLIT

This script provides a complete solution for binding to both port 5000 and port 8080
in the Replit environment. It can be used in three ways:

1. As a standalone script to start a redirect server on port 8080
2. Imported to add dual-port functionality to any Python application
3. Used with the workflow to ensure port 8080 is always available

Usage:
  python port_binding_solution.py             # Start port 8080 redirector to port 5000
  python port_binding_solution.py 3000        # Start port 8080 redirector to port 3000
  python port_binding_solution.py --check     # Check if port 8080 is available
"""
import sys
import os
import logging
import socket
import http.server
import socketserver
import threading
import time
import argparse

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("port_binding")

class RedirectHandler(http.server.BaseHTTPRequestHandler):
    """Handler that redirects all requests to the target port"""
    
    @classmethod
    def create_handler_class(cls, target_port):
        """Create a handler class configured for a specific target port"""
        
        class ConfiguredHandler(cls):
            TARGET_PORT = target_port
            
        return ConfiguredHandler
    
    def redirect_request(self):
        """Send a redirect to the same path on the target port"""
        self.send_response(302)
        host = self.headers.get('Host', '')
        if ':8080' in host:
            redirect_host = host.replace(':8080', f':{self.TARGET_PORT}')
        else:
            parts = host.split('.')
            if len(parts) > 1:
                redirect_host = host
            else:
                redirect_host = f"{host}:{self.TARGET_PORT}"
        
        self.send_header('Location', f'https://{redirect_host}{self.path}')
        self.end_headers()
    
    def do_GET(self): self.redirect_request()
    def do_POST(self): self.redirect_request()
    def do_PUT(self): self.redirect_request()
    def do_DELETE(self): self.redirect_request()
    def do_HEAD(self): self.redirect_request() 
    def do_OPTIONS(self): self.redirect_request()
    
    def log_message(self, format, *args):
        """Override to minimize logging"""
        if args and args[1] and (500 <= int(args[1]) < 600):
            logger.error(f"Error %s - %s", self.path, args[1])

def is_port_in_use(port):
    """Check if the specified port is already in use"""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex(('localhost', port)) == 0

def start_port_8080_server(target_port=5000):
    """
    Start an HTTP server on port 8080 that redirects to the target port.
    
    Args:
        target_port (int): The target port to redirect requests to
        
    Returns:
        bool: True if server started successfully, False otherwise
    """
    if is_port_in_use(8080):
        logger.info("Port 8080 is already in use")
        return False
        
    try:
        # Create a handler class configured for the target port
        handler = RedirectHandler.create_handler_class(target_port)
        
        # Create the HTTP server
        logger.info(f"Starting HTTP server on port 8080 (redirecting to port {target_port})")
        server = socketserver.TCPServer(("0.0.0.0", 8080), handler)
        
        # Run the server in a daemon thread
        server_thread = threading.Thread(target=server.serve_forever)
        server_thread.daemon = True
        server_thread.start()
        
        logger.info(f"Server started on port 8080 and redirecting to port {target_port}")
        return True
    except Exception as e:
        logger.error(f"Error starting server: {e}")
        return False

def ensure_port_8080_binding(target_port=5000):
    """
    Ensure that port 8080 is bound, starting a server if needed.
    This function is safe to call from any application.
    
    Args:
        target_port (int): The target port to redirect requests to
        
    Returns:
        bool: True if port 8080 is bound (either already or newly started)
    """
    if is_port_in_use(8080):
        logger.info("Port 8080 is already in use, no action needed")
        return True
    else:
        return start_port_8080_server(target_port)

def check_port_8080():
    """
    Check if port 8080 is in use.
    
    Returns:
        bool: True if port 8080 is in use, False otherwise
    """
    if is_port_in_use(8080):
        logger.info("Port 8080 is in use")
        return True
    else:
        logger.info("Port 8080 is not in use")
        return False

if __name__ == "__main__":
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='Port 8080 binding solution for Replit')
    parser.add_argument('target_port', nargs='?', type=int, default=5000, 
                        help='Target port to redirect requests to (default: 5000)')
    parser.add_argument('--check', action='store_true', 
                        help='Check if port 8080 is in use and exit')
    args = parser.parse_args()
    
    if args.check:
        # Just check if port 8080 is in use
        if check_port_8080():
            sys.exit(0)  # Port is in use
        else:
            sys.exit(1)  # Port is not in use
    else:
        # Start the port 8080 server
        logger.info(f"Starting port 8080 binding solution (target port: {args.target_port})")
        if start_port_8080_server(args.target_port):
            # Keep the main thread alive
            try:
                while True:
                    time.sleep(60)
            except KeyboardInterrupt:
                logger.info("Exiting...")
        else:
            sys.exit(1)  # Failed to start server