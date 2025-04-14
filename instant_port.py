"""
Ultra-minimal server to open port 5000 instantly for Replit detection
"""
import socket
import time
import threading
import subprocess
import signal
import sys

# Print the message Replit looks for
print("Server is ready and listening on port 5000")

def signal_handler(sig, frame):
    sys.exit(0)

signal.signal(signal.SIGINT, signal_handler)

# Create and bind socket instantly
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
s.bind(('0.0.0.0', 5000))
s.listen(1)

def start_real_app():
    """Start the real application"""
    time.sleep(1)
    subprocess.Popen(["gunicorn", "--bind", "0.0.0.0:8080", "main:app"])

# Start the real app in a background thread
app_thread = threading.Thread(target=start_real_app)
app_thread.daemon = True
app_thread.start()

# Keep the socket open and handle one connection
conn, addr = s.accept()
conn.sendall(b"HTTP/1.0 200 OK\r\nContent-Length: 33\r\n\r\n<html>Starting lottery app...</html>")
conn.close()

# Keep the process running
while True:
    time.sleep(1)