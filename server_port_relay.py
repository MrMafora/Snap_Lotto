#!/usr/bin/env python3
"""
Port relay script that forwards requests from port 8080 to port 5000
This script should be run in the background to ensure the application
is accessible from the expected 8080 port
"""
import socket
import threading
import time
import signal
import sys
import os
import logging

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('port_relay')

# Configuration
SOURCE_PORT = 8080
DESTINATION_PORT = 5000
BUFFER_SIZE = 8192
MAX_CONNECTIONS = 50

def create_pid_file():
    """Create a PID file for the proxy process"""
    with open('port_relay.pid', 'w') as f:
        f.write(str(os.getpid()))
    logger.info(f"PID file created with PID {os.getpid()}")

def remove_pid_file():
    """Remove the PID file on exit"""
    try:
        os.remove('port_relay.pid')
        logger.info("PID file removed")
    except FileNotFoundError:
        pass

def handle_client(client_socket):
    """Handle a client connection by forwarding to the destination"""
    try:
        # Connect to destination server
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_socket.connect(('localhost', DESTINATION_PORT))
        
        # Create threads to forward data in both directions
        client_to_server = threading.Thread(
            target=forward_data,
            args=(client_socket, server_socket, "Client -> Server"),
        )
        server_to_client = threading.Thread(
            target=forward_data,
            args=(server_socket, client_socket, "Server -> Client"),
        )
        
        # Start forwarding threads
        client_to_server.daemon = True
        server_to_client.daemon = True
        client_to_server.start()
        server_to_client.start()
        
        # Wait for threads to complete
        client_to_server.join()
        server_to_client.join()
    except Exception as e:
        logger.error(f"Error handling client: {e}")
    finally:
        # Clean up sockets
        try:
            client_socket.close()
        except:
            pass
        try:
            server_socket.close()
        except:
            pass

def forward_data(source, destination, direction):
    """Forward data from source to destination socket"""
    try:
        while True:
            data = source.recv(BUFFER_SIZE)
            if not data:
                # Connection closed
                break
            destination.sendall(data)
    except:
        # Silently close the connection
        pass

def check_destination_reachable():
    """Check if the destination server is running"""
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(1)
        result = sock.connect_ex(('localhost', DESTINATION_PORT))
        sock.close()
        return result == 0
    except:
        return False

def start_proxy():
    """Start the port forwarding proxy server"""
    # Create a server socket
    proxy_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    proxy_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    
    try:
        # Bind to the source port
        proxy_socket.bind(('0.0.0.0', SOURCE_PORT))
        proxy_socket.listen(MAX_CONNECTIONS)
        logger.info(f"Proxy server started: 0.0.0.0:{SOURCE_PORT} -> localhost:{DESTINATION_PORT}")
        
        # Create PID file
        create_pid_file()
        
        # Handle incoming connections
        while True:
            try:
                client_socket, client_address = proxy_socket.accept()
                logger.debug(f"Accepted connection from {client_address}")
                
                # Handle client in a new thread
                client_thread = threading.Thread(target=handle_client, args=(client_socket,))
                client_thread.daemon = True
                client_thread.start()
            except Exception as e:
                logger.error(f"Error accepting connection: {e}")
    except KeyboardInterrupt:
        logger.info("Proxy server stopping...")
    except Exception as e:
        logger.error(f"Error starting proxy server: {e}")
    finally:
        # Clean up
        proxy_socket.close()
        remove_pid_file()
        logger.info("Proxy server stopped")

def wait_for_destination():
    """Wait for the destination server to start"""
    logger.info(f"Waiting for destination server on port {DESTINATION_PORT}...")
    retry_count = 0
    max_retries = 30  # Wait up to 30 seconds
    
    while retry_count < max_retries:
        if check_destination_reachable():
            logger.info(f"Destination server is now running on port {DESTINATION_PORT}")
            return True
        
        time.sleep(1)
        retry_count += 1
    
    logger.error(f"Destination server not available after {max_retries} seconds")
    return False

def handle_signal(signum, frame):
    """Handle termination signals"""
    if signum in (signal.SIGINT, signal.SIGTERM):
        logger.info(f"Received signal {signum}. Shutting down...")
        # The finally block in start_proxy will handle cleanup
        sys.exit(0)

if __name__ == "__main__":
    # Register signal handlers
    signal.signal(signal.SIGINT, handle_signal)
    signal.signal(signal.SIGTERM, handle_signal)
    
    # Wait for the destination server to be available
    if wait_for_destination():
        # Start the proxy
        start_proxy()
    else:
        logger.error("Exiting due to destination server unavailability")
        sys.exit(1)