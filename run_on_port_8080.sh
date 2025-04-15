#!/bin/bash
# This script runs the application on port 8080 as required by Replit
# Using gunicorn to ensure compatibility with production environment

echo "[$(date '+%Y-%m-%d %H:%M:%S')] Starting application on port 8080..."
exec gunicorn --bind 0.0.0.0:8080 --workers 1 --reuse-port --reload main:app