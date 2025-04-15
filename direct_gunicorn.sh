#!/bin/bash
# Direct Gunicorn start script using the configuration file

echo "Starting Gunicorn with configuration file (binding to port 8080)..."
gunicorn -c gunicorn.conf.py main:app