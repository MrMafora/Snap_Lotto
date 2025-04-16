"""
Gunicorn configuration for both development and deployment
This ensures consistent binding across environments
"""

# Import os to access environment variables
import os
import logging

# Setup basic logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('gunicorn.conf')

# Default to production for deployments
environment = os.environ.get('ENVIRONMENT', 'production')

# Bind to port 8080 in production, 5000 in development
if environment.lower() == 'production':
    bind = "0.0.0.0:8080"
else:
    bind = "0.0.0.0:5000"

# Worker configuration
workers = 2
threads = 2
worker_class = "gthread"
timeout = 60

# Logging
accesslog = "-"
errorlog = "-"
loglevel = "info"