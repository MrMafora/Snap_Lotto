"""
Gunicorn configuration for both development and deployment
"""
import os
import logging
import sys

# Setup basic logging
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('gunicorn.conf')

# Default to development mode unless specified
environment = os.environ.get('ENVIRONMENT', 'development')

# Set bind address based on environment
if environment.lower() == 'production':
    bind = "0.0.0.0:8080"  # For Replit deployment
else:
    bind = "0.0.0.0:5000"  # For development

# Print binding information
logger.info(f"Gunicorn configured to bind to {bind}")
print(f"IMPORTANT: Gunicorn binding to {bind}", file=sys.stderr)

# Worker configuration
workers = 2
threads = 2
worker_class = "gthread"
timeout = 60

# Logging
accesslog = "-"
errorlog = "-"
loglevel = "info"

# Debug actual binding
def on_starting(server):
    logger.info(f"Gunicorn starting - binding to {bind}")

def post_fork(server, worker):
    logger.info(f"Worker forked - running on port {bind.split(':')[1]}")
    print(f"Worker forked - running on port {bind.split(':')[1]}", file=sys.stderr)