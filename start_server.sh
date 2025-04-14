#!/bin/bash

# Start the Gunicorn server with our configuration
echo "Starting Gunicorn server with improved worker configuration..."

# Check if we're in production mode
if [ "$ENVIRONMENT" = "production" ]; then
    # Production mode - no reload
    echo "Running in production mode without reload"
    gunicorn -c gunicorn.conf.py main:app
else
    # Development mode - with reload
    echo "Running in development mode with reload"
    gunicorn -c gunicorn.conf.py --reload main:app
fi