"""
Simple and direct Gunicorn configuration file with ONLY the essential settings
"""
import os
import sys
import logging

# Setup logging
logging.basicConfig(level=logging.INFO,
                  format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('direct_gunicorn.conf')

# Force binding to port 8080 with no environment variable overrides
bind = "0.0.0.0:8080"

# Worker configuration
workers = 2
worker_class = "gthread"
threads = 2
timeout = 60

# Logging
loglevel = "info"

def on_starting(server):
    """Log server startup"""
    logger.info(f"Starting Gunicorn server with bind: {bind}")
    print(f"BINDING TO: {bind}", file=sys.stderr)