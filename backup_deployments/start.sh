#!/bin/bash
# First, run our aggressive port clearing script to ensure all ports are free
echo "Making sure all ports are clear..."
./clear_ports.sh

# Start the application on port 8080
echo "Starting server on port 8080..."
# Set up gunicorn with optimal settings for Replit:
# - bind to port 8080 (which is forwarded to external port 80)
# - single worker to reduce memory usage
# - increased timeout for long-running requests
# - access log disabled to reduce console noise
# - error log redirected to stderr for workflow visibility
# - preload the application to reduce startup time
exec gunicorn \
  --bind 0.0.0.0:8080 \
  --workers 1 \
  --timeout 120 \
  --access-logfile - \
  --error-logfile - \
  --log-level info \
  --preload \
  main:app