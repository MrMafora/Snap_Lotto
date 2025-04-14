#!/bin/bash

# Kill any existing server processes
pkill -f gunicorn || true
pkill -f python || true

# Wait a moment to ensure ports are free
sleep 1

# Run our pre-start script to ensure port detection
python pre_start.py