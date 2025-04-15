#!/bin/bash
# Final direct port binding solution for Replit
# This script starts the application and forces it to bind to port 8080 directly

echo "[$(date '+%Y-%m-%d %H:%M:%S')] Starting direct port binding solution..."

# Set environment variable to tell the application to use port 8080
export DIRECT_PORT=8080

# Start the server using gunicorn with direct binding to port 8080
exec gunicorn --bind 0.0.0.0:8080 --workers 1 --timeout 600 --reload main:app