#!/usr/bin/env python3
"""
Direct port binding solution for the lottery application.

This script can run the application directly on:
1. Single port mode: port 5000 (development) or port 8080 (production)
2. Dual port mode: both port 5000 and 8080 simultaneously

It replaces the need for separate scripts and bridges by using ThreadingMixIn
to handle multiple ports simultaneously.
"""
import os
import sys
import signal
import time
import logging
import threading
import socket
import http.server
import socketserver
import urllib.request
import urllib.error
import argparse
import subprocess

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('direct_port_binding.log')
    ]
)
logger = logging.getLogger('direct_port_binding')

# Constants
PORT_5000 = 5000
PORT_8080 = 8080
DEFAULT_HOST = "0.0.0.0"
LOCAL_HOST = "127.0.0.1"
MAIN_APP = "main:app"

def check_port_available(port, host=DEFAULT_HOST):
    """Check if a port is available for binding"""
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.bind((host, port))
            return True
    except OSError:
        return False

def check_port_responsive(port, host=LOCAL_HOST, path="/health_check", timeout=2):
    """Check if a port is already running a responsive application"""
    try:
        url = f"http://{host}:{port}{path}"
        with urllib.request.urlopen(url, timeout=timeout) as response:
            return response.status == 200
    except Exception:
        return False

def clear_port(port):
    """Attempt to clear a port by killing any processes using it"""
    if sys.platform.startswith('win'):
        # Windows
        subprocess.run(f"FOR /F \"tokens=5\" %P IN ('netstat -a -n -o | findstr :{port}') DO taskkill /F /PID %P", 
                      shell=True)
    else:
        # Linux/Mac
        try:
            # Try using lsof
            pids = subprocess.check_output(f"lsof -ti:{port}", shell=True, stderr=subprocess.DEVNULL)
            for pid in pids.decode().strip().split('\n'):
                if pid:
                    subprocess.run(f"kill -9 {pid}", shell=True)
        except subprocess.CalledProcessError:
            # lsof not available, try alternative method
            pass

def run_gunicorn_process(port, app=MAIN_APP, workers=4, log_file=None):
    """Run Gunicorn on the specified port"""
    cmd = [
        "gunicorn",
        "--bind", f"{DEFAULT_HOST}:{port}",
        "--workers", str(workers),
        "--timeout", "120",
        "--reload",
        "--reuse-port",
        app
    ]
    
    if log_file:
        with open(log_file, 'w') as f:
            process = subprocess.Popen(cmd, stdout=f, stderr=f)
    else:
        process = subprocess.Popen(cmd)
    
    # Give it time to start
    time.sleep(2)
    
    # Check if the process is running
    if process.poll() is None:
        logger.info(f"Gunicorn started on port {port} (PID: {process.pid})")
        return process
    else:
        logger.error(f"Failed to start Gunicorn on port {port}")
        return None

class PortProxy(http.server.BaseHTTPRequestHandler):
    """HTTP request handler that forwards requests to a target port"""
    target_port = PORT_5000  # Default target port
    
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
        target_url = f"http://{LOCAL_HOST}:{self.target_port}{self.path}"
        
        # Get request headers
        headers = {}
        for header in self.headers:
            headers[header] = self.headers[header]
        
        # Special handling for host header
        headers['Host'] = f"{LOCAL_HOST}:{self.target_port}"
        
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

class ThreadedHTTPServer(socketserver.ThreadingMixIn, http.server.HTTPServer):
    """Threaded HTTP server to handle concurrent requests"""
    pass

def run_proxy_server(source_port, target_port):
    """Run a proxy server that forwards from source_port to target_port"""
    # Create a custom handler with the specified target port that inherits from PortProxy
    # We need to define the target_port as a class variable to make it available to handler methods
    handler_target_port = target_port  # Store the target port in a local variable
    
    # Create a custom class that adds the target_port attribute
    class CustomPortProxy(PortProxy):
        # Set the class attribute
        target_port = handler_target_port
    
    try:
        # Start server in a thread
        server = ThreadedHTTPServer((DEFAULT_HOST, source_port), CustomPortProxy)
        server_thread = threading.Thread(target=server.serve_forever, daemon=True)
        server_thread.start()
        logger.info(f"Started proxy on port {source_port} forwarding to port {target_port}")
        return server, server_thread
    except Exception as e:
        logger.error(f"Failed to start proxy on port {source_port}: {str(e)}")
        return None, None

