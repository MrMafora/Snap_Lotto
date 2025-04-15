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

# Determine binding based on environment
environment = os.environ.get('ENVIRONMENT', 'development')

# Primary binding
if environment.lower() == 'production':
    # Production environment uses port 8080 for Replit deployment
    bind = "0.0.0.0:8080"
else:
    # Development environment uses port 5000
    bind = "0.0.0.0:5000"

# Worker configuration
workers = 4
worker_class = "sync"
threads = 2
timeout = 120
keepalive = 5

# Logging
accesslog = "-"
errorlog = "-"
loglevel = "info"