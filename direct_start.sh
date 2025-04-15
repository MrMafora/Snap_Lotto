#!/bin/bash
# Direct port binding solution for Replit
# This script starts the Flask application directly on port 8080

echo "[$(date '+%Y-%m-%d %H:%M:%S')] Starting application on port 8080 directly..."
exec gunicorn --bind 0.0.0.0:8080 --workers 1 --timeout 600 --reload main:app