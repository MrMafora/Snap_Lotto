#!/bin/bash

# Kill any existing processes on port 5000
echo "Clearing port 5000..."
pkill -f "gunicorn" || true
fuser -k 5000/tcp || true
sleep 1

# Start gunicorn with our config
echo "Starting gunicorn..."
exec gunicorn --bind 0.0.0.0:5000 --reuse-port --reload main:app