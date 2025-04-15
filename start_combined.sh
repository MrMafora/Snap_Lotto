#!/bin/bash
# Combined startup script for both ports 5000 and 8080

# Kill any existing processes on ports 5000 and 8080
echo "Checking for existing processes on ports 5000 and 8080..."
PORT_5000_PID=$(lsof -ti:5000)
PORT_8080_PID=$(lsof -ti:8080)

if [ ! -z "$PORT_5000_PID" ]; then
    echo "Killing process on port 5000 (PID: $PORT_5000_PID)..."
    kill -9 $PORT_5000_PID
fi

if [ ! -z "$PORT_8080_PID" ]; then
    echo "Killing process on port 8080 (PID: $PORT_8080_PID)..."
    kill -9 $PORT_8080_PID
fi

# Wait a moment to ensure ports are released
sleep 1

# Start the main application using gunicorn on port 5000
echo "Starting main application on port 5000..."
MAIN_APP_LOG="server_5000.log"
ENVIRONMENT=development gunicorn --bind 0.0.0.0:5000 --reuse-port --reload main:app > $MAIN_APP_LOG 2>&1 &
MAIN_PID=$!
echo "Main application started with PID: $MAIN_PID"

# Allow time for the main application to start
sleep 3

# Start the port 8080 bridge
echo "Starting port 8080 bridge..."
BRIDGE_LOG="bridge.log"
python bridge.py > $BRIDGE_LOG 2>&1 &
BRIDGE_PID=$!
echo "Bridge started with PID: $BRIDGE_PID"

# Save PIDs for later management
echo $MAIN_PID > main.pid
echo $BRIDGE_PID > bridge.pid

# Provide status
echo "============================================"
echo "Application started:"
echo "  - Main app (port 5000): PID $MAIN_PID (log: $MAIN_APP_LOG)"
echo "  - Bridge (port 8080): PID $BRIDGE_PID (log: $BRIDGE_LOG)"
echo "============================================"
echo "Use the following commands for management:"
echo "  - To stop all: kill -9 \$(cat main.pid bridge.pid)"
echo "  - To stop bridge only: kill -9 \$(cat bridge.pid)"
echo "  - To check logs: tail -f $MAIN_APP_LOG $BRIDGE_LOG"
echo "============================================"

# Keep the script running to make it easier to stop with Ctrl+C
echo "Press Ctrl+C to stop all servers"
trap "kill -9 $MAIN_PID $BRIDGE_PID; echo 'All servers stopped'; exit 0" INT
wait