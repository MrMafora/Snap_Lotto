#!/usr/bin/env python3
import os
import subprocess
import time
import signal
import sys

def main():
    """
    Run the Gunicorn server on both port 5000 (for the app) and 8080 (for Replit)
    """
    print("Starting Gunicorn on ports 5000 and 8080...")
    
    # Start primary server on port 5000
    primary_cmd = ["gunicorn", "--bind", "0.0.0.0:5000", "--reuse-port", "--reload", "main:app"]
    primary_proc = subprocess.Popen(primary_cmd)
    
    # Wait a bit for the primary server to start
    time.sleep(2)
    
    # Start proxy server on port 8080 that forwards to port 5000
    proxy_cmd = ["python", "simple_proxy.py"]
    proxy_proc = subprocess.Popen(proxy_cmd)
    
    print(f"Primary server PID: {primary_proc.pid}")
    print(f"Proxy server PID: {proxy_proc.pid}")
    
    # Handle termination signals
    def signal_handler(sig, frame):
        print("Terminating servers...")
        proxy_proc.terminate()
        primary_proc.terminate()
        sys.exit(0)
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Keep the script running
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        signal_handler(signal.SIGINT, None)

if __name__ == "__main__":
    main()