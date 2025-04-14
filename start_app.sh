#!/bin/bash

# Kill any existing gunicorn processes
pgrep gunicorn | xargs kill -9 2>/dev/null || true

# Print message for port detection
echo "Starting Flask application on port 5000..."

# Start the Flask application
python simple_app.py