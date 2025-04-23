#!/usr/bin/env python3
"""
Port Proxy Service

This script runs as a background daemon that forwards traffic from port 8080 to port 5000.
It's designed to run alongside the main application to make it accessible on both ports.

Usage:
  python port_proxy_service.py start  # Start proxy as daemon
  python port_proxy_service.py stop   # Stop running proxy
  python port_proxy_service.py status # Check if proxy is running
"""

import atexit
import http.server
import logging
import os
import signal
import socket
import sys
import threading
import time
import urllib.request
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("logs/port_proxy.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('port_proxy')

# Constants
PID_FILE = "logs/port_proxy.pid"
PORT = 8080
TARGET_PORT = 5000

# Ensure logs directory exists
Path("logs").mkdir(exist_ok=True)

class ProxyHTTPRequestHandler(http.server.BaseHTTPRequestHandler):
    """HTTP request handler that forwards requests to another port"""
    
    def do_GET(self):
        """Handle GET requests by forwarding them to the target port"""
        self._forward_request("GET")
    
    def do_POST(self):
        """Handle POST requests by forwarding them to the target port"""
        content_length = int(self.headers.get('Content-Length', 0))
        post_data = self.rfile.read(content_length) if content_length > 0 else None
        self._forward_request("POST", post_data)
    
    def _forward_request(self, method, body=None):
        """Forward a request to the target port"""
        try:
            target_url = f"http://localhost:{TARGET_PORT}{self.path}"
            
            # Prepare headers
            headers = {}
            for header in self.headers:
                if header.lower() not in ('host', 'content-length'):
                    headers[header] = self.headers[header]
            
            # Create and send the request
            req = urllib.request.Request(
                target_url,
                data=body,
                headers=headers,
                method=method
            )
            
            with urllib.request.urlopen(req) as response:
                # Copy the response status
                self.send_response(response.status)
                
                # Copy the response headers
                for header, value in response.getheaders():
                    self.send_header(header, value)
                self.end_headers()
                
                # Copy the response body
                self.wfile.write(response.read())
        
        except Exception as e:
            logger.error(f"Error forwarding {method} request to {self.path}: {e}")
            self.send_response(502)
            self.send_header('Content-type', 'text/plain')
            self.end_headers()
            self.wfile.write(f"Error: {str(e)}".encode())
    
    # Minimize logging output to keep the console clean
    def log_message(self, format, *args):
        if args and len(args) > 1 and (args[1].startswith('5') or args[1].startswith('4')):
            logger.warning(f"{args[0]} - {args[1]} - {args[2]}")
        return

def is_port_in_use(port):
    """Check if a port is already in use"""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex(('localhost', port)) == 0

def write_pid_file():
    """Write the current process ID to the PID file"""
    with open(PID_FILE, 'w') as f:
        f.write(str(os.getpid()))
    atexit.register(lambda: os.remove(PID_FILE) if os.path.exists(PID_FILE) else None)

def read_pid_file():
    """Read the process ID from the PID file if it exists"""
    if os.path.exists(PID_FILE):
        with open(PID_FILE, 'r') as f:
            try:
                return int(f.read().strip())
            except ValueError:
                return None
    return None

def is_process_running(pid):
    """Check if a process with the given ID is running"""
    try:
        os.kill(pid, 0)
        return True
    except (OSError, ProcessLookupError):
        return False

def start_proxy():
    """Start the proxy server as a daemon process"""
    # Check if already running
    pid = read_pid_file()
    if pid and is_process_running(pid):
        logger.info(f"Proxy already running with PID {pid}")
        return
    
    # Check if the port is available
    if is_port_in_use(PORT):
        logger.error(f"Port {PORT} already in use")
        return
    
    # Create and start the server
    write_pid_file()
    
    server = http.server.ThreadingHTTPServer(
        ('', PORT), 
        ProxyHTTPRequestHandler
    )
    
    logger.info(f"Port proxy started on port {PORT} forwarding to port {TARGET_PORT}")
    
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        logger.info("Stopping proxy server")
    finally:
        server.server_close()

def stop_proxy():
    """Stop a running proxy server"""
    pid = read_pid_file()
    if pid:
        if is_process_running(pid):
            logger.info(f"Stopping proxy server with PID {pid}")
            try:
                os.kill(pid, signal.SIGTERM)
                # Wait for the process to terminate
                for _ in range(10):
                    if not is_process_running(pid):
                        break
                    time.sleep(0.1)
                else:
                    logger.warning("Process did not terminate, sending SIGKILL")
                    os.kill(pid, signal.SIGKILL)
                logger.info("Proxy server stopped")
            except (OSError, ProcessLookupError):
                logger.warning("Process already terminated")
        else:
            logger.info("Process not running, cleaning up PID file")
        
        # Clean up PID file
        if os.path.exists(PID_FILE):
            os.remove(PID_FILE)
    else:
        logger.info("No PID file found, proxy not running")

def check_status():
    """Check if the proxy server is running"""
    pid = read_pid_file()
    if pid and is_process_running(pid):
        logger.info(f"Proxy server is running with PID {pid}")
        return True
    else:
        if pid:
            logger.info("Proxy server is not running (stale PID file)")
            if os.path.exists(PID_FILE):
                os.remove(PID_FILE)
        else:
            logger.info("Proxy server is not running")
        return False

if __name__ == "__main__":
    command = sys.argv[1] if len(sys.argv) > 1 else "start"
    
    if command == "start":
        logger.info("Starting port proxy service...")
        start_proxy()
    elif command == "stop":
        logger.info("Stopping port proxy service...")
        stop_proxy()
    elif command == "status":
        check_status()
    else:
        logger.error(f"Unknown command: {command}")
        print(f"Usage: {sys.argv[0]} [start|stop|status]")
        sys.exit(1)