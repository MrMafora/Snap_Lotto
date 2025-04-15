#!/bin/bash
# Run the application on port 8080 for Replit deployment compatibility
echo "Starting server on port 8080..."
gunicorn --bind 0.0.0.0:8080 --workers=4 --reuse-port --reload main:app