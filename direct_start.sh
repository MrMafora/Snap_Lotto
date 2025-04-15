#!/bin/bash
# Direct startup script for Replit deployment
# This script uses gunicorn.conf.py with port 8080 binding

echo "Starting application directly using gunicorn.conf.py (port 8080)..."
exec gunicorn -c gunicorn.conf.py main:app