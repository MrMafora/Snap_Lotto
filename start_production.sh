#!/bin/bash
# Production startup script for Replit deployment

# Print banner
echo "====================================================="
echo "  LOTTERY APPLICATION PRODUCTION DEPLOYMENT"
echo "====================================================="
echo "Starting application on port 8080..."

# Set environment
export ENVIRONMENT=production
export DEBUG=false

# Clear port 8080 if needed
echo "Checking port 8080..."
if lsof -i :8080 > /dev/null 2>&1; then
    echo "Port 8080 is in use. Clearing..."
    if command -v fuser > /dev/null; then
        fuser -k 8080/tcp
    else
        for pid in $(lsof -t -i:8080); do
            echo "Killing process $pid"
            kill -9 $pid
        done
    fi
    sleep 1
else
    echo "Port 8080 is available."
fi

# Check PostgreSQL connection
echo "Checking database connection..."
if [ -n "$DATABASE_URL" ]; then
    echo "Database URL is set."
else
    echo "WARNING: DATABASE_URL is not set. Using SQLite fallback."
fi

# Start the production server
echo "Starting production server..."
exec python production_server.py