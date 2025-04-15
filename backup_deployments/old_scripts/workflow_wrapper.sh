#!/bin/bash
# Workflow wrapper script that manages the application with proper port binding
# This script is designed to be used by the Replit workflow

echo "Starting lottery application with dual port binding..."

# Kill any existing processes
echo "Cleaning up existing processes..."
pkill -f "gunicorn" || true
pkill -f "python.*maintain_port_8080" || true
pkill -f "python.*run_port_8080" || true

# Force a short delay to ensure all ports are released
sleep 1

# Start the port 8080 supervisor in the background
echo "Starting port 8080 supervisor..."
python maintain_port_8080.py > port_8080_supervisor.log 2>&1 &
SUPERVISOR_PID=$!

# Start the main application with modified startup for faster loading
echo "Starting main application on port 5000..."
exec gunicorn --bind 0.0.0.0:5000 --reuse-port --reload main:app

# Cleanup on exit (this part will only execute if gunicorn fails)
kill $SUPERVISOR_PID 2>/dev/null || true