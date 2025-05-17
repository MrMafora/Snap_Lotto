#!/usr/bin/env python
"""
Script to explicitly start the Gunicorn server on port 8080 for Replit compatibility.
"""
import os
import sys
import subprocess

def main():
    """Start the Gunicorn server with explicit port 8080 binding"""
    print("Starting Gunicorn server on port 8080...")
    
    # Use explicit command-line flag to override any config file settings
    cmd = [
        "gunicorn",
        "--bind=0.0.0.0:8080",  # Explicit bind address
        "--workers=2",          # Number of worker processes
        "--threads=2",          # Number of threads per worker
        "--worker-class=gthread", # Worker class
        "--timeout=60",         # Worker timeout
        "--reload",             # Auto-reload on code changes
        "main:app"              # WSGI application
    ]
    
    # Print the command for debugging
    print(f"Running command: {' '.join(cmd)}")
    
    # Execute Gunicorn and capture output
    result = subprocess.run(cmd, capture_output=True, text=True)
    print(f"Command exit code: {result.returncode}")
    print(f"Command stdout: {result.stdout}")
    print(f"Command stderr: {result.stderr}")

if __name__ == "__main__":
    main()