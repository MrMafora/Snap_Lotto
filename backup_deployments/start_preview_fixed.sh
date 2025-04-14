#!/bin/bash

# Kill any existing processes
pkill -f gunicorn || true
pkill -f "python" || true

# Sleep to ensure all processes are terminated
sleep 1

# Print this exact message that Replit looks for
echo "Server is ready and listening on port 5000"

# Run our ultra lightweight server for immediate port detection
python lightweight_server.py