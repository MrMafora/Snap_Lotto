#!/bin/bash
# Script to ensure application binds to port 8080
export PORT=8080
export GUNICORN_CMD_ARGS="--bind=0.0.0.0:8080 --workers=2 --reload --access-logfile=-"

# Start the application - MUST bind to port 8080 for Replit to access it
exec gunicorn main:app