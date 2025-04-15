#!/bin/bash
# Script to start both the main application on port 5000 and the port 8080 bridge

# Log file
LOG_FILE="replit_startup.log"

echo "[$(date '+%Y-%m-%d %H:%M:%S')] Starting Replit server..." | tee -a $LOG_FILE

# Function to handle SIGINT/SIGTERM
cleanup() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] Shutting down..." | tee -a $LOG_FILE
    kill $PORT_8080_PID 2>/dev/null
    kill $GUNICORN_PID 2>/dev/null
    exit 0
}

# Set trap for cleanup
trap cleanup SIGINT SIGTERM

# Start main application on port 5000 (usual workflow)
echo "[$(date '+%Y-%m-%d %H:%M:%S')] Starting main application on port 5000..." | tee -a $LOG_FILE
gunicorn --bind 0.0.0.0:5000 --reuse-port --reload main:app &
GUNICORN_PID=$!

# Wait for main application to fully start
echo "[$(date '+%Y-%m-%d %H:%M:%S')] Waiting for main application to initialize..." | tee -a $LOG_FILE
sleep 3

# Check if main application is running
if ! ps -p $GUNICORN_PID > /dev/null; then
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] ERROR: Main application failed to start!" | tee -a $LOG_FILE
    exit 1
fi

# Start port 8080 bridge in background
echo "[$(date '+%Y-%m-%d %H:%M:%S')] Starting port 8080 bridge..." | tee -a $LOG_FILE
python simple_port_8080.py &
PORT_8080_PID=$!

# Wait for port 8080 bridge to fully start
echo "[$(date '+%Y-%m-%d %H:%M:%S')] Waiting for port 8080 bridge to initialize..." | tee -a $LOG_FILE
sleep 2

# Check if port 8080 bridge is running
if ! ps -p $PORT_8080_PID > /dev/null; then
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] ERROR: Port 8080 bridge failed to start!" | tee -a $LOG_FILE
    # Try to kill gunicorn
    kill $GUNICORN_PID 2>/dev/null
    exit 1
fi

echo "[$(date '+%Y-%m-%d %H:%M:%S')] Server is ready and listening on ports 5000 and 8080" | tee -a $LOG_FILE

# Keep the script running to maintain both processes
wait $GUNICORN_PID