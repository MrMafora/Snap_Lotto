#!/bin/bash
# Direct port 8080 application starter

# Kill any existing processes on port 8080
echo "Checking for processes on port 8080..."
kill $(lsof -t -i:8080) 2>/dev/null || true

# Wait for port to be available
echo "Waiting for port 8080 to be available..."
sleep 2

# Start the Gunicorn server directly on port 8080
echo "Starting application on port 8080..."
exec gunicorn --bind 0.0.0.0:8080 --reuse-port --reload main:app