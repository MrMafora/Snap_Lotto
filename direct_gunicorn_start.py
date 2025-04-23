#!/usr/bin/env python3
import os
import subprocess
import sys
import time

# Set environment variables to ensure consistent port usage
os.environ['PORT'] = '8080'
os.environ['GUNICORN_PORT'] = '8080'

print("Starting Gunicorn on port 8080...")

# Start Gunicorn directly with the correct port
try:
    # Use a direct command with explicit port binding
    cmd = ["gunicorn", "--bind", "0.0.0.0:8080", "--reuse-port", "--reload", "main:app"]
    
    print(f"Executing: {' '.join(cmd)}")
    
    # Start the process
    process = subprocess.Popen(cmd, stdout=sys.stdout, stderr=sys.stderr)
    
    # Wait for the process to initialize
    time.sleep(2)
    
    # Check if process is still running
    if process.poll() is None:
        print("Gunicorn started successfully on port 8080")
    else:
        print("Failed to start Gunicorn")
        sys.exit(1)
    
    # Keep the script running
    process.wait()
    
except Exception as e:
    print(f"Error starting Gunicorn: {e}")
    sys.exit(1)