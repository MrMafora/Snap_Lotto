#!/bin/bash
# Dual-port starter script for Replit
# This script:
# 1. Opens port 5000 immediately (will be exposed externally as port 80)
# 2. Runs the actual application on port 8080 internally
# 3. Proxies requests between them

# Kill any existing processes
echo "Clearing ports 5000 and 8080..."
pkill -f "python start_direct.py" || true
pkill -f "gunicorn" || true
fuser -k 5000/tcp 2>/dev/null || true
fuser -k 8080/tcp 2>/dev/null || true
sleep 1

# Start our dual-port server with proper routing
echo "Starting dual-port server system with port 5000 -> 80 external mapping..."
exec python start_direct.py