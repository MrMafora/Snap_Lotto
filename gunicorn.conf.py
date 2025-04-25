
"""
Gunicorn configuration file
"""
import os
import logging
import sys

# Setup basic logging
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('gunicorn.conf')

# Override bind setting - always use port 8080 for Replit compatibility
bind = "0.0.0.0:8080"

# Make absolutely certain we bind to port 8080
os.environ['PORT'] = '8080'
os.environ['GUNICORN_PORT'] = '8080'
os.environ['REPLIT_PORT'] = '8080'

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
    logger.info(f"Gunicorn starting - binding to {bind}")
    print(f"Gunicorn starting - binding to {bind}", file=sys.stderr)

def post_fork(server, worker):
    logger.info(f"Worker forked - running on port 8080")
    print(f"Worker forked - running on port 8080", file=sys.stderr)
