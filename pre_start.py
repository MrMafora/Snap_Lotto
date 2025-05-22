"""
Pre-start script for Replit port detection.
Run this file immediately before starting gunicorn to ensure port 5000 is detected.

Usage: python pre_start.py
"""
import sys
import subprocess
import threading
import time

def start_port_opener():
    """Start the immediate port opener in a separate process"""
    try:
        subprocess.Popen(["python", "immediate_port.py"])
        print("Started immediate port opener for Replit detection")
    except Exception as e:
        print(f"Failed to start port opener: {e}")
        
def check_gunicorn():
    """Check if gunicorn is already running and kill it if needed"""
    try:
        subprocess.run(["pkill", "-f", "gunicorn"], stderr=subprocess.DEVNULL)
        print("Killed any existing gunicorn processes")
    except:
        print("No existing gunicorn processes found")
    
if __name__ == "__main__":
    # Kill any existing gunicorn processes
    check_gunicorn()
    
    # Start the port opener (don't wait for it to finish)
    start_port_opener()
    
    # Wait a moment for the port opener to start
    print("Waiting for port opener to initialize...")
    time.sleep(1)
    
    print("Pre-start completed, ready for gunicorn")
    sys.exit(0)  # Exit with success code