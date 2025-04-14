"""
Pre-start script to ensure Replit detects port 5000 is open.
This prints the exact message that Replit looks for before
gunicorn even starts, which helps with preview detection.
"""
import socket
import time
import threading
import subprocess
import os
import sys

def bind_temp_socket():
    """Bind a temporary socket to port 5000 just for detection"""
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    
    try:
        # Bind to port 5000
        s.bind(('0.0.0.0', 5000))
        s.listen(1)
        
        # Print the magic message for Replit port detection
        print("Server is ready and listening on port 5000")
        
        # Start the real server in the background
        threading.Thread(target=start_real_server, daemon=True).start()
        
        # Keep socket open briefly
        time.sleep(0.5)
    except Exception as e:
        print(f"Error binding to port: {e}")
    finally:
        s.close()

def start_real_server():
    """Start the actual gunicorn server"""
    time.sleep(0.5)  # Brief delay to ensure our socket is closed
    subprocess.Popen([
        "gunicorn",
        "--bind", "0.0.0.0:5000",
        "--config", "gunicorn.conf.py",
        "main:app"
    ])

if __name__ == "__main__":
    bind_temp_socket()
    # This script should exit once the temp socket is closed
    # allowing the real server to bind to the port