def run_dual_port_mode():
    """Run the application on port 5000 with a proxy on port 8080"""
    logger.info("Starting in dual port mode...")
    
    # Clear both ports to ensure they're available
    if not check_port_available(PORT_5000):
        logger.info(f"Port {PORT_5000} is in use, attempting to clear...")
        clear_port(PORT_5000)
    
    if not check_port_available(PORT_8080):
        logger.info(f"Port {PORT_8080} is in use, attempting to clear...")
        clear_port(PORT_8080)
    
    # Start the primary application on port 5000
    primary_process = run_gunicorn_process(PORT_5000, log_file="gunicorn_5000.log")
    if not primary_process:
        logger.error("Failed to start the primary application on port 5000")
        return False
    
    # Wait a moment to make sure the app is running
    time.sleep(3)
    
    # Start the proxy server on port 8080 forwarding to 5000
    proxy_server, proxy_thread = run_proxy_server(PORT_8080, PORT_5000)
    if not proxy_server:
        logger.error("Failed to start the proxy server on port 8080")
        primary_process.terminate()
        return False
    
    logger.info("Dual port mode is running:")
    logger.info(f"  - Primary: port {PORT_5000} (PID: {primary_process.pid})")
    logger.info(f"  - Bridge: port {PORT_8080} -> {PORT_5000}")
    
    try:
        # Keep the main thread alive
        while True:
            # Check if the primary process is still running
            if primary_process.poll() is not None:
                logger.error("Primary process has stopped, shutting down...")
                break
            
            # Check if proxy thread is still alive (handle case where proxy_thread might be None)
            if proxy_thread is None or not proxy_thread.is_alive():
                logger.error("Proxy thread has stopped or was not properly started, shutting down...")
                break
            
            time.sleep(1)
    except KeyboardInterrupt:
        logger.info("Received KeyboardInterrupt, shutting down...")
    finally:
        # Shutdown
        logger.info("Shutting down...")
        if proxy_server:
            proxy_server.shutdown()
        if primary_process and primary_process.poll() is None:
            primary_process.terminate()
    
    logger.info("Dual port mode has been shut down")
    return True

def run_single_port_mode(port):
    """Run the application directly on the specified port"""
    logger.info(f"Starting in single port mode on port {port}...")
    
    # Clear the port to ensure it's available
    if not check_port_available(port):
        logger.info(f"Port {port} is in use, attempting to clear...")
        clear_port(port)
    
    # Start the application on the specified port
    process = run_gunicorn_process(port, log_file=f"gunicorn_{port}.log")
    if not process:
        logger.error(f"Failed to start the application on port {port}")
        return False
    
    logger.info(f"Application is running on port {port} (PID: {process.pid})")
    
    try:
        # Keep the main thread alive
        while True:
            # Check if the process is still running
            if process.poll() is not None:
                logger.error("Process has stopped, shutting down...")
                break
            
            time.sleep(1)
    except KeyboardInterrupt:
        logger.info("Received KeyboardInterrupt, shutting down...")
    finally:
        # Shutdown
        logger.info("Shutting down...")
        if process and process.poll() is None:
            process.terminate()
    
    logger.info("Single port mode has been shut down")
    return True

def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description='Direct port binding for the lottery application')
    parser.add_argument('--mode', choices=['auto', 'single', 'dual'], default='auto',
                      help='Running mode (auto, single, or dual)')
    parser.add_argument('--port', type=int, default=None,
                      help='Port to use in single mode (default: 5000 for development, 8080 for production)')
    parser.add_argument('--environment', choices=['development', 'production'], default=None,
                      help='Application environment (development or production)')
    args = parser.parse_args()
    
    # Determine environment
    env = args.environment if args.environment else os.environ.get('ENVIRONMENT', 'development')
    
    # Determine port and mode based on environment and arguments
    if args.mode == 'auto':
        if env.lower() == 'production':
            # Production: run on port 8080
            port = PORT_8080
            mode = 'single'
        else:
            # Development: dual port (primary 5000, bridge to 8080)
            mode = 'dual'
            port = PORT_5000
    else:
        # Explicit mode
        mode = args.mode
        if args.port:
            port = args.port
        elif env.lower() == 'production':
            port = PORT_8080
        else:
            port = PORT_5000
    
    logger.info(f"Starting with environment: {env}, mode: {mode}, port: {port if mode == 'single' else 'dual'}")
    
    # Set environment variable for child processes
    os.environ['ENVIRONMENT'] = env
    
    # Run in the specified mode
    if mode == 'dual':
        return run_dual_port_mode()
    else:
        return run_single_port_mode(port)

if __name__ == "__main__":
    sys.exit(0 if main() else 1)