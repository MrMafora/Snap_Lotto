#!/bin/bash
# Script to ensure application binds to port 8080
export PORT=8080
export GUNICORN_PORT=8080
export FLASK_RUN_PORT=8080
export SERVER_PORT=8080

# Stop any existing proxy service
pkill -f "port_proxy_service.py" || true

# Make the direct start script executable
chmod +x direct_start_on_8080.py

# Start the application - MUST bind to port 8080 for Replit to access it
echo "Starting application directly on port 8080"
exec python3 direct_start_on_8080.py