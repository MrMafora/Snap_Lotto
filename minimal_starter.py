"""
Extremely minimal socket server to open port 5000 instantly
"""
import socket
import threading
import time
import os
import sys

# Create a listening socket on port 5000 that opens instantly
server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
server_socket.bind(('0.0.0.0', 5000))
server_socket.listen(5)

# Print message immediately to let Replit know port is open
print("Port 5000 is now open and listening!")
sys.stdout.flush()

def start_real_app():
    """Start the real app after a delay"""
    time.sleep(0.5)  # Wait briefly to ensure port detection happens
    
    print("Starting the real Flask application...")
    
    # Modify main.py to run on a different port (temporarily)
    original_main = None
    with open('main.py', 'r') as f:
        original_main = f.read()
    
    # Check if we need to modify the port
    if "port=5000" in original_main and "port=8080" not in original_main:
        try:
            modified_main = original_main.replace(
                "app.run(host=\"0.0.0.0\", port=5000", 
                "app.run(host=\"0.0.0.0\", port=8080"
            )
            
            with open('main.py', 'w') as f:
                f.write(modified_main)
                
            # Start the application
            os.system("python main.py &")
            
            # Wait a moment for the app to initialize
            time.sleep(5)
            
            # Restore the original main.py
            with open('main.py', 'w') as f:
                f.write(original_main)
                
        except Exception as e:
            print(f"Error modifying main.py: {e}")
            
            # Restore the original main.py if it exists
            if original_main:
                with open('main.py', 'w') as f:
                    f.write(original_main)
    else:
        # Just run on the configured port
        os.system("python main.py &")

# Start the real application in a separate thread
app_thread = threading.Thread(target=start_real_app)
app_thread.daemon = True
app_thread.start()

# Accept connections on port 5000 and redirect to port 8080
print("Accepting connections and redirecting to the main application...")
try:
    while True:
        client_socket, address = server_socket.accept()
        try:
            # Send simple 302 redirect to port 8080
            response = (
                "HTTP/1.1 302 Found\r\n"
                "Location: http://0.0.0.0:8080/\r\n"
                "Content-Type: text/html\r\n"
                "\r\n"
                "<html><body>Redirecting to main application...</body></html>\r\n"
            )
            client_socket.sendall(response.encode())
            client_socket.close()
        except Exception as e:
            print(f"Error handling client: {e}")
except KeyboardInterrupt:
    print("Shutting down...")
finally:
    server_socket.close()