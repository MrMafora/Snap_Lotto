#!/bin/bash
# Port 8080 Workflow Script
# This script is designed to be used by the Replit workflow to bind to port 8080

# Start the application directly on port 8080
# This is the simplest and most direct approach to satisfy Replit's requirements
exec gunicorn --bind 0.0.0.0:8080 --reuse-port --reload main:app