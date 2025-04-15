#!/usr/bin/env python3
"""
Dual port binding solution for Replit deployments.
This script runs a single Flask application that listens on both port 5000 and port 8080.
"""
import os
import socket
import signal
import sys
import logging
import threading
import time
from werkzeug.serving import make_server
from main import app

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('dual_bind_server')

class ServerThread(threading.Thread):
    """Thread class to run a Flask server in the background"""
    def __init__(self, app, host, port):
        """Initialize with Flask app and server parameters"""
        threading.Thread.__init__(self)
        self.host = host
        self.port = port
        logger.info(f"Creating server on {host}:{port}")
        try:
            self.srv = make_server(host, port, app)
            self.ctx = app.app_context()
            self.ctx.push()
            logger.info(f"Server created successfully on {host}:{port}")
        except Exception as e:
            logger.error(f"Error creating server on {host}:{port}: {str(e)}")
            raise

    def run(self):
        """Start the server"""
        logger.info(f"Starting server on {self.host}:{self.port}")
        try:
            self.srv.serve_forever()
        except Exception as e:
            logger.error(f"Error in server on {self.host}:{self.port}: {str(e)}")

    def shutdown(self):
        """Shutdown the server"""
        logger.info(f"Shutting down server on {self.host}:{self.port}")
        try:
            self.srv.shutdown()
        except Exception as e:
            logger.error(f"Error shutting down server on {self.host}:{self.port}: {str(e)}")

def check_port_in_use(port):
    """Check if a port is already in use"""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex(('localhost', port)) == 0

def main():
    """Start the dual port binding server"""
    # List to store threads for cleanup
    server_threads = []

    try:
        # Check if ports are already in use
        for port in [5000, 8080]:
            if check_port_in_use(port):
                logger.warning(f"Port {port} is already in use. Skipping.")
            else:
                # Create and start server on this port
                server_thread = ServerThread(app, '0.0.0.0', port)
                server_thread.daemon = True
                server_thread.start()
                server_threads.append((port, server_thread))
                logger.info(f"Server thread started on port {port}")

        if not server_threads:
            logger.error("Could not start any servers. All ports are in use.")
            return

        # Log success message
        ports_str = ', '.join(str(port) for port, _ in server_threads)
        logger.info(f"Server is running on ports: {ports_str}")
        print(f"Server is running on ports: {ports_str}")

        # Keep the main thread alive
        while True:
            time.sleep(1)

    except KeyboardInterrupt:
        logger.info("Shutdown requested (KeyboardInterrupt)")
    except Exception as e:
        logger.error(f"Error in server: {str(e)}")
    finally:
        # Shutdown all servers
        for port, thread in server_threads:
            try:
                logger.info(f"Shutting down server on port {port}")
                thread.shutdown()
            except Exception as e:
                logger.error(f"Error shutting down server on port {port}: {str(e)}")

def signal_handler(sig, frame):
    """Handle signals gracefully"""
    logger.info(f"Received signal {sig}. Shutting down.")
    sys.exit(0)

if __name__ == "__main__":
    # Register signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Start the server
    main()