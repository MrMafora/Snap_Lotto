#!/usr/bin/env python3
"""
Standalone port proxy for Replit deployment
This script forwards all traffic from port 8080 to port 5000
"""
import http.server
import socket
import socketserver
import sys
import threading
import time
import urllib.request
import urllib.error
import os

# Configuration
SOURCE_PORT = 8080
DESTINATION_PORT = 5000
MAX_WAIT_TIME = 60  # Maximum time to wait for the destination server (seconds)
HOSTNAME = "0.0.0.0"  # Bind to all interfaces
PID_FILE = "port_proxy.pid"
LOG_FILE = "port_proxy.log"


def log_message(message):
    """Log a message to both stderr and log file"""
    timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
    formatted_message = f"[{timestamp}] [PORT_PROXY] {message}"
    
    # Print to stderr
    print(formatted_message, file=sys.stderr, flush=True)
    
    # Append to log file
    with open(LOG_FILE, "a") as f:
        f.write(formatted_message + "\n")


def create_pid_file():
    """Create a PID file"""
    with open(PID_FILE, "w") as f:
        f.write(str(os.getpid()))
    log_message(f"PID file created: {PID_FILE}")


def remove_pid_file():
    """Remove the PID file"""
    if os.path.exists(PID_FILE):
        os.remove(PID_FILE)
        log_message(f"PID file removed: {PID_FILE}")


def check_destination_server():
    """Check if the destination server is running"""
    try:
        with urllib.request.urlopen(f"http://localhost:{DESTINATION_PORT}/health_port_check", timeout=1) as response:
            return response.getcode() == 200
    except Exception:
        return False


def wait_for_destination_server():
    """Wait for the destination server to become available"""
    log_message(f"Waiting for destination server on port {DESTINATION_PORT}...")
    
    start_time = time.time()
    while time.time() - start_time < MAX_WAIT_TIME:
        if check_destination_server():
            log_message(f"Destination server on port {DESTINATION_PORT} is available")
            return True
        time.sleep(1)
    
    log_message(f"Destination server not available after {MAX_WAIT_TIME} seconds")
    return False


class ProxyHandler(http.server.BaseHTTPRequestHandler):
    """Handler for HTTP requests that forwards to the destination server"""
    
    def do_GET(self):
        """Handle GET requests"""
        self._forward_request("GET")
    
    def do_POST(self):
        """Handle POST requests"""
        content_length = int(self.headers.get('Content-Length', 0))
        body = self.rfile.read(content_length) if content_length > 0 else None
        self._forward_request("POST", body)
    
    def do_PUT(self):
        """Handle PUT requests"""
        content_length = int(self.headers.get('Content-Length', 0))
        body = self.rfile.read(content_length) if content_length > 0 else None
        self._forward_request("PUT", body)
    
    def do_DELETE(self):
        """Handle DELETE requests"""
        self._forward_request("DELETE")
    
    def do_HEAD(self):
        """Handle HEAD requests"""
        self._forward_request("HEAD")
    
    def do_OPTIONS(self):
        """Handle OPTIONS requests"""
        self._forward_request("OPTIONS")
    
    def do_PATCH(self):
        """Handle PATCH requests"""
        content_length = int(self.headers.get('Content-Length', 0))
        body = self.rfile.read(content_length) if content_length > 0 else None
        self._forward_request("PATCH", body)
    
    def _forward_request(self, method, body=None):
        """Forward a request to the destination server"""
        destination_url = f"http://localhost:{DESTINATION_PORT}{self.path}"
        
        try:
            # Create request object
            req = urllib.request.Request(
                destination_url,
                data=body,
                method=method
            )
            
            # Copy headers, excluding certain ones that could cause issues
            for header_name, header_value in self.headers.items():
                if header_name.lower() not in ('host', 'content-length'):
                    req.add_header(header_name, header_value)
            
            # Send the request
            with urllib.request.urlopen(req) as response:
                # Copy status code and headers
                self.send_response(response.status)
                
                # Copy response headers
                for header, value in response.getheaders():
                    if header.lower() not in ('transfer-encoding', 'content-length'):
                        self.send_header(header, value)
                
                # Finish headers
                self.end_headers()
                
                # Copy response body
                self.wfile.write(response.read())
                
        except urllib.error.HTTPError as e:
            # Handle HTTP errors
            self.send_response(e.code)
            for header, value in e.headers.items():
                if header.lower() not in ('transfer-encoding', 'content-length'):
                    self.send_header(header, value)
            self.end_headers()
            self.wfile.write(e.read())
            
        except Exception as e:
            # Log and return a 502 Bad Gateway error
            log_message(f"Error forwarding request to {destination_url}: {e}")
            self.send_response(502)
            self.send_header('Content-Type', 'text/plain')
            self.end_headers()
            self.wfile.write(f"Error: Could not forward request to destination server: {e}".encode())
    
    def log_message(self, format, *args):
        """Override default logging to use our custom logger"""
        log_message(f"{self.client_address[0]} - {format % args}")


def run_proxy_server():
    """Run the HTTP proxy server"""
    
    # Create log file if it doesn't exist
    if not os.path.exists(LOG_FILE):
        with open(LOG_FILE, "w") as f:
            pass
    
    # Create PID file
    create_pid_file()
    
    # Set up a handler for clean shutdown
    try:
        # Wait for the destination server
        if not wait_for_destination_server():
            log_message("Exiting because destination server is not available")
            remove_pid_file()
            return
        
        # Create server
        log_message(f"Starting proxy server on port {SOURCE_PORT} forwarding to port {DESTINATION_PORT}")
        
        class ReusableTCPServer(socketserver.TCPServer):
            allow_reuse_address = True
        
        with ReusableTCPServer((HOSTNAME, SOURCE_PORT), ProxyHandler) as httpd:
            # Run the server in a separate thread
            server_thread = threading.Thread(target=httpd.serve_forever)
            server_thread.daemon = True
            server_thread.start()
            
            log_message(f"Proxy server is running at http://{HOSTNAME}:{SOURCE_PORT}/")
            
            try:
                # Keep main thread alive
                while True:
                    # Check if destination server is still available
                    if not check_destination_server():
                        log_message("Destination server is not responding, checking again...")
                        time.sleep(5)
                        if not check_destination_server():
                            log_message("Destination server is still not responding, restarting proxy...")
                            break
                    
                    time.sleep(10)
            
            except KeyboardInterrupt:
                log_message("Keyboard interrupt received, shutting down")
            finally:
                log_message("Shutting down proxy server")
                httpd.shutdown()
                httpd.server_close()
    
    except Exception as e:
        log_message(f"Error in proxy server: {e}")
    
    finally:
        # Clean up
        remove_pid_file()
        log_message("Proxy server stopped")


if __name__ == "__main__":
    run_proxy_server()