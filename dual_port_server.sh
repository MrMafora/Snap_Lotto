#!/bin/bash
# This script starts the application in dual-port mode
# - One instance on port 5000 for local development
# - One instance on port 8080 for Replit deployment

echo "Starting dual port server for Replit deployment..."

# Function to clean up processes on exit
cleanup() {
  echo "Cleaning up processes..."
  pkill -f "gunicorn --bind 0.0.0.0:5000"
  pkill -f "gunicorn --bind 0.0.0.0:8080"
  exit 0
}

# Register the cleanup function for signals
trap cleanup SIGINT SIGTERM

# Start main Flask app on port 5000 (in background)
echo "Starting server on port 5000..."
gunicorn --bind 0.0.0.0:5000 --workers=2 --reuse-port --reload main:app > /tmp/gunicorn-5000.log 2>&1 &

# Store the PID of the port 5000 server
PORT_5000_PID=$!
echo "Server on port 5000 started with PID: $PORT_5000_PID"

# Start another instance on port 8080 for deployment
echo "Starting server on port 8080..."
gunicorn --bind 0.0.0.0:8080 --workers=2 --reuse-port --reload main:app > /tmp/gunicorn-8080.log 2>&1 &

# Store the PID of the port 8080 server
PORT_8080_PID=$!
echo "Server on port 8080 started with PID: $PORT_8080_PID"

echo "Both servers running on ports 5000 and 8080"
echo "Press Ctrl+C to stop both servers"

# Keep the script running to maintain the background processes
while true; do
  sleep 1
  # Check if either process has died
  if ! ps -p $PORT_5000_PID > /dev/null; then
    echo "Server on port 5000 died, restarting..."
    gunicorn --bind 0.0.0.0:5000 --workers=2 --reuse-port --reload main:app > /tmp/gunicorn-5000.log 2>&1 &
    PORT_5000_PID=$!
  fi
  if ! ps -p $PORT_8080_PID > /dev/null; then
    echo "Server on port 8080 died, restarting..."
    gunicorn --bind 0.0.0.0:8080 --workers=2 --reuse-port --reload main:app > /tmp/gunicorn-8080.log 2>&1 &
    PORT_8080_PID=$!
  fi
done