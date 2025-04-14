#!/bin/bash

# Kill any existing processes
pkill -f gunicorn || true
pkill -f python || true
pkill -f flask || true

# Wait for ports to be released
sleep 1

# Start our optimized preview solution
python replit_preview.py