#!/bin/bash
# This script is called by Replit's workflow system
# instead of calling gunicorn directly

# Force kill any processes on these ports first
echo "Forcefully terminating any processes on port 5000..."
./force_kill_port_5000.sh
./clear_ports.sh

# Run the required gunicorn process on port 5000 to satisfy Replit's requirements
echo "Starting gunicorn on port 5000 as Replit expects..."
gunicorn --bind 0.0.0.0:5000 --reuse-port --reload main:app