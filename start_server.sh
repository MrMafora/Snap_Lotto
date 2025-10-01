#!/bin/bash

# Autoscale Deployment optimized configuration
# PORT is provided by Replit Autoscale deployment environment

PORT=${PORT:-5000}
echo "Starting server on port: $PORT (Autoscale mode)"

# Autoscale-optimized gunicorn configuration
# Single worker for request handling, multiple threads for concurrency
exec gunicorn \
    --bind 0.0.0.0:$PORT \
    --workers 1 \
    --threads 4 \
    --timeout 120 \
    --keep-alive 5 \
    --max-requests 1000 \
    --max-requests-jitter 100 \
    --preload \
    --access-logfile - \
    --error-logfile - \
    --log-level info \
    main:app