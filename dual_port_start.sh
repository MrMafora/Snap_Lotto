#!/bin/bash
# Dual-Port Startup Script for Replit Compatibility
# This script starts both the main application on port 5000 and ensures port 8080 is available

echo "Starting dual-port lottery application setup..."

# Kill any existing gunicorn processes
echo "Cleaning up existing processes..."
pkill -f "gunicorn" || true
pkill -f "python.*maintain_port_8080" || true
pkill -f "python.*run_port_8080" || true

# Force a short delay to ensure all ports are released
sleep 1

# Start the port 8080 maintenance script in the background
echo "Starting port 8080 supervisor..."
nohup python maintain_port_8080.py > port_8080_supervisor.log 2>&1 &

# Start the main application using gunicorn on port 5000
echo "Starting main application on port 5000..."
exec gunicorn --bind 0.0.0.0:5000 --reuse-port --reload main:app