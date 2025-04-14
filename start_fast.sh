#!/bin/bash

# Kill any existing processes
pkill -f gunicorn || true
pkill -f "python instant_server.py" || true

# Wait a moment for ports to be freed
sleep 1

# Start our instant server which will handle port detection quickly
python instant_server.py