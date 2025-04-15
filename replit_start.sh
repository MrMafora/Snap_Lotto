#!/bin/bash
# Script to start both the Flask application and the Replit-specific port proxy server

# Define log file
LOG_FILE="replit_startup.log"

# Function to log messages
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a $LOG_FILE
}

# Check if Python is available
if ! command -v python &> /dev/null; then
    log "Error: Python is required but not found."
    exit 1
fi

# Kill any existing processes running on ports 5000 or 8080
log "Checking for existing processes on ports 5000 and 8080..."
PORT_5000_PID=$(lsof -ti:5000 2>/dev/null)
PORT_8080_PID=$(lsof -ti:8080 2>/dev/null)

if [ ! -z "$PORT_5000_PID" ]; then
    log "Killing process on port 5000 (PID: $PORT_5000_PID)"
    kill -9 $PORT_5000_PID 2>/dev/null
fi

if [ ! -z "$PORT_8080_PID" ]; then
    log "Killing process on port 8080 (PID: $PORT_8080_PID)"
    kill -9 $PORT_8080_PID 2>/dev/null
fi

# Start the port 8080 proxy server in the background
log "Starting port 8080 proxy server..."
python replit_proxy.py > replit_proxy.log 2>&1 &
PROXY_PID=$!

# Give the proxy a moment to start
sleep 2

# Check if proxy started successfully
if ps -p $PROXY_PID > /dev/null; then
    log "Proxy server started successfully with PID: $PROXY_PID"
else
    log "ERROR: Failed to start proxy server. Check replit_proxy.log for details."
    exit 1
fi

# Start the main Flask application
log "Starting main Flask application on port 5000..."
exec gunicorn --bind 0.0.0.0:5000 --reuse-port --reload main:app