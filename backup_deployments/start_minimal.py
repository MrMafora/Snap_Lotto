"""
Extremely minimal socket server to open port 5000 instantly
"""
import socket
import threading
import time
import signal
import os
import sys

print("Initializing minimal server for Replit port detection...")
sys.stdout.flush()

# Step 1: Create basic socket on port 5000 to instantly satisfy Replit's port detection
sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
try:
    sock.bind(('0.0.0.0', 5000))
    sock.listen(5)
    print("Port 5000 is now open and ready!")
    sys.stdout.flush()
except Exception as e:
    print(f"Error binding to port 5000: {e}")
    sys.exit(1)

def start_real_app():
    """Start the real application"""
    time.sleep(2)  # Wait for Replit to detect the port
    
    # Close our temporary socket (optional)
    print("Starting the main application...")
    
    # Attempt to close the temporary socket
    try:
        sock.close()
    except:
        pass
    
    # Start the actual application
    os.system("python3 main.py")

# Start the real application in a separate thread
app_thread = threading.Thread(target=start_real_app)
app_thread.daemon = True
app_thread.start()

# Keep the main thread alive with a minimal HTTP server
try:
    while True:
        try:
            client, addr = sock.accept()
            client.send(b'HTTP/1.1 200 OK\r\nContent-Type: text/html\r\n\r\n<html><body>Initializing application, please wait...</body></html>')
            client.close()
        except:
            # Socket may have been closed by the real app
            time.sleep(0.5)
            break
except KeyboardInterrupt:
    print("Shutting down...")
finally:
    try:
        sock.close()
    except:
        pass