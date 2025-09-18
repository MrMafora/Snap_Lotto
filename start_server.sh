#!/bin/bash

# Smart port binding for both development and production deployment
# Uses PORT environment variable if available (production), defaults to 5000 (development)

PORT=${PORT:-5000}
echo "Starting server on port: $PORT"

# Enhanced production configuration for better reliability
exec gunicorn \
    --bind 0.0.0.0:$PORT \
    --workers 1 \
    --threads 2 \
    --timeout 120 \
    --keep-alive 5 \
    --max-requests 1000 \
    --max-requests-jitter 100 \
    --preload \
    --access-logfile - \
    --error-logfile - \
    --log-level info \
    main:app