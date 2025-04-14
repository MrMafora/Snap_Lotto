#!/bin/bash

# Kill any existing processes
pkill -f gunicorn || true
pkill -f python || true
pkill -f flask || true

# Wait for ports to be released
sleep 1

# Start the simplified server
python simple_replit_server.py