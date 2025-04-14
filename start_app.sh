#!/bin/bash

# Kill any existing processes
pkill -f gunicorn || true
pkill -f python || true
pkill -f flask || true

# Wait for ports to be released
sleep 1

# Use the direct Python approach as recommended by Replit support
echo "Starting app with direct Flask approach..."
python3 start_flask.py