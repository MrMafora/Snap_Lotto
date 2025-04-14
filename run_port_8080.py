"""
Simple TCP server that binds to port 8080 and redirects requests to port 5000
"""
import socket
import threading
import time

def handle_connection(client_socket):
    """Handle incoming connection by sending a redirect to port 5000"""
    try:
        # Receive the request (we don't need to parse it)
        request = client_socket.recv(1024)
        
        # Send a redirect response
        response = (
            b"HTTP/1.1 302 Found\r\n"
            b"Location: http://localhost:5000/\r\n"
            b"Connection: close\r\n\r\n"
        )
        client_socket.sendall(response)
    except Exception as e:
        print(f"Error handling connection: {e}")
    finally:
        client_socket.close()

def run_server():
    """Run a simple TCP server on port 8080"""
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    
    try:
        server.bind(('0.0.0.0', 8080))
        server.listen(5)
        print(f"Server listening on port 8080")
        
        while True:
            client, addr = server.accept()
            print(f"Connection from {addr}")
            thread = threading.Thread(target=handle_connection, args=(client,))
            thread.daemon = True
            thread.start()
    except Exception as e:
        print(f"Server error: {e}")
    finally:
        server.close()

if __name__ == "__main__":
    print("Starting port 8080 server...")
    run_server()