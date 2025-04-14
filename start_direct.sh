#!/bin/bash

# Kill any existing processes on port 5000
echo "Clearing port 5000..."
pkill -f "python start_direct.py" || true
pkill -f "gunicorn" || true
fuser -k 5000/tcp 2>/dev/null || true
sleep 1

# Start our direct Flask server
echo "Starting direct Flask server..."
exec python start_direct.py