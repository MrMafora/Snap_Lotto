#!/bin/bash
# Direct port 8080 binding for Replit deployment
# This script starts the application directly on port 8080

# Print banner
echo "====================================================="
echo "  STARTING LOTTERY APPLICATION ON PORT 8080"
echo "====================================================="

# Set environment variables for production
export ENVIRONMENT="production"
export DEBUG="false"

# Check if port 8080 is available
if curl -s http://localhost:8080 > /dev/null 2>&1; then
    echo "Port 8080 is already in use. Attempting to free it..."
    # Try to find and kill processes using port 8080
    if command -v fuser > /dev/null; then
        fuser -k 8080/tcp
    elif command -v lsof > /dev/null; then
        for pid in $(lsof -t -i:8080); do
            echo "Killing process $pid"
            kill -9 $pid
        done
    else
        echo "WARNING: Could not check for processes using port 8080"
    fi
    sleep 2
fi

# Start the application on port 8080
echo "Starting application on port 8080..."
exec gunicorn --bind 0.0.0.0:8080 --workers 4 --timeout 120 --access-logfile - main:app