#!/bin/bash
# Script to stop any existing gunicorn processes and start a new one on port 8080
# This script ensures a clean server startup on the correct port

# Print debug information
echo "=== SERVER RESTART SCRIPT ==="
echo "Current directory: $(pwd)"
echo "Python version: $(python --version)"
echo "Available Python packages: $(pip freeze | grep -E 'flask|gunicorn')"

# Hard-stop any existing gunicorn processes
echo -e "\n=== STOPPING EXISTING PROCESSES ==="
echo "Stopping any existing gunicorn processes..."
ps aux | grep gunicorn
pkill -f gunicorn || echo "No existing gunicorn processes found."

# Wait for processes to terminate
echo "Waiting for processes to terminate..."
sleep 2
ps aux | grep gunicorn | grep -v grep || echo "All gunicorn processes stopped."

echo -e "\n=== SETTING ENVIRONMENT VARIABLES ==="
# Set PORT environment variables with export for future processes
export PORT=8080
export GUNICORN_PORT=8080
export FLASK_APP=main.py
export FLASK_ENV=development

# Show environment
echo "Environment variables set:"
echo "PORT=$PORT"
echo "GUNICORN_PORT=$GUNICORN_PORT"
echo "FLASK_APP=$FLASK_APP"
echo "FLASK_ENV=$FLASK_ENV"

echo -e "\n=== STARTING SERVER ON PORT 8080 ==="
echo "Starting gunicorn on port 8080..."

# Run gunicorn with explicit port binding and additional debugging
exec gunicorn --bind 0.0.0.0:8080 --log-level debug --workers=2 --worker-class=gthread --threads=2 --timeout=60 --reload main:app