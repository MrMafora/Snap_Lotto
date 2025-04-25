"""
Gunicorn configuration for both development and production
"""
import os
import logging
import sys

# Setup basic logging
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('gunicorn.conf')

# Determine environment and port
environment = os.environ.get('ENVIRONMENT', 'development')
port = os.environ.get('PORT', '8080')  # Default to 8080 for Replit compatibility

# Bind to the appropriate port
bind = f"0.0.0.0:5000"

# Print binding information to help debug port issues
logger.info(f"Gunicorn configured to bind to {bind}")
print(f"IMPORTANT: Gunicorn binding to port {port}", file=sys.stderr)

# Overwrite any potentially conflicting environment variables
os.environ['PORT'] = port
os.environ['GUNICORN_PORT'] = port

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
    logger.info(f"Worker forked - running on port {port}")
    print(f"Worker forked - running on port {port}", file=sys.stderr)