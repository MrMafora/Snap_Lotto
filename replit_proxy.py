#!/usr/bin/env python3
"""
Replit-specific proxy server that forwards all requests from port 8080 to port 5000.
This implementation uses a reverse proxy approach rather than redirects to maintain
compatibility with Replit's environment.
"""
import socket
import select
import threading
import time
import logging
import sys
import os

# Configure logging to both console and file
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('replit_proxy.log')
    ]
)
logger = logging.getLogger('replit_proxy')

class ProxyServer:
    """
    A simple TCP proxy server that forwards requests from port 8080 to port 5000.
    """
    def __init__(self, listen_addr=('0.0.0.0', 8080), target_addr=('127.0.0.1', 5000)):
        self.listen_addr = listen_addr
        self.target_addr = target_addr
        self.connections = []
        self.running = False
        
    def start(self):
        """Start the proxy server"""
        try:
            # Create the server socket
            self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.server.bind(self.listen_addr)
            self.server.listen(5)
            self.server.setblocking(0)
            
            logger.info(f"Proxy server started on {self.listen_addr[0]}:{self.listen_addr[1]}")
            logger.info(f"Forwarding all traffic to {self.target_addr[0]}:{self.target_addr[1]}")
            
            self.connections = [self.server]
            self.running = True
            
            # Main server loop
            while self.running:
                # Use select to efficiently wait for socket events
                readable, _, exceptional = select.select(self.connections, [], self.connections, 1)
                
                for sock in readable:
                    # New connection request on the server socket
                    if sock is self.server:
                        self._accept_connection()
                    # Data received on an existing connection
                    else:
                        self._handle_connection(sock)
                        
                # Handle exceptional conditions
                for sock in exceptional:
                    logger.warning(f"Exceptional condition on {sock.getpeername()}")
                    self.connections.remove(sock)
                    sock.close()
            
        except Exception as e:
            logger.error(f"Error in proxy server: {str(e)}")
            self.stop()
            return False
        return True
    
    def _accept_connection(self):
        """Accept a new client connection"""
        try:
            client_sock, client_addr = self.server.accept()
            logger.info(f"New connection from {client_addr[0]}:{client_addr[1]}")
            
            # Connect to the target server
            try:
                target_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                target_sock.connect(self.target_addr)
                
                # Set both sockets to non-blocking mode
                client_sock.setblocking(0)
                target_sock.setblocking(0)
                
                # Add both sockets to the connections list
                self.connections.append(client_sock)
                self.connections.append(target_sock)
                
                # Start two threads to forward data in both directions
                threading.Thread(target=self._forward_data, 
                                 args=(client_sock, target_sock, "client to target"),
                                 daemon=True).start()
                
                threading.Thread(target=self._forward_data, 
                                 args=(target_sock, client_sock, "target to client"),
                                 daemon=True).start()
                
            except Exception as e:
                logger.error(f"Failed to connect to target: {str(e)}")
                client_sock.close()
        except Exception as e:
            logger.error(f"Error accepting connection: {str(e)}")
    
    def _handle_connection(self, sock):
        """Handle data on an existing connection"""
        try:
            # Try to receive data from the socket
            data = sock.recv(4096)
            if data:
                # Find the other socket in the connection pair
                for connection in self.connections:
                    if connection != self.server and connection != sock:
                        try:
                            connection.send(data)
                        except Exception as e:
                            logger.error(f"Error forwarding data: {str(e)}")
                            connection.close()
                            self.connections.remove(connection)
            else:
                # Connection closed
                if sock in self.connections:
                    self.connections.remove(sock)
                sock.close()
        except Exception as e:
            logger.error(f"Error handling connection: {str(e)}")
            if sock in self.connections:
                self.connections.remove(sock)
            sock.close()
    
    def _forward_data(self, source, destination, direction):
        """Forward data from source to destination"""
        try:
            while self.running:
                try:
                    data = source.recv(4096)
                    if not data:
                        break
                    destination.sendall(data)
                    logger.debug(f"Forwarded {len(data)} bytes {direction}")
                except (ConnectionResetError, BrokenPipeError):
                    break
                except socket.error:
                    time.sleep(0.1)  # Brief pause to prevent high CPU usage
        except Exception as e:
            logger.error(f"Error in data forwarding ({direction}): {str(e)}")
        finally:
            logger.info(f"Closing connection ({direction})")
            try:
                source.close()
                destination.close()
            except:
                pass
            
            # Remove from connections list if still present
            if source in self.connections:
                self.connections.remove(source)
            if destination in self.connections:
                self.connections.remove(destination)
    
    def stop(self):
        """Stop the proxy server and clean up connections"""
        logger.info("Stopping proxy server")
        self.running = False
        
        # Close all connections
        for conn in self.connections:
            try:
                conn.close()
            except:
                pass
        
        # Clear connections list
        self.connections = []

def main():
    """Main function to run the proxy server"""
    try:
        # Create and start the proxy server
        proxy = ProxyServer()
        proxy.start()
    except KeyboardInterrupt:
        logger.info("Proxy server stopped by user")
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
    finally:
        sys.exit(0)

if __name__ == "__main__":
    main()