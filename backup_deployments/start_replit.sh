#!/bin/bash

# Kill any existing processes on port 5000
echo "Clearing port 5000..."
pkill -f "python start_replit.py" || true
pkill -f "gunicorn" || true
fuser -k 5000/tcp 2>/dev/null || true
fuser -k 8080/tcp 2>/dev/null || true
sleep 1

# Start our Replit-optimized script
echo "Starting Replit-optimized server..."
exec python start_replit.py