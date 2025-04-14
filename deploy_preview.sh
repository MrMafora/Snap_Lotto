#!/bin/bash

# Kill any existing processes
pkill -f gunicorn || true
pkill -f "python" || true

# Wait for ports to be released
sleep 1

# Run our preview script
python preview_redirect.py