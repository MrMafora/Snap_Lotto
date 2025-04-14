#!/bin/bash
# Script used by Replit deployment to start the application
# This script ensures we use the special dual-port configuration where
# port 5000 is mapped to external port 80 as required for Replit Autoscale deployments

# Aggressive cleanup of existing processes
echo "Stopping all existing processes that might be using ports 5000 or 8080..."

# Kill all Python and Gunicorn processes
pkill -9 -f "python start_direct.py" || true
pkill -9 -f "gunicorn" || true
killall -9 python 2>/dev/null || true

# Try multiple methods to ensure port 5000 and 8080 are free
for PORT in 5000 8080; do
  # Find processes using these ports
  if command -v lsof >/dev/null 2>&1; then
    PIDS=$(lsof -t -i:$PORT 2>/dev/null)
    if [ ! -z "$PIDS" ]; then
      echo "Killing processes using port $PORT: $PIDS"
      kill -9 $PIDS 2>/dev/null || true
    fi
  fi
  
  # Try to use fuser if available
  if command -v fuser >/dev/null 2>&1; then
    fuser -k ${PORT}/tcp 2>/dev/null || true
  fi
done

# Sleep to allow processes to fully terminate
sleep 3
echo "All existing processes should be terminated"

# Launch our dual-port configuration
echo "Starting dual-port configuration with port 5000 -> 80 routing..."
exec python start_direct.py