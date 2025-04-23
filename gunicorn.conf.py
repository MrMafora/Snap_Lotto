"""
Gunicorn configuration for both development and deployment
This ensures consistent binding across environments
"""

# Import os to access environment variables
import os
import logging
import sys

# Setup basic logging
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('gunicorn.conf')

# Default to production for deployments
environment = os.environ.get('ENVIRONMENT', 'production')

# CRITICAL: Use port 8080 for Replit compatibility
# This is updated to match Replit's expected port
bind = "0.0.0.0:8080"

# Print binding information to help debug port issues
logger.info(f"Gunicorn configured to bind to {bind}")
print(f"IMPORTANT: Gunicorn binding to {bind}", file=sys.stderr)

# Overwrite any potentially conflicting environment variables
os.environ['PORT'] = '8080'
os.environ['GUNICORN_PORT'] = '8080'

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
    print(f"Gunicorn starting - binding to {bind}", file=sys.stderr)

def post_fork(server, worker):
    logger.info(f"Worker forked - running on {bind}")
    print(f"Worker forked - running on {bind}", file=sys.stderr)