#!/bin/bash

# Kill any existing servers to free up ports
pkill -f gunicorn || true
pkill -f "python quick_server.py" || true
pkill -f "python -m http.server" || true

# Wait for ports to be released
sleep 1

# Report port for Replit detection
echo "Server is ready and listening on port 5000"

# Launch our quick server
python quick_server.py