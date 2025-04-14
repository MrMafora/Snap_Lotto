"""
DUAL PORT APPLICATION RUNNER FOR REPLIT

This script starts both the main Flask application on port 5000
and a minimal HTTP server on port 8080 that redirects to port 5000.
"""
import http.server
import socketserver
import threading
import time
import logging
import sys
import os
import signal
import subprocess

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)

class RedirectHandler(http.server.BaseHTTPRequestHandler):
    """Handler that redirects all requests to port 5000"""
    def redirect_request(self):
        """Send a redirect to the same path on port 5000"""
        self.send_response(302)
        host = self.headers.get('Host', '')
        redirect_host = host.replace(':8080', ':5000') if ':8080' in host else host
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
        if args and (500 <= int(args[1]) < 600):
            logger.error(f"Error %s - %s", self.path, args[1])

def start_port_8080_server():
    """Start the HTTP server on port 8080"""
    try:
        # Create the HTTP server
        logger.info("Starting HTTP server on port 8080")
        server = socketserver.TCPServer(("0.0.0.0", 8080), RedirectHandler)
        server.daemon_threads = True
        
        # Run the server in a daemon thread
        server_thread = threading.Thread(target=server.serve_forever)
        server_thread.daemon = True
        server_thread.start()
        
        logger.info("Server started on port 8080")
        return True
    except Exception as e:
        logger.error(f"Error starting server on port 8080: {e}")
        return False

def start_main_application():
    """Start the main Flask application using Gunicorn"""
    try:
        logger.info("Starting main application on port 5000")
        gunicorn_cmd = [
            "gunicorn",
            "--bind", "0.0.0.0:5000",
            "--reuse-port",
            "--reload",
            "main:app"
        ]
        # Start Gunicorn process
        process = subprocess.Popen(
            gunicorn_cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            universal_newlines=True
        )
        
        # Monitor Gunicorn output in a separate thread
        def monitor_output():
            for line in process.stdout:
                logger.info(f"Gunicorn: {line.strip()}")
        
        output_thread = threading.Thread(target=monitor_output)
        output_thread.daemon = True
        output_thread.start()
        
        logger.info("Main application started on port 5000")
        return process
    except Exception as e:
        logger.error(f"Error starting main application: {e}")
        return None

if __name__ == "__main__":
    logger.info("Starting dual port application runner")
    
    # Start the port 8080 server
    if not start_port_8080_server():
        logger.error("Failed to start port 8080 server")
        sys.exit(1)
    
    # Start the main application
    main_app_process = start_main_application()
    if not main_app_process:
        logger.error("Failed to start main application")
        sys.exit(1)
    
    logger.info("Server is ready and listening on ports 5000 and 8080")
    
    try:
        # Keep the main thread alive and monitor the main application process
        while True:
            if main_app_process.poll() is not None:
                logger.error("Main application process exited with code %d", main_app_process.returncode)
                sys.exit(1)
            time.sleep(5)
    except KeyboardInterrupt:
        logger.info("Shutting down...")
        if main_app_process:
            main_app_process.terminate()
        sys.exit(0)