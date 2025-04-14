#!/bin/bash
# Direct port 8080 binding script
# This script launches the application directly on port 8080 for Replit compatibility

echo "Starting lottery application on port 8080..."

# Kill any existing processes
echo "Cleaning up existing processes..."
pkill -f "gunicorn" || true
pkill -f "python.*maintain_port_8080" || true
pkill -f "python.*run_port_8080" || true
pkill -f "python.*direct_port_8080" || true

# Force a short delay to ensure all ports are released
sleep 1

# Direct port 8080 binding method:
# This is the solution that will work most reliably with Replit
echo "Starting gunicorn directly on port 8080..."
exec gunicorn --bind 0.0.0.0:8080 --reuse-port --reload main:app