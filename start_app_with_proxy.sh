#!/bin/bash
# Start the application with the port proxy
# This script runs both the main application and the port proxy

# Kill any existing processes on port 8080
fuser -k 8080/tcp 2>/dev/null || true
sleep 1

# Start the main app in the background
echo "Starting main application on port 5000..."
gunicorn --bind 0.0.0.0:5000 main:app &
APP_PID=$!

# Wait for app to start
echo "Waiting for main application to start..."
sleep 3

# Start the port proxy in the foreground
echo "Starting port proxy from 8080 to 5000..."
exec python standalone_port_proxy.py