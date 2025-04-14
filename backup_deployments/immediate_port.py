"""
Immediate port opener for Replit with instant startup.
This is designed to be imported by gunicorn.conf.py or run standalone.
"""
import socket
import threading
import subprocess
import time
import os
import sys
import http.server
import socketserver
from http.server import BaseHTTPRequestHandler
import signal

# Set up the port that Replit is looking for
PORT = 5000  
SOCKET_TIMEOUT = 120  # How long to keep the socket open before giving up (seconds)

# Keep track of whether we've already opened the port
port_opened = False
immediate_socket = None

def signal_handler(sig, frame):
    """Handle Ctrl+C gracefully"""
    print("Shutting down immediate port opener...")
    if immediate_socket:
        try:
            immediate_socket.close()
        except:
            pass
    sys.exit(0)

# Register the signal handler
signal.signal(signal.SIGINT, signal_handler)

class FastHandler(BaseHTTPRequestHandler):
    """Ultra minimal HTTP handler for quick responses"""
    def log_message(self, format, *args):
        """Disable logging for performance"""
        return
        
    def do_GET(self):
        """Respond to GET requests with a simple loading page"""
        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers()
        self.wfile.write(b"""
        <html>
        <head>
            <title>Application Starting</title>
            <style>
                body { font-family: Arial, sans-serif; background-color: #f5f5f5; text-align: center; padding-top: 100px; }
                .loader { border: 8px solid #f3f3f3; border-top: 8px solid #3498db; border-radius: 50%; width: 50px; height: 50px; animation: spin 1s linear infinite; margin: 0 auto; }
                @keyframes spin { 0% { transform: rotate(0deg); } 100% { transform: rotate(360deg); } }
                h1 { color: #333; }
            </style>
            <meta http-equiv="refresh" content="2">
        </head>
        <body>
            <h1>Application is starting...</h1>
            <p>This may take a few moments. Thank you for your patience.</p>
            <div class="loader"></div>
        </body>
        </html>
        """)
    
    def do_POST(self):
        """Respond to POST requests with a service unavailable message"""
        self.send_response(503)
        self.send_header('Content-type', 'text/plain')
        self.end_headers()
        self.wfile.write(b"Application is starting, please try again shortly.")

def open_port_immediately():
    """Open the port as quickly as possible and keep it open"""
    global port_opened, immediate_socket
    
    if port_opened:
        return
    
    try:
        # Use a simple HTTP server - faster than manual socket management
        print(f"Opening port {PORT} immediately for Replit detection...")
        sys.stdout.flush()
        
        server = socketserver.TCPServer(("0.0.0.0", PORT), FastHandler)
        server.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        
        # Store the socket globally
        immediate_socket = server.socket
        
        # Mark that we've opened the port
        port_opened = True
        
        # Print success message
        print(f"PORT {PORT} OPEN - Replit should detect this immediately")
        sys.stdout.flush()
        
        # Set a timeout for the server
        start_time = time.time()
        
        # Run the server for a limited time or until Ctrl+C
        while time.time() - start_time < SOCKET_TIMEOUT:
            server.handle_request()
            
    except (OSError, socket.error) as e:
        # Most likely the port is already in use by the real application
        if "Address already in use" in str(e):
            print(f"Port {PORT} is already in use - application may already be running")
        else:
            print(f"Error opening port {PORT}: {e}")
        sys.stdout.flush()

# For standalone execution
if __name__ == "__main__":
    # Run in the main thread - we don't need to return control immediately
    open_port_immediately()
    
    # If the timeout expires, exit normally
    print("Immediate port opener finished - application should be fully started")
    sys.exit(0)