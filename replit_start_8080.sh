#!/bin/bash
# Start the application directly on port 8080 using Flask's built-in server
# This script is designed for Replit deployment to make the app externally accessible

echo "[$(date '+%Y-%m-%d %H:%M:%S')] Starting Flask application directly on port 8080..."

# Run the application directly with Python (not Gunicorn)
# This leverages the code in main.py that binds to port 8080 when run directly
exec python main.py