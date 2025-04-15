#!/bin/bash
# Deployment script for Replit
# This script starts the application on both port 5000 and port 8080

echo "Starting application on ports 5000 and 8080"
exec python dual_bind_server.py