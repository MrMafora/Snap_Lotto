#!/bin/bash
# Script to explicitly start the application on port 8080

# First, run our script to forcibly kill any processes on port 5000
echo "Killing any processes on port 5000..."
./force_kill_port_5000.sh

# Clear all ports to make sure 8080 is free
echo "Clearing any existing processes on other ports..."
./clear_ports.sh

# Start the gunicorn application on port 8080 with explicit bind parameter
echo "Starting application on port 8080..."
exec gunicorn --bind 0.0.0.0:8080 --workers 1 --timeout 120 --worker-class sync main:app