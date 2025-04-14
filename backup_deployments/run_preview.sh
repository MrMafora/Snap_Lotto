#!/bin/bash

# Kill any existing Flask or Python processes
pkill -f python || true
pkill -f flask || true
pkill -f gunicorn || true

# Wait for any ports to be released
sleep 1

# Run the Replit preview solution
echo "Starting Replit preview solution..."
exec python3 replit_preview.py