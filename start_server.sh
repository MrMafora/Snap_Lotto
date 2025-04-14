#!/bin/bash

# Wait a moment to ensure the port_detector has released the port
sleep 2

# Kill any existing Flask processes
pkill -f "python simple_app.py" || true

# Start the Gunicorn server with minimal configuration for better port detection
echo "Starting Gunicorn server with minimal configuration..."

# Use --preload to load the application before forking workers
# This helps with faster startup and port detection
gunicorn \
  --bind 0.0.0.0:5000 \
  --reuse-port \
  --workers 1 \
  --worker-class sync \
  --log-level info \
  --access-logfile - \
  --error-logfile - \
  main:app