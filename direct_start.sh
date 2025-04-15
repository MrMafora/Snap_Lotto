#!/bin/bash
# Direct port binding solution starter script

# Function to log messages
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1"
}

# Check if Python is available
if ! command -v python &> /dev/null; then
    log "Error: Python is required but not found."
    exit 1
fi

# Make script executable
chmod +x direct_binding.py

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

# Start the direct binding script
log "Starting direct port binding solution..."
exec ./direct_binding.py