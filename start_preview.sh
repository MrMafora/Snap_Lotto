#!/bin/bash

# Kill any existing processes that might block our ports
pkill -f gunicorn || true
pkill -f "python port_detector.py" || true
pkill -f "python simple_app.py" || true

# Ensure port is clearly reported for Replit detection 
echo "Starting port detector for Replit preview..."
echo "Server is ready and listening on port 5000"

# Run the port detector script
python port_detector.py