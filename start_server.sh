#!/bin/bash

# Start the Gunicorn server with our configuration
echo "Starting Gunicorn server with improved worker configuration..."
gunicorn -c gunicorn.conf.py --reload main:app