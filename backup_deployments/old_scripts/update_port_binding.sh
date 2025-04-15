#!/bin/bash
# Script to update port binding from 5000 to 8080

echo "Updating port binding from 5000 to 8080..."

# Kill any running processes
pkill -f "gunicorn" || true

# Change to port 8080
echo "Starting server on port 8080..."
gunicorn --bind 0.0.0.0:8080 --reuse-port --reload main:app