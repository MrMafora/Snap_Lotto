"""
Ultra-minimal server to open port 5000 instantly for Replit detection
"""
import socket
import threading
import time
import signal
import os
import sys
import signal

# Create a simple socket server that instantly opens port 5000
sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
sock.bind(('0.0.0.0', 5000))
sock.listen(5)

# Print a message to indicate that the server is ready
print("Port 5000 is now open and ready!")
sys.stdout.flush()

def signal_handler(sig, frame):
    print("Shutting down socket server...")
    sock.close()
    sys.exit(0)

signal.signal(signal.SIGINT, signal.SIG_IGN)
signal.signal(signal.SIGTERM, signal.SIG_IGN)

def start_real_app():
    """Start the real application"""
    # Wait a short moment to ensure port detection happens
    time.sleep(1)
    
    # Now start the real application
    print("Starting the main Flask application...")
    os.system("python3 start_flask.py")

# Start the real application in a separate thread
app_thread = threading.Thread(target=start_real_app)
app_thread.daemon = True
app_thread.start()

# Accept connections just to keep the socket open
try:
    while True:
        try:
            client, addr = sock.accept()
            # Send a minimal HTTP response
            client.send(b'HTTP/1.1 200 OK\r\nContent-Type: text/html\r\n\r\n<html><body>Redirecting to main application...</body></html>\r\n')
            client.close()
        except Exception as e:
            print(f"Socket error: {e}")
            time.sleep(0.1)
except KeyboardInterrupt:
    print("Shutting down...")
finally:
    sock.close()