#!/bin/bash
# Script for deployment in Replit

# Force kill any processes on port 5000 first
echo "Forcefully terminating any processes on port 5000..."
./force_kill_port_5000.sh

# Clear all ports to make sure 8080 is free
echo "Clearing any existing processes on other ports..."
./clear_ports.sh

# Start the application on port 8080 using Flask directly
echo "Starting application on port 8080 for deployment..."
exec python main_8080.py