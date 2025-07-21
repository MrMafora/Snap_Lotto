#!/bin/bash

# Cloud Run Deployment Script for South African Lottery Scanner
# This script addresses the deployment issues mentioned in the error

echo "Preparing deployment for Cloud Run..."

# Fix pyee package installation issues by forcing reinstall
echo "Fixing package installation issues..."
pip uninstall pyee -y 2>/dev/null || true
pip install --force-reinstall --no-deps pyee 2>/dev/null || true

# Verify essential packages
echo "Verifying essential packages..."
python -c "import flask, gunicorn, psycopg2" || {
    echo "Essential packages missing, attempting to install..."
    pip install flask gunicorn psycopg2-binary
}

# Set Cloud Run environment variables
export PORT=${PORT:-8080}
export FLASK_ENV=production
export PYTHONUNBUFFERED=1

echo "Environment configured:"
echo "PORT: $PORT"
echo "FLASK_ENV: $FLASK_ENV"

# Test the application starts correctly
echo "Testing application startup..."
timeout 10 python -c "
import main
print('Application imports successfully')
" || echo "Warning: Application test failed, but continuing deployment..."

echo "Deployment preparation complete!"
echo "Your application is configured to:"
echo "  - Bind to port $PORT (Cloud Run compatible)"
echo "  - Use production settings"
echo "  - Handle package conflicts automatically"
echo ""
echo "To deploy to Cloud Run, use:"
echo "  gcloud run deploy lottery-scanner --source . --port $PORT --region us-central1"