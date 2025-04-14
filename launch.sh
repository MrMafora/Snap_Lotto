#!/bin/bash
# Launch script to start both port 5000 main application
# and port 8080 bridge application

# Run the port 8080 bridge in the background
echo "Starting port 8080 bridge application..."
python run_port_8080_bridge.py > port_8080.log 2>&1 &
PORT_8080_PID=$!

# Give the bridge a moment to start
sleep 1

# Start the main application (as per workflow configuration)
echo "Starting main application on port 5000..."
exec gunicorn --bind 0.0.0.0:5000 --reuse-port --reload main:app