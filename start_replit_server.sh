#!/bin/bash
# Script to start both the main application and the port 8080 proxy

# Define log file
LOG_FILE="replit_server.log"

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
kill_processes() {
    local PORT=$1
    local PIDS=$(lsof -t -i:$PORT 2>/dev/null)
    
    if [ ! -z "$PIDS" ]; then
        log "Killing processes on port $PORT (PIDs: $PIDS)"
        kill -9 $PIDS 2>/dev/null
    fi
}

kill_processes 5000
kill_processes 8080

# Start the main application in the background
log "Starting main application on port 5000..."
gunicorn --bind 0.0.0.0:5000 --reuse-port --reload main:app &
MAIN_PID=$!

# Give the main app time to start
log "Waiting for main app to start..."
sleep 3

# Check if main app is running
if ! ps -p $MAIN_PID > /dev/null; then
    log "ERROR: Main application failed to start. Exiting."
    exit 1
fi

# Start the port 8080 proxy server in the background
log "Starting port 8080 proxy server..."
nohup python bridge.py > bridge.log 2>&1 &
BRIDGE_PID=$!

# Check if bridge started correctly
sleep 2
if ! ps -p $BRIDGE_PID > /dev/null; then
    log "WARNING: Bridge may not have started correctly. Check bridge.log for details."
    # Try alternative method
    log "Trying alternative proxy method..."
    nohup python simple_port_8080.py > simple_proxy.log 2>&1 &
fi

# Keep the script running to maintain both processes
log "Both services started. Press Ctrl+C to stop."
tail -f bridge.log