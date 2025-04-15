#!/usr/bin/env python3
"""
Simple port 8080 to 5000 bridge for Replit.
"""
import http.server
import urllib.request
import urllib.error
import logging
import signal
import sys
import threading
import time
import io
import socket

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(), logging.FileHandler('bridge.log')]
)
logger = logging.getLogger('port_bridge')

# Bridge settings
SOURCE_PORT = 8080
TARGET_PORT = 5000
TARGET_HOST = "localhost"

class BridgeHandler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        self.proxy_request("GET")
    
    def do_POST(self):
        self.proxy_request("POST")
    
    def do_PUT(self):
        self.proxy_request("PUT")
    
    def do_DELETE(self):
        self.proxy_request("DELETE")
    
    def do_HEAD(self):
        self.proxy_request("HEAD")
    
    def do_OPTIONS(self):
        self.proxy_request("OPTIONS")
    
    def do_PATCH(self):
        self.proxy_request("PATCH")
    
    def proxy_request(self, method):
        """Forward the request to the target port"""
        target_url = f"http://{TARGET_HOST}:{TARGET_PORT}{self.path}"
        
        # Get request headers
        headers = {}
        for header in self.headers:
            headers[header] = self.headers[header]
        
        # Special handling for host header
        headers['Host'] = f"{TARGET_HOST}:{TARGET_PORT}"
        
        # Get request body if present
        content_length = int(self.headers.get('Content-Length', 0))
        body = None
        if content_length > 0:
            body = self.rfile.read(content_length)
        
        try:
            # Create the request
            req = urllib.request.Request(
                url=target_url,
                data=body,
                headers=headers,
                method=method
            )
            
            # Send the request to the target
            with urllib.request.urlopen(req) as response:
                # Copy response status and headers
                self.send_response(response.status)
                for header, value in response.getheaders():
                    # Skip transfer-encoding as it can cause issues
                    if header.lower() != 'transfer-encoding':
                        self.send_header(header, value)
                self.end_headers()
                
                # Copy response body
                self.wfile.write(response.read())
                
        except urllib.error.HTTPError as e:
            # Handle HTTP errors
            self.send_response(e.code)
            for header, value in e.headers.items():
                if header.lower() != 'transfer-encoding':
                    self.send_header(header, value)
            self.end_headers()
            
            # Copy error response body if available
            if hasattr(e, 'read'):
                self.wfile.write(e.read())
            else:
                self.wfile.write(str(e).encode('utf-8'))
                
        except Exception as e:
            # Handle other errors
            logger.error(f"Error proxying request to {target_url}: {str(e)}")
            self.send_response(502)  # Bad Gateway
            self.send_header('Content-Type', 'text/plain')
            self.end_headers()
            self.wfile.write(f"Error proxying request: {str(e)}".encode('utf-8'))
    
    def log_message(self, format, *args):
        """Override default logging to use our logger"""
        logger.info(f"{self.client_address[0]} - {args[0]}")

def check_target_port():
    """Check if the target port is running before starting the bridge"""
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(2)
            result = s.connect_ex((TARGET_HOST, TARGET_PORT))
            if result == 0:
                logger.info(f"Target port {TARGET_PORT} is available")
                return True
            else:
                logger.warning(f"Target port {TARGET_PORT} is not available (error code: {result})")
                return False
    except Exception as e:
        logger.error(f"Error checking target port: {str(e)}")
        return False

def check_source_port():
    """Check if the source port is available for binding"""
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(1)
            result = s.connect_ex(('127.0.0.1', SOURCE_PORT))
            if result != 0:
                # Port is available
                logger.info(f"Source port {SOURCE_PORT} is available for binding")
                return True
            else:
                logger.warning(f"Source port {SOURCE_PORT} is already in use")
                return False
    except Exception as e:
        logger.error(f"Error checking source port: {str(e)}")
        return False

def run_bridge():
    """Start the port bridge"""
    # First check if our target port is available
    logger.info("Performing pre-flight checks...")
    
    # Verify target port
    if not check_target_port():
        logger.error(f"Target port {TARGET_PORT} is not available. Bridge cannot start.")
        return False
    
    # Verify source port
    if not check_source_port():
        logger.error(f"Source port {SOURCE_PORT} is already in use. Bridge cannot start.")
        return False
    
    logger.info("Pre-flight checks passed. Starting bridge...")
        
    try:
        server_address = ('', SOURCE_PORT)
        
        # Create and configure the HTTP server
        logger.info(f"Creating HTTP server on port {SOURCE_PORT}...")
        httpd = http.server.HTTPServer(server_address, BridgeHandler)
        httpd.timeout = 1
        
        # Handle signals for graceful shutdown
        def signal_handler(sig, frame):
            logger.info(f"Received signal {sig}, shutting down bridge...")
            httpd.server_close()
            sys.exit(0)
        
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
        
        logger.info(f"Starting port bridge: forwarding requests from port {SOURCE_PORT} to port {TARGET_PORT}")
        
        # Use a flag for shutdown
        shutdown_flag = threading.Event()
        
        try:
            # Define the server thread function
            def serve_forever():
                """Run the HTTP server until shutdown is requested"""
                try:
                    logger.info("Server thread started")
                    while not shutdown_flag.is_set():
                        httpd.handle_request()
                except Exception as e:
                    logger.error(f"Error in server thread: {str(e)}")
                finally:
                    logger.info("Server thread shutting down")
            
            # Start the server in a background thread
            server_thread = threading.Thread(target=serve_forever)
            server_thread.daemon = True
            server_thread.start()
            
            logger.info(f"Bridge is now running on port {SOURCE_PORT}, forwarding to {TARGET_HOST}:{TARGET_PORT}")
            
            # Keep the main thread alive
            while server_thread.is_alive():
                time.sleep(1)
                
        except KeyboardInterrupt:
            logger.info("KeyboardInterrupt received, shutting down...")
        except Exception as e:
            logger.error(f"Unexpected error: {str(e)}")
        finally:
            # Clean up the server
            shutdown_flag.set()
            try:
                httpd.server_close()
            except Exception as e:
                logger.error(f"Error closing server: {str(e)}")
            logger.info("Bridge shutdown complete")
            
    except socket.error as e:
        if e.errno == 98:  # Address already in use
            logger.error(f"Port {SOURCE_PORT} is already in use. Cannot start bridge.")
        else:
            logger.error(f"Socket error: {str(e)}")
        return False
    except Exception as e:
        logger.error(f"Failed to start bridge: {str(e)}")
        return False
    
    return True

if __name__ == "__main__":
    run_bridge()