#!/bin/bash

# Kill any existing server processes first
pkill -f gunicorn || true
pkill -f python || true

sleep 1

# Start our ultra minimal port opener
python instant_port.py