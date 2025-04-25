
"""
Gunicorn configuration file for deployment
"""
import os
import sys
import logging

# Setup basic logging
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('gunicorn.conf')

# Always bind to port 8080 for Replit compatibility
bind = "0.0.0.0:8080"

# Worker configuration
workers = 2
threads = 2
worker_class = "gthread"
timeout = 60

# Logging
accesslog = "-"
errorlog = "-"
loglevel = "info"

def on_starting(server):
    """Log server startup"""
    logger.info(f"Gunicorn starting - binding to {bind}")
    print(f"Gunicorn starting - binding to {bind}", file=sys.stderr)

def post_fork(server, worker):
    """Log worker startup"""
    logger.info("Worker forked - running on port 8080")
    print("Worker forked - running on port 8080", file=sys.stderr)
