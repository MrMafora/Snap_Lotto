#!/bin/bash
# Script to start both the main application on port 5000 and the proxy on port 8080

# Launch the port forwarding proxy in the background
echo "Starting port forwarding proxy on port 8080..."
python port_forward.py &
PROXY_PID=$!

# Wait a moment for the proxy to initialize
sleep 2

# Check if proxy started successfully
if ps -p $PROXY_PID > /dev/null; then
  echo "Port forwarding proxy started successfully (PID: $PROXY_PID)"
else
  echo "Error: Port forwarding proxy failed to start"
  exit 1
fi

# Start the main application
echo "Starting main application on port 5000..."
gunicorn --bind 0.0.0.0:5000 --reuse-port --reload main:app

# This section only executes if gunicorn exits
echo "Main application stopped"

# Clean up the proxy
kill $PROXY_PID
echo "Port forwarding proxy stopped"