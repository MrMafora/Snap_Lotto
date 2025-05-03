#!/usr/bin/env python3
"""
Direct application starter for development
Ensures the application binds to the expected port (8080) for Replit
"""
import os
import sys
import subprocess
import signal
import time

# Configuration
PORT = 8080
APP_MODULE = "main:app"

def run_gunicorn():
    """Run the gunicorn server directly on port 8080"""
    print(f"Starting gunicorn on port {PORT}...")
    cmd = [
        "gunicorn",
        "--bind", f"0.0.0.0:{PORT}",
        "--reuse-port",
        "--reload",
        APP_MODULE
    ]
    
    try:
        # Start gunicorn process
        process = subprocess.Popen(cmd)
        print(f"Gunicorn started with PID {process.pid}")
        
        # Return the process object
        return process
    except Exception as e:
        print(f"Error starting gunicorn: {e}")
        sys.exit(1)

def handle_signal(signum, frame):
    """Handle termination signals"""
    print(f"Received signal {signum}. Shutting down...")
    sys.exit(0)

if __name__ == "__main__":
    # Register signal handlers
    signal.signal(signal.SIGINT, handle_signal)
    signal.signal(signal.SIGTERM, handle_signal)
    
    # Start the server
    gunicorn_process = run_gunicorn()
    
    try:
        # Keep the script running
        while True:
            # Check if gunicorn is still running
            if gunicorn_process.poll() is not None:
                print("Gunicorn process terminated unexpectedly")
                sys.exit(1)
            
            # Sleep to avoid high CPU usage
            time.sleep(1)
    except KeyboardInterrupt:
        print("Stopping server...")
    finally:
        # Make sure to terminate the gunicorn process
        if gunicorn_process.poll() is None:
            gunicorn_process.terminate()
            gunicorn_process.wait()
        
        print("Server stopped